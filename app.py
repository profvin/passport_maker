import streamlit as st
from PIL import Image, ImageEnhance, ImageOps
import io
import base64
from rembg import remove, new_session
import hashlib
from datetime import datetime

# --- 1. SET PAGE CONFIG ---
st.set_page_config(
    page_title="Express Passport Maker", 
    layout="wide"
)

# --- FORCE LIGHT MODE & VISIBILITY VIA CSS ---
st.markdown(
    """
    <style>
    /* Force canvas and main app backgrounds to light */
    .stApp, html, body, [data-testid="stAppViewContainer"] {
        background-color: #FFFFFF !important;
        color: #31333F !important;
    }
    [data-testid="stHeader"] {
        background-color: #FFFFFF !important;
    }
    
    /* Make sure text elements stay sharp and highly readable */
    h1, h2, h3, p, span, label, .stMarkdown {
        color: #31333F !important;
    }
    
    /* Ensure input fields have proper visibility */
    input, textarea, [data-testid="stTextInput"] {
        color: #31333F !important;
        background-color: #FFFFFF !important;
    }
    
    /* Avoid dark background wrapping in the uploader previews */
    [data-testid="stImage"] {
        background-color: #FFFFFF !important;
        border: 1px solid #f0f0f0;
        border-radius: 4px;
        padding: 5px;
    }
    
    /* Hides the top header bar (including Deploy button) */
    header {visibility: hidden;}
    
    /* Hides the main menu button (top right) */
    #MainMenu {visibility: hidden;}
    
    /* Hides the "Made with Streamlit" footer */
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True
)

# --- A4 Canvas Dimensions (300 DPI) ---
A4_WIDTH = 2480
A4_HEIGHT = 3508

st.title("Express Passport Maker 📸")

# --- 🔑 THE MATHEMATICAL PASSWORD GENERATOR ---
MASTER_SECRET = st.secrets.get("MASTER_SECRET")
secret_fallback_active = False

if not MASTER_SECRET:
    MASTER_SECRET = "local_test_key"
    secret_fallback_active = True

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

def get_days_left_in_cycle():
    from calendar import monthrange
    today = datetime.now()
    day = today.day
    year = today.year
    month = today.month

    if 1 <= day <= 7:
        days_left = 7 - day
    elif 8 <= day <= 14:
        days_left = 14 - day
    elif 15 <= day <= 21:
        days_left = 21 - day
    else:
        _, last_day = monthrange(year, month)
        days_left = last_day - day
        
    return days_left

# --- 🔓 ADMIN EXEMPTION CHECK ---
is_admin_bypass = "admin" in st.query_params and st.query_params["admin"] == "true"

# --- 🔐 HIDDEN ADMIN PORTAL (Main Screen Triggered) ---
if is_admin_bypass:
    with st.container():
        st.success("⚡ Admin Mode Active: Client Keys Generated Automatically!")
        col1, col2, col3, col4 = st.columns(4)
        col1.code(f"Week 1 Key:\n{PASSWORDS['week_1']}")
        col2.code(f"Week 2 Key:\n{PASSWORDS['week_2']}")
        col3.code(f"Week 3 Key:\n{PASSWORDS['week_3']}")
        col4.code(f"Week 4 Key:\n{PASSWORDS['week_4']}")
        st.markdown("---")

# Show secret diagnostic warning only to admin
if is_admin_bypass and secret_fallback_active:
    st.warning("⚠️ Secrets Loading: 'MASTER_SECRET' is using local_test_key")

# --- 🔑 LOGIN GATE ---
user_password = ""
if is_admin_bypass:
    st.success("⚡ Admin Mode Active: Password Bypass Enabled")
    access_granted = True
else:
    with st.container():
        st.write("### 🔑 Client Portal Access")
        user_password = st.text_input(
            "Enter your Active Weekly Access Key to unlock the editor:", 
            type="password", 
            placeholder="Contact your system administrator to get your weekly key"
        )
    access_granted = user_password in allowed_keys

# --- APPLICATION EXECUTION ---
if access_granted:
    if not is_admin_bypass:
        st.success("✅ Access Granted! Editor unlocked.")
        days_remaining = get_days_left_in_cycle()
        
        if days_remaining == 0:
            st.warning("⚠️ **Reminder:** Your weekly Access Key expires **tonight at midnight**!")
        elif days_remaining <= 2:
            st.warning(f"⚠️ **Reminder:** Only **{days_remaining} days** left before your key expires.")
        else:
            st.info(f"📆 **Subscription Active:** **{days_remaining} days** left in this cycle.")
            
    st.markdown("---")
    
    # --- Step 1: File Uploader ---
    uploaded_files = st.file_uploader(
        "Upload portrait photo(s)", 
        type=["jpg", "jpeg", "png"], 
        accept_multiple_files=True
    )

    if uploaded_files:
        # Load and verify all uploaded images
        input_images = []
        for file in uploaded_files:
            try:
                img = Image.open(file)
                img = ImageOps.exif_transpose(img)
                img = img.convert("RGBA")
                
                # ⚡ SPEED OPTIMIZATION
                MAX_PROCESSING_DIM = 1000
                if max(img.size) > MAX_PROCESSING_DIM:
                    img.thumbnail((MAX_PROCESSING_DIM, MAX_PROCESSING_DIM), Image.Resampling.LANCZOS)
                input_images.append(img)
            except Exception as e:
                st.error(f"Error loading file {file.name}: {e}")
        
        # --- 🎨 MAIN SCREEN CONTROL PANEL ---
        st.markdown("### 🎨 Image Editing & Layout Controls")
        
        ctrl_col1, ctrl_col2, ctrl_col3 = st.columns(3)
        
        with ctrl_col1:
            bg_preset = st.selectbox(
                "Choose Background Color Preset",
                ["White", "Light Blue", "Light Grey", "Sky Blue", "Royal Blue", "Red", "Custom HEX"]
            )
            
            preset_mapping = {
                "White": "#FFFFFF",
                "Light Blue": "#ADD8E6",
                "Light Grey": "#D3D3D3",
                "Sky Blue": "#87CEEB",
                "Royal Blue": "#4169E1",
                "Red": "#FF0000"
            }
            
            initial_hex = preset_mapping.get(bg_preset, "#FFFFFF")
            
            hex_input = st.text_input(
                "Custom HEX Color Code (e.g. #FFFFFF)", 
                value=initial_hex, 
                help="Type any standard hex code. Don't worry, you can also use the color pallete grid below!"
            )
            
            if not hex_input.startswith("#"):
                hex_input = f"#{hex_input}"
            if len(hex_input) != 7:
                hex_input = "#FFFFFF"
                
            st.markdown("<p style='font-size:0.85rem; font-weight:bold; margin-bottom:5px;'>Or select from this Interactive Studio Palette:</p>", unsafe_allow_html=True)
            
            palette_colors = [
                ("#FFFFFF", "White"), ("#ADD8E6", "Lt Blue"), ("#D3D3D3", "Lt Grey"), 
                ("#87CEEB", "Sky Blue"), ("#4169E1", "Royal Blue"), ("#000080", "Navy"),
                ("#FF0000", "Red"), ("#FFD700", "Gold"), ("#008000", "Green"),
                ("#F4F4F4", "Chalk"), ("#E6E6FA", "Lavender"), ("#FFF0F5", "Lavender Blush"),
                ("#FFE4E1", "Misty Rose"), ("#F5F5DC", "Beige"), ("#F0F8FF", "Alice Blue"),
                ("#333333", "Charcoal"), ("#000000", "Black"), ("#4B0082", "Indigo")
            ]
            
            cols = st.columns(6)
            chosen_palette_color = None
            
            for idx, (hex_code, label) in enumerate(palette_colors):
                col_target = cols[idx % 6]
                with col_target:
                    if st.button("", key=f"color_btn_{idx}", help=f"Click to select {label} ({hex_code})"):
                        chosen_palette_color = hex_code
                        
                    st.markdown(
                        f"""
                        <div style="
                            background-color: {hex_code}; 
                            width: 100%; 
                            height: 15px; 
                            border: 1px solid #ccc; 
                            border-radius: 4px; 
                            margin-top: -15px;
                            margin-bottom: 10px;
                        "></div>
                        """, 
                        unsafe_allow_html=True
                    )
            
            if chosen_palette_color:
                bg_color_hex = chosen_palette_color
                st.success(f"Selected color: {bg_color_hex}")
            else:
                bg_color_hex = hex_input

            size_option = st.selectbox(
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
                sub_col_w, sub_col_h = st.columns(2)
                custom_w = sub_col_w.number_input("Width (px)", min_value=100, max_value=1000, value=600, step=10)
                custom_h = sub_col_h.number_input("Height (px)", min_value=100, max_value=1000, value=600, step=10)
                
                if custom_w is not None and custom_h is not None:
                    if int(custom_w) > 0 and int(custom_h) > 0:
                        photo_width = int(custom_w)
                        photo_height = int(custom_h)

            photo_width = max(100, photo_width)
            photo_height = max(100, photo_height)

        with ctrl_col2:
            num_copies = st.slider("Total Number of Copies (A4 Sheet)", min_value=1, max_value=24, value=8, step=1)
            brightness = st.slider("Brightness", 0.5, 2.0, 1.0, 0.1)
            contrast = st.slider("Contrast", 0.5, 2.0, 1.0, 0.1)
            
        with ctrl_col3:
            st.markdown("**👤 Subject Nudging Controls**")
            subject_scale = st.slider(
                "Subject Scale % (Zoom)", 
                min_value=70, 
                max_value=130, 
                value=100, 
                step=2,
                help="Zoom in or out to make the head fill the frame better or leave breathing room."
            )
            
            vertical_nudge = st.slider(
                "Subject Vertical Offset (Move Up/Down)", 
                min_value=-150, 
                max_value=150, 
                value=0, 
                step=5,
                help="Nudge the subject down to prevent hair cuts, or up to hide background empty space at the bottom."
            )
            
            saturation = st.slider("Saturation (Color)", 0.5, 2.0, 1.0, 0.1)

        st.markdown("---")

        # --- Processing Engine ---
        processed_images = []
        with st.spinner("⚡ Running high-detail hair segmentation..."):
            hair_safe_session = new_session(model_name="u2net_human_seg")
            
            for idx, img in enumerate(input_images):
                no_bg_image = remove(
                    img,
                    session=hair_safe_session,
                    alpha_matting=True,
                    alpha_matting_foreground_threshold=240,
                    alpha_matting_background_threshold=10,
                    alpha_matting_erode_size=2
                ).convert("RGBA")
                
                orig_w, orig_h = no_bg_image.size
                aspect_ratio = orig_h / orig_w
                
                base_w = photo_width
                base_h = int(photo_width * aspect_ratio)
                
                scale_multiplier = subject_scale / 100.0
                target_sub_w = int(base_w * scale_multiplier)
                target_sub_h = int(base_h * scale_multiplier)

                subject_copy = no_bg_image.resize((target_sub_w, target_sub_h), Image.Resampling.LANCZOS)
                
                solid_bg = Image.new("RGBA", (photo_width, photo_height), bg_color_hex)
                
                offset_x = (photo_width - target_sub_w) // 2
                offset_y = (photo_height - target_sub_h) + vertical_nudge
                
                solid_bg.paste(subject_copy, (offset_x, offset_y), subject_copy)
                combined_image = solid_bg.convert("RGB")
                
                # Apply filters
                enhancer = ImageEnhance.Brightness(combined_image)
                combined_image = enhancer.enhance(brightness)
                
                enhancer = ImageEnhance.Contrast(combined_image)
                combined_image = enhancer.enhance(contrast)
                
                enhancer = ImageEnhance.Color(combined_image)
                combined_image = enhancer.enhance(saturation)
                
                processed_images.append(combined_image)

        # --- Display Layout ---
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.write("### 👤 Passport Previews")
            for idx, p_img in enumerate(processed_images):
                st.image(p_img, caption=f"Photo {idx+1} ({photo_width}x{photo_height}px)", width='stretch')
            
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
            
            num_pics = len(processed_images)
            copies_pasted = 0
            
            for row in range(int(rows_count)):
                for col in range(int(cols_count)):
                    if copies_pasted >= num_copies:
                        break
                    
                    current_image = processed_images[copies_pasted % num_pics]
                    
                    x = margin_x + col * step_w
                    y = margin_y + row * step_h
                    a4_canvas.paste(current_image, (x, y))
                    copies_pasted += 1
                if copies_pasted >= num_copies:
                    break
                    
            st.image(a4_canvas, caption="Multi-Photo A4 Layout", width='stretch')

            # Save A4 to binary stream
            buffered = io.BytesIO()
            a4_canvas.save(buffered, format="JPEG", quality=95)
            img_bytes = buffered.getvalue()

            # --- Action Buttons Layout ---
            st.write("### 📥 Print Actions")
            action_col1, action_col2 = st.columns(2)
            
            with action_col1:
                st.download_button(
                    label="💾 Download A4 JPEG File",
                    data=img_bytes,
                    file_name="passport_print_sheet.jpg",
                    mime="image/jpeg",
                    width='stretch',
                )
                
            with action_col2:
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
                # Updated deprecated component to modern iframe 
                st.iframe(f"data:text/html;base64,{base64.b64encode(print_html.encode()).decode()}", height=60)

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
        # Updated deprecated component to modern iframe
        st.iframe(f"data:text/html;base64,{base64.b64encode(payment_html.encode()).decode()}", height=260)
