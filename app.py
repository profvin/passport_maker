import streamlit as st
from PIL import Image, ImageEnhance, ImageOps
import io
import base64

# Try to import rembg safely
try:
    from rembg import remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False

st.set_page_config(page_title="Express Passport Maker", layout="wide")

st.title("Express Passport Maker 📸")

if not REMBG_AVAILABLE:
    st.error("The background removal library ('rembg') is not installed correctly. Run: pip install rembg")

uploaded_file = st.file_uploader("Upload a portrait photo", type=["jpg", "jpeg", "png"])

if uploaded_file is not None and REMBG_AVAILABLE:
    input_image = Image.open(uploaded_file)
    
    st.write("### Settings")
    bg_color_hex = st.color_picker("Choose Background Color", "#FFFFFF")
    
    # Simple default size to test stability
    photo_width, photo_height = 600, 600
    
    with st.spinner("Processing..."):
        # Remove background
        no_bg_image = remove(input_image).convert("RGBA")
        
        # Crop & Fit
        fitted_subject = ImageOps.fit(no_bg_image, (photo_width, photo_height), Image.Resampling.LANCZOS)
        
        # Canvas
        solid_bg = Image.new("RGBA", (photo_width, photo_height), bg_color_hex)
        combined_image = Image.alpha_composite(solid_bg, fitted_subject).convert("RGB")
        
    st.image(combined_image, caption="Preview", width=300)
