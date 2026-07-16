import streamlit as st
from PIL import Image, ImageEnhance
import io
import base64
from rembg import remove

# Set page configuration
st.set_page_config(page_title="Express Passport Maker", layout="wide")

# --- 1. Define A4 Canvas Dimensions (300 DPI) ---
A4_WIDTH = 2480
A4_HEIGHT = 3508

st.title("Express Passport Maker 📸")

# --- Step 1: File Uploader ---
uploaded_file = st.file_uploader("Upload a portrait photo", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # 1. Load and display original image
    input_image = Image.open(uploaded_file)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### Original Photo")
        st.image(input_image, use_container_width=True)
        
    with col2:
        st.write("### Processing...")
        # 2. Remove background
        with st.spinner("Removing background..."):
            no_bg_image = remove(input_image)
            
        # 3. Brightness control
        brightness = st.slider("Adjust Brightness", 0.5, 2.0, 1.0, 0.1)
        enhancer = ImageEnhance.Brightness(no_bg_image)
        processed_image = enhancer.enhance(brightness)
        
        st.image(processed_image, caption="Processed Image", use_container_width=True)

    # --- Step 2: Generate A4 Print Sheet ---
    st.markdown("---")
    st.write("### Step 2: Generate Print Sheet")
    
    # Create a blank A4 white canvas
    a4_canvas = Image.new("RGB", (A4_WIDTH, A4_HEIGHT), "white")
    
    # Size of a standard passport photo at 300 DPI (approx 2 x 2 inches -> 600 x 600 pixels)
    photo_width = 600
    photo_height = 600
    
    # Resize our processed image to passport dimensions
    resized_photo = processed_image.convert("RGB").resize((photo_width, photo_height))
    
    # Paste photos in a grid (5 rows x 4 columns = 20 passport photos)
    margin_x = 150
    margin_y = 200
    gap = 100
    
    for row in range(5):
        for col in range(4):
            x = margin_x + col * (photo_width + gap)
            y = margin_y + row * (photo_height + gap)
            a4_canvas.paste(resized_photo, (x, y))
            
    # --- Step 3: Print Preview ---
    st.write("### 🖨️ Print Preview (A4 Sheet)")
    st.image(a4_canvas, caption="This is exactly how it will print on A4 paper", use_container_width=True)

    # Convert the canvas to Base64 to enable direct printing through the browser
    buffered = io.BytesIO()
    a4_canvas.save(buffered, format="JPEG", quality=95)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    img_data_uri = f"data:image/jpeg;base64,{img_str}"

    # --- Step 4: Direct Print Engine Button (HTML + JavaScript) ---
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
        padding: 14px 28px;
        font-size: 18px;
        font-weight: bold;
        border-radius: 8px;
        cursor: pointer;
        width: 100%;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 50px;
    ">
        🖨️ Open Print Dialog (A4)
    </button>
    """
    
    st.components.v1.html(print_html, height=100)
