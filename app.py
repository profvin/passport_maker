import streamlit as st
from PIL import Image, ImageEnhance
from rembg import remove
import io

st.set_page_config(page_title="Local Passport Maker", layout="wide")
st.title("📸 Local Passport Photo Studio")
st.write("Optimized for all hair types and styles.")

# 1. SIDEBAR CONTROLS
st.sidebar.header("1. Document Settings")
country_sizes = {
    "US / India (2 x 2 inches)": (600, 600),
    "UK / EU / East Africa (35 x 45 mm)": (413, 531),
    "Custom Size": None
}
size_choice = st.sidebar.selectbox("Passport Standard", list(country_sizes.keys()))

if size_choice == "Custom Size":
    p_width = st.sidebar.number_input("Width (px)", value=413)
    p_height = st.sidebar.number_input("Height (px)", value=531)
    target_size = (p_width, p_height)
else:
    target_size = country_sizes[size_choice]

bg_color = st.sidebar.color_picker("Background Color", "#FFFFFF")

# NEW: Advanced Framing Controls to accommodate voluminous hair
st.sidebar.header("2. Crop & Framing")
zoom = st.sidebar.slider("Zoom Out / Padding", 1.0, 2.5, 1.2, 0.1, 
                        help="Increase this if a high or wide hairstyle is getting cut off.")
vertical_offset = st.sidebar.slider("Nudge Up/Down", -150, 150, 0, 5,
                                   help="Move the image up or down within the frame.")

st.sidebar.header("3. Image Adjustments")
brightness = st.sidebar.slider("Brightness", 0.5, 2.0, 1.0, 0.1)
sharpness = st.sidebar.slider("Detail Sharpness", 0.5, 2.5, 1.0, 0.1)

st.sidebar.header("4. Print Sheet Settings")
paper_sizes = {
    "4x6 inch Photo Paper": (1200, 1800),
    "A4 Paper": (2480, 3508)
}
paper_choice = st.sidebar.selectbox("Print Sheet Size", list(paper_sizes.keys()))
num_copies = st.sidebar.number_input("Number of Copies", min_value=1, max_value=30, value=8)

# 2. FILE UPLOADER
uploaded_file = st.file_uploader("Upload a Portrait Photo", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    raw_bytes = uploaded_file.read()
    image = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Original Image")
        st.image(image, use_container_width=True)
        
    with st.spinner("Analyzing silhouette and isolating hair..."):
        # Step 1: Remove the background FIRST on the full image
        # This gives us a transparent image containing only the person and their hair
        no_bg_full = remove(image)
        
        # Step 2: Automatically find the exact boundaries of the person (including protruding hair)
        # getbbox() returns (left, upper, right, lower) of the non-transparent pixels
        bbox = no_bg_full.getbbox()
        
        if bbox:
            b_left, b_top, b_right, b_bottom = bbox
            subj_w = b_right - b_left
            subj_h = b_bottom - b_top
            
            # Calculate center of the actual subject
            center_x = b_left + (subj_w / 2)
            center_y = b_top + (subj_h / 2) + vertical_offset
            
            # Target Passport Ratio (Height / Width)
            pass_ratio = target_size[1] / target_size[0]
            
            # Determine crop size based on the subject's size multiplied by the user's Zoom factor
            # This guarantees the entire hair and shoulders fit inside the frame
            crop_w = max(subj_w, subj_h / pass_ratio) * zoom
            crop_h = crop_w * pass_ratio
            
            # Calculate crop coordinates centered around the subject
            crop_left = max(0, int(center_x - (crop_w / 2)))
            crop_top = max(0, int(center_y - (crop_h / 2)))
            crop_right = min(image.width, int(center_x + (crop_w / 2)))
            crop_bottom = min(image.height, int(center_y + (crop_h / 2)))
            
            # Crop the transparent image
            cropped_subj = no_bg_full.crop((crop_left, crop_top, crop_right, crop_bottom))
        else:
            # Fallback if bbox detection fails
            cropped_subj = no_bg_full.resize(target_size)

        # Step 3: Resize to standard passport dimensions
        resized_subj = cropped_subj.resize(target_size, Image.Resampling.LANCZOS)
        
        # Step 4: Paste onto the user's chosen solid color background
        hex_color = bg_color.lstrip('#')
        rgb_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        solid_bg = Image.new("RGBA", target_size, rgb_color + (255,))
        
        # Composite subject over the colored background
        final_passport = Image.alpha_composite(solid_bg, resized_subj.convert("RGBA")).convert("RGB")
        
        # Step 5: Apply Image Adjustments
        if brightness != 1.0:
            final_passport = ImageEnhance.Brightness(final_passport).enhance(brightness)
        if sharpness != 1.0:
            final_passport = ImageEnhance.Sharpness(final_passport).enhance(sharpness)
        
    with col2:
        st.subheader("Processed Passport Photo")
        st.image(final_passport, caption="Single Copy Preview", width=250)

    # 3. SHEET GENERATION
    st.subheader("🖨️ Ready-to-Print Sheet Preview")
    
    sheet_w, sheet_h = paper_sizes[paper_choice]
    print_sheet = Image.new("RGB", (sheet_w, sheet_h), (255, 255, 255))
    
    margin = 50
    spacing = 30
    curr_x = margin
    curr_y = margin
    pass_w, pass_h = target_size
    
    copies_placed = 0
    for _ in range(num_copies):
        if curr_x + pass_w > sheet_w - margin:
            curr_x = margin
            curr_y += pass_h + spacing
            
        if curr_y + pass_h > sheet_h - margin:
            st.warning("All requested copies couldn't fit on a single page!")
            break
            
        print_sheet.paste(final_passport, (curr_x, curr_y))
        curr_x += pass_w + spacing
        copies_placed += 1
        
    st.image(print_sheet, caption=f"Print Sheet ({copies_placed} copies)", use_container_width=True)
    
    buf = io.BytesIO()
    print_sheet.save(buf, format="JPEG", quality=95)
    byte_im = buf.getvalue()
    
    st.download_button(
        label="Download Print-Ready JPEG",
        data=byte_im,
        file_name="passport_print_sheet.jpg",
        mime="image/jpeg"
    )