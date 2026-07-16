import streamlit as st
import streamlit.components.v1 as components
from PIL import Image, ImageEnhance, ImageOps
import io
import base64
from rembg import remove
import hashlib
from datetime import datetime

# --- 1. SET PAGE CONFIG ---
st.set_page_config(page_title="Express Passport Maker", layout="wide")

# --- A4 Canvas Dimensions (300 DPI) ---
A4_WIDTH = 2480
A4_HEIGHT = 3508

st.title("Express Passport Maker 📸")

# --- 🔑 THE MATHEMATICAL PASSWORD GENERATOR ---
MASTER_SECRET = "profnabari"

def generate_key_for_week(week_num):
    current_year = datetime.now().year
    current_month = datetime.now().month
    raw_string = f"{MASTER_SECRET}-{current_year}-{current_month}-w{week_num}"
    return hashlib.sha256(raw_string.encode()).hexdigest()[:8]

PASSWORDS = {
    "week_1": generate_key_for_week(1),
    "week_2": generate_key_for_week(2),
    "week_3": generate_key_for_week(3),
    "week_4": generate_key_for_week(4),
}

today_day = datetime.now().day
if 1 <= today_day <= 7:
    current_key = PASSWORDS["week_1"]
    next_key = PASSWORDS["week_2"]
elif 8 <= today_day <= 14:
    current_key = PASSWORDS["week_2"]
    next_key = PASSWORDS["week_3"]
elif 15 <= today_day <= 21:
    current_key = PASSWORDS["week_3"]
    next_key = PASSWORDS["week_4"]
else:
    current_key = PASSWORDS["week_4"]
    next_key = PASSWORDS["week_1"]

allowed_keys = [current_key, next_key]

# --- 🔑 LOGIN GATE ---
with st.container():
    st.write("### 🔑 Client Portal Access")
    user_password = st.text_input(
        "Enter your Active Weekly Access Key to unlock the editor:", 
        type="password", 
        placeholder="Contact your system administrator to get your weekly key"
    )

