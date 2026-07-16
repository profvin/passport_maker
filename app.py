import streamlit as st
from PIL import Image, ImageEnhance, ImageOps
import io
import base64
from rembg import remove
import hashlib
from datetime import datetime

# --- 1. SET PAGE CONFIG (MUST BE THE VERY FIRST STREAMLIT CALL) ---
st.set_page_config(page_title="Express Passport Maker", layout="wide")

# --- A4 Canvas Dimensions (300 DPI) ---
A4_WIDTH = 2480
A4_HEIGHT = 3508

st.title("Express Passport Maker 📸")

# --- 🔑 THE MATHEMATICAL PASSWORD GENERATOR ---
# Change this master key to your own secret word. Keep it secret!
# Anyone who knows this key can mathematically generate your passwords.
MASTER_SECRET = "profnabari"

def generate_key_for_week(week_num):
    """
    Generates a unique, deterministic 8-character password 
    based on the Master Secret, current Year, current Month, and Week Number.
    """
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    # Example raw string: "my_ultra_secret_master_key_123-2026-7-w1"
    raw_string = f"{MASTER_SECRET}-{current_year}-{current_month}-w{week_num}"
    
    # Hash the string and return the first 8 characters
    return hashlib.sha256(raw_string.encode()).hexdigest()[:8]

# Automatically generate this month's 4 active weekly keys
PASSWORDS = {
    "week_1": generate_key_for_week(1),
    "week_2": generate_key_for_week(2),
    "week_3": generate_key_for_week(3),
    "week_4": generate_key_for_week(4),
}

# Automatically determine which week we are in based on today's date
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
    next_key = PASSWORDS["week_1"]  # Wraps around to next month's week 1

# Accept BOTH this week's key and next week's key to make transitions smooth
allowed_keys = [current_key, next_key]

# --- 🔑 LOGIN GATE CONTAINER ---
with st.container():
    st.write("### 🔑 Client Portal Access")
    user_password = st.text_input(
        "Enter your Active Weekly Access Key to unlock the editor:", 
        type="password", 
        placeholder="Contact your system administrator to get your weekly key"
    )

# --- Check Password and Run App ---
if user_password in allowed_keys:
    st.success("✅ Access Granted! Editor unlocked.")
    st.markdown("---")
    
    # --- Step 1: File Uploader ---
    uploaded_file = st.file_uploader("Upload a portrait photo", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        # Load original image
        input_image = Image.open(uploaded_file)
        
        # Create sidebar for editing controls
        st.sidebar.header("🎨 Image Editing & Settings")
        
        # 1. Background Color Picker
        bg_color_hex = st.sidebar.color_picker("Choose Background Color", "#FFFFFF")
        
        # 2. Image Size Selection
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
        
        # Fallback default values
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

        # 3. Layout Settings
        st.sidebar.markdown("---")
        st.sidebar.subheader("🔢 Layout Settings")
        num_copies = st.sidebar.slider("Number of Copies", min_value=1, max_value=24, value=8, step=1)

        # 4. Image Enhancements
        st.sidebar.markdown("### Image Adjustments")
        brightness = st.sidebar.slider("Brightness", 0.5, 2.0, 1.0, 0.1)
        contrast = st.sidebar.slider("Contrast", 0.5, 2.0, 1.0, 0.1)
        saturation = st.sidebar.slider("Saturation (Color)", 0.5, 2.0, 1.0, 0.1)

        # --- Processing Engine ---
        with st.spinner("Processing image..."):
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
            st.image(combined_image, caption=f"Aspect ratio locked to {photo_width}x{photo_height}px", use_container_width=True)
            
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
                    
            st.image(a4_canvas, caption="Preview of full A4 page", use_container_width=True)

        # --- Print Processing ---
        buffered = io.BytesIO()
        a4_canvas.save(buffered, format="JPEG", quality=95)
        img_str = base64.b64encode(buffered.getvalue()).decode()
        img_data_uri = f"data:image/jpeg;base64,{img_str}"

        print_html = f"""
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
            padding: 16px 32px;
            font-size: 18px;
            font-weight: bold;
            border-radius: 8px;
            cursor: pointer;
            width: 100%;
            box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
            margin-top: 20px;
            margin-bottom: 50px;
        ">
            🖨️ Click to Print A4 Sheet
        </button>
        """
        
        try:
            st.iframe(print_html, height=120)
        except AttributeError:
            import streamlit.components.v1 as components
            components.html(print_html, height=120)

else:
    # Shown only when the access key is missing or incorrect
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
        st.markdown("""
        ### 💳 How to Get Your Key
        1. Send your weekly subscription fee to the administrator.
        2. Send a payment confirmation receipt over chat/WhatsApp.
        3. Receive your active Access Key instantly!
        """)

# --- 🔐 HIDDEN ADMIN PORTAL ---
# Appears in the sidebar so you can retrieve current passwords.
st.sidebar.markdown("---")
with st.sidebar.expander("🛠️ Admin Portal (View Keys)"):
    admin_input = st.text_input("Enter Master Secret Key to reveal passwords:", type="password")
    if admin_input == MASTER_SECRET:
        st.success("Admin verified!")
        st.write("**This Month's Generated Keys:**")
        for week, pwd in PASSWORDS.items():
            st.code(f"{week}: {pwd}")
    elif admin_input != "":
        st.error("Incorrect Master Secret Key.")
