with col2:
        st.write(f"### 🖨️ Generated A4 Print Sheet ({num_copies} Copies)")
        
        # Create blank A4 white canvas (300 DPI)
        a4_canvas = Image.new("RGB", (A4_WIDTH, A4_HEIGHT), "white")
        
        # --- REDUCED MARGINS & GAPS TO FIT 5 COLUMNS ---
        margin_x = 80   # Reduced from 150 to give more horizontal room
        margin_y = 120  # Reduced from 200
        gap = 40        # Reduced from 80 to bring photos closer together
        
        # Calculate grid parameters safely
        step_w = photo_width + gap
        step_h = photo_height + gap
        
        if step_w > 0 and step_h > 0:
            cols_count = (A4_WIDTH - (2 * margin_x)) // step_w
            rows_count = (A4_HEIGHT - (2 * margin_y)) // step_h
        else:
            cols_count, rows_count = 1, 1
        
        # Render the copies on the A4 canvas
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
