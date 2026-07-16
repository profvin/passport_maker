import streamlit as st
from PIL import Image
import io
import base64

# --- 1. Define A4 Canvas Dimensions (300 DPI) ---
A4_WIDTH = 2480
A4_HEIGHT = 3508

st.title("Express Passport Maker 📸")

# ... (Keep your existing image upload & cropping logic here) ...

# Assuming 'cropped_image' is the final cropped passport photo
if 'cropped_image' in locals() or 'cropped_image' in globals():
    st.write("### Step 2: Generate Print Sheet")
    
    # Create the blank A4 white canvas
    a4_canvas = Image.new("RGB", (A4_WIDTH, A4_HEIGHT), "white")
    
    # Size of a standard passport photo at 300 DPI (approx 2 x 2 inches -> 600 x 600 pixels)
    # Adjust width/height depending on your target passport size
    photo_width = 600
    photo_height = 600
    resized_photo = cropped_image.resize((photo_width, photo_height))
    
    # Paste photos in a grid (e.g., 4 columns x 5 rows)
    margin_x = 150
    margin_y = 200
    gap = 100
    
    for row in range(5):
        for col in range(4):
            x = margin_x + col * (photo_width + gap)
            y = margin_y + row * (photo_height + gap)
            a4_canvas.paste(resized_photo, (x, y))
            
    # --- 2. Direct Preview ---
    st.write("### 🖨️ Print Preview (A4 Sheet)")
    st.image(a4_canvas, caption="This is exactly how it will print on A4 paper", use_container_width=True)

    # Convert the PIL image to Base64 to allow direct printing via HTML
    buffered = io.BytesIO()
    a4_canvas.save(buffered, format="JPEG", quality=95)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    img_data_uri = f"data:image/jpeg;base64,{img_str}"

    # --- 3. Direct Print Engine (HTML + JS) ---
    # This code creates a button. When clicked, it opens a clean window containing ONLY the image and fires the print dialog.
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
        padding: 12px 24px;
        font-size: 16px;
        font-weight: bold;
        border-radius: 8px;
        cursor: pointer;
        width: 100%;
        box-shadow: 0px 4px 6px rgba(0,0,0,0.1);
    ">
        🖨️ Open Print Dialog (A4)
    </button>
    """
    
    # Render the custom print button safely in Streamlit
    st.components.v1.html(print_html, height=80)
