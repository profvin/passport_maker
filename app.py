import streamlit as st
from PIL import Image, ImageEnhance, ImageOps
import io
import base64
from rembg import remove

# Set page configuration
st.set_config = st.set_page_config(page_title="Express Passport Maker", layout="wide")

# --- A4 Canvas Dimensions (300 DPI) ---
A4_WIDTH = 2480
A4_HEIGHT = 3508

st.title("Express Passport Maker 📸")

# --- Step 1: File Uploader ---
uploaded_file = st.file_uploader("Upload a portrait photo", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Load original image
    input_image = Image.open(uploaded_file)
    
    # Create sidebar for all your editing controls
    st.sidebar.header("🎨 Image Editing & Settings")
    
    # 1. Background Color Picker
    bg_color_hex = st.sidebar.color_picker("Choose Background Color", "#FFFFFF")
    
    # 2. Image Size Selection
    size_option = st.sidebar.selectbox(
        "Select Passport Size",
        [
            "2 x 2 inches (US / India)", 
            "35 x 45 mm (UK / Europe / Kenya)", 
            "Custom"
        ]
    )
    
    if size_option == "2 x 2 inches (US / India)":
        photo_width, photo_height = 600, 600  # 300 DPI equivalent
    elif size_option == "35 x 45 mm (UK / Europe / Kenya)":
        photo_width, photo_height = 413, 531  # 300 DPI equivalent
    else:
        col_w, col_h = st.sidebar.columns(2)
        custom_w = col_w.number_input("Width (px)", min_value=100, max_value=1000, value=600)
        custom_h = col_h.number_input("Height (px)", min_value=100, max_value=1000, value=600)
        photo_width, photo_height = int(custom_w), int(custom_h)

    # 3. Image Enhancements (Sliders)
    st.sidebar.markdown("### Adjustments")
    brightness = st.sidebar.slider("Brightness", 0.5, 2.0, 1.0, 0.1)
    contrast = st.sidebar.slider("Contrast", 0.5, 2.0, 1.0, 0.1)
    saturation = st.sidebar.slider("Saturation (Color)", 0.5, 2.0, 1.0, 0.1)

    # --- Processing Engine ---
    with st.spinner("Processing image..."):
        # 1. Remove background (returns transparent RGBA)
        no_bg_image = remove(input_image).convert("RGBA")
        
        # 2. Create solid background with selected color
        solid_bg = Image.new("RGBA", no_bg_image.size, bg_color_hex)
        
        # Combine transparent image over the solid colored background
        combined_image = Image.alpha_composite(solid_bg, no_bg_image).convert("RGB")
        
        # 3. Apply Brightness
        enhancer = ImageEnhance.Brightness(combined_image)
        combined_image = enhancer.enhance(brightness)
        
        # 4. Apply Contrast
        enhancer = ImageEnhance.Contrast(combined_image)
        combined_image = enhancer.enhance(contrast)
        
        # 5. Apply Saturation
        enhancer = ImageEnhance.Color(combined_image)
        combined_image = enhancer.enhance(saturation)

    # --- Display Layout ---
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.write("### 👤 Single Passport Preview")
        # Resize to selected passport size for preview
        preview_photo = combined_image.resize((photo_width, photo_height))
        st.image(preview_photo, caption=f"Size: {photo_width}x{photo_height} px", use_container_width=True)
        
    with col2:
        st.write("### 🖨️ Generated A4 Print Sheet")
        
        # Create blank A4 white canvas
        a4_canvas = Image.new("RGB", (A4_WIDTH, A4_HEIGHT), "white")
        
        # Dynamically calculate spacing based on selected size
        # Margin and spacing configuration
        margin_x = 150
        margin_y = 200
        gap = 80
        
        # Calculate how many columns and rows can physically fit on A4
        cols_count = (A4_WIDTH - (2 * margin_x)) // (photo_width + gap)
        rows_count = (A4_HEIGHT - (2 * margin_y)) // (photo_height + gap)
        
        # Render the grid
        for row in range(int(rows_count)):
            for col in range(int(cols_count)):
                x = margin_x + col * (photo_width + gap)
                y = margin_y + row * (photo_height + gap)
                a4_canvas.paste(preview_photo, (x, y))
                
        st.image(a4_canvas, caption="Preview of full A4 page", use_container_width=True)

    # --- Direct Print Trigger Code ---
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
                    @page {{
                        size: A4;
                        margin: 0;
                    }}
                    body {{
                        margin: 0;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        height: 100vh;
                        background-color: white;
                    }}
                    img {{
                        max-width: 100%;
                        max-height: 100%;
                        width: auto;
                        height: auto;
                        object-fit: contain;
                    }}
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
    
    st.components.v1.html(print_html, height=120)