if user_password in allowed_keys:
    st.success("✅ Access Granted! Editor unlocked.")
    st.markdown("---")
    
    # --- Step 1: File Uploader ---
    uploaded_file = st.file_uploader("Upload a portrait photo", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        # Load original image
        input_image = Image.open(uploaded_file)
        
        # ⚡ SPEED OPTIMIZATION: Resize giant images before background removal
        # This speeds up processing on Streamlit Cloud by up to 5x!
        MAX_PROCESSING_DIM = 1000
        if max(input_image.size) > MAX_PROCESSING_DIM:
            input_image.thumbnail((MAX_PROCESSING_DIM, MAX_PROCESSING_DIM), Image.Resampling.LANCZOS)
        
        # Create sidebar for editing controls
        st.sidebar.header("🎨 Image Editing & Settings")
        bg_color_hex = st.sidebar.color_picker("Choose Background Color", "#FFFFFF")
        
        size_option = st.sidebar.selectbox(
            "Select Passport Size",
            [
                "2 x 2 inches (US / India)", 
                "35 x 45 mm (UK / Europe / Kenya)",
                "35 x 43 mm",
                "prof size",
                "Custom"
            ]
        )
        
        photo_width = 600
        photo_height = 600
        
        if size_option == "2 x 2 inches (US / India)":
            photo_width, photo_height = 600, 600
        elif size_option == "35 x 45 mm (UK / Europe / Kenya)":
            photo_width, photo_height = 413, 531
        elif size_option == "35 x 43 mm":
            photo_width, photo_height = 413, 508
        elif size_option == "prof size":
            photo_width, photo_height = 413, 531
        elif size_option == "Custom":
            col_w, col_h = st.sidebar.columns(2)
            custom_w = col_w.number_input("Width (px)", min_value=100, max_value=1000, value=600, step=10)
            custom_h = col_h.number_input("Height (px)", min_value=100, max_value=1000, value=600, step=10)
            
            if custom_w is not None and custom_h is not None:
                if int(custom_w) > 0 and int(custom_h) > 0:
                    photo_width = int(custom_w)
                    photo_height = int(custom_h)

        photo_width = max(100, photo_width)
        photo_height = max(100, photo_height)

        st.sidebar.markdown("---")
        st.sidebar.subheader("🔢 Layout Settings")
        num_copies = st.sidebar.slider("Number of Copies", min_value=1, max_value=24, value=8, step=1)

        st.sidebar.markdown("### Image Adjustments")
        brightness = st.sidebar.slider("Brightness", 0.5, 2.0, 1.0, 0.1)
        contrast = st.sidebar.slider("Contrast", 0.5, 2.0, 1.0, 0.1)
        saturation = st.sidebar.slider("Saturation (Color)", 0.5, 2.0, 1.0, 0.1)

        # --- Processing Engine ---
        with st.spinner("⚡ Removing background & adjusting colors..."):
            no_bg_image = remove(input_image).convert("RGBA")
            fitted_subject = ImageOps.fit(no_bg_image, (photo_width, photo_height), Image.Resampling.LANCZOS)
            solid_bg = Image.new("RGBA", (photo_width, photo_height), bg_color_hex)
            combined_image = Image.alpha_composite(solid_bg, fitted_subject).convert("RGB")
            
            enhancer = ImageEnhance.Brightness(combined_image)
            combined_image = enhancer.enhance(brightness)
            
            enhancer = ImageEnhance.Contrast(combined_image)
            combined_image = enhancer.enhance(contrast)
            
            enhancer = ImageEnhance.Color(combined_image)
            combined_image = enhancer.enhance(saturation)

        # --- Display Layout ---
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.write("### 👤 Single Passport Preview")
            st.image(combined_image, caption=f"Locked to {photo_width}x{photo_height}px", use_container_width=True)
            
        with col2:
            st.write(f"### 🖨️ Generated A4 Print Sheet ({num_copies} Copies)")
            
            a4_canvas = Image.new("RGB", (A4_WIDTH, A4_HEIGHT), "white")
            margin_x = 80   
            margin_y = 120  
            gap = 40        
            
            step_w = photo_width + gap
            step_h = photo_height + gap
            
            if step_w > 0 and step_h > 0:
                cols_count = (A4_WIDTH - (2 * margin_x)) // step_w
                rows_count = (A4_HEIGHT - (2 * margin_y)) // step_h
            else:
                cols_count, rows_count = 1, 1
            
            copies_pasted = 0
            for row in range(int(rows_count)):
                for col in range(int(cols_count)):
                    if copies_pasted >= num_copies:
                        break
                    x = margin_x + col * step_w
                    y = margin_y + row * step_h
                    a4_canvas.paste(combined_image, (x, y))
                    copies_pasted += 1
                if copies_pasted >= num_copies:
                    break
                    
            st.image(a4_canvas, caption="A4 Print Sheet Layout", use_container_width=True)

            # Save A4 to binary stream
            buffered = io.BytesIO()
            a4_canvas.save(buffered, format="JPEG", quality=95)
            img_bytes = buffered.getvalue()

            # --- Action Buttons Layout ---
            st.write("### 📥 Print Actions")
            action_col1, action_col2 = st.columns(2)
            
            with action_col1:
                # 1. High-Quality Direct Download Button (Fail-Safe)
                st.download_button(
                    label="💾 Download A4 JPEG File",
                    data=img_bytes,
                    file_name="passport_print_sheet.jpg",
                    mime="image/jpeg",
                    use_container_width=True,
                )
                
            with action_col2:
                # 2. Re-engineered Browser Print Frame with fixed heights
                img_str = base64.b64encode(img_bytes).decode()
                img_data_uri = f"data:image/jpeg;base64,{img_str}"
                
                print_html = f"""
                <html>
                <body style="margin:0; padding:0;">
                    <script>
                    function printImage() {{
                        var pwa = window.open('', '_blank');
                        pwa.document.open();
                        pwa.document.write(`
                            <html>
                            <head>
                                <title>Print Passport Sheet</title>
                                <style>
                                    @page {{ size: A4; margin: 0; }}
                                    body {{ margin: 0; display: flex; justify-content: center; align-items: center; height: 100vh; background-color: white; }}
                                    img {{ max-width: 100%; max-height: 100%; width: auto; height: auto; object-fit: contain; }}
                                </style>
                            </head>
                            <body onload="window.print(); window.onafterprint = function() {{ window.close(); }}">
                                <img src="{img_data_uri}" />
                            </body>
                            </html>
                        `);
                        pwa.document.close();
                    }}
                    </script>
                    <button onclick="printImage()" style="
                        background-color: #FF4B4B;
                        color: white;
                        border: none;
                        padding: 10px 20px;
                        font-size: 16px;
                        font-weight: bold;
                        border-radius: 4px;
                        cursor: pointer;
                        width: 100%;
                        height: 45px;
                        box-shadow: 0px 2px 4px rgba(0,0,0,0.1);
                    ">
                        🖨️ Direct Browser Print
                    </button>
                </body>
                </html>
                """
                # Use st.components.v1.html with explicit height to guarantee it stays visible
                components.html(print_html, height=60)

else:
    if user_password != "":
        st.error("❌ Invalid Access Key. Please check the key or contact the administrator to renew your weekly access.")
    
    st.info("💡 **Welcome to Express Passport Maker!**\n\nTo get instant access and start generating print-ready passport sheets in seconds, make your payment and request an access key.")
    
    col_info1, col_info2 = st.columns(2)
    with col_info1:
        st.markdown("""
        ### 🚀 Why Subscribe?
        * **Super Fast:** No Photoshop skills required.
        * **Auto Background Removal:** Change backgrounds in 1 click.
        * **Perfect Margins:** Fits exactly on A4.
        * **Save Time & Money:** Turn a 10-minute job into a 30-second print.
        """)
    with col_info2:
        # Custom payment instructions HTML directly in Streamlit
        st.markdown("### 💳 How to Get Your Key")
        
        whatsapp_link = "https://wa.me/254718269914?text=Hello%20Admin,%20I%20have%20sent%20my%20weekly%20subscription%20via%20M-Pesa.%20Here%20is%20my%20payment%20confirmation."
        
        payment_html = f"""
        <div style="background-color: #f9f9f9; padding: 15px; border-radius: 8px; border: 1px solid #e0e0e0; font-family: sans-serif;">
            <p style="margin-top: 0; font-size: 0.95rem; color: #444;">1. Send your weekly subscription fee to the administrator via:</p>
            <div style="background-color: #e8f5e9; padding: 10px; border-radius: 6px; border: 1px solid #c8eedb; text-align: center; margin-bottom: 12px;">
                <span style="font-size: 0.8rem; color: #2e7d32; font-weight: bold; text-transform: uppercase;">M-Pesa Buy Goods Till</span>
                <div style="font-size: 1.4rem; font-weight: 800; color: #1b5e20;">3136870</div>
            </div>
            <p style="font-size: 0.95rem; color: #444; margin-bottom: 15px;">2. Click below to submit your payment confirmation screenshot via WhatsApp to <strong>0718269914</strong>:</p>
            <div style="text-align: center;">
                <a href="{whatsapp_link}" target="_blank" style="
                    display: inline-block;
                    background-color: #25D366;
                    color: white;
                    padding: 8px 16px;
                    text-decoration: none;
                    border-radius: 20px;
                    font-weight: bold;
                    font-size: 0.9rem;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                ">
                    💬 Send Receipt on WhatsApp
                </a>
            </div>
            <p style="margin-top: 15px; margin-bottom: 0; font-weight: bold; color: #2e7d32; font-size: 0.95rem; text-align: center;">
                Receive your active Access Key instantly!
            </p>
        </div>
        """
        st.components.v1.html(payment_html, height=260)

# --- 🔐 HIDDEN ADMIN PORTAL (URL Triggered) ---
# Check if "?admin=true" is in the URL path
if "admin" in st.query_params and st.query_params["admin"] == "true":
    st.sidebar.markdown("---")
    with st.sidebar.expander("🛠️ Admin Portal (View Keys)", expanded=True):
        admin_input = st.text_input("Enter Master Secret Key to reveal passwords:", type="password")
        if admin_input == MASTER_SECRET:
            st.success("Admin verified!")
            st.write("**This Month's Generated Keys:**")
            for week, pwd in PASSWORDS.items():
                st.code(f"{week}: {pwd}")
        elif admin_input != "":
            st.error("Incorrect Master Secret Key.")
