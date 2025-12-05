import xml.etree.ElementTree as ET


def invert_hex_color(hex_color):
    """Convert hex color to its inverse"""
    # Remove the # symbol
    hex_color = hex_color.replace('#', '')
    
    # Convert each pair of hex digits to decimal, invert, convert back to hex
    r = 255 - int(hex_color[0:2], 16)
    g = 255 - int(hex_color[2:4], 16) 
    b = 255 - int(hex_color[4:6], 16)
    
    # Format back to hex with leading zeros
    return f"#{r:02x}{g:02x}{b:02x}"


def invert_svg_colors(input_file, output_file):
    """Read SVG, invert all hex colors, save new SVG"""
    
    # Parse the SVG
    tree = ET.parse(input_file)
    root = tree.getroot()
    
    colors_inverted = 0
    
    # Go through every element
    for element in root.iter():
        
        # Check fill attribute
        fill = element.get('fill')
        if fill and fill.startswith('#') and len(fill) == 7:
            inverted_fill = invert_hex_color(fill)
            element.set('fill', inverted_fill)
            print(f"Inverted fill: {fill} → {inverted_fill}")
            colors_inverted += 1
        
        # Check stroke attribute  
        stroke = element.get('stroke')
        if stroke and stroke.startswith('#') and len(stroke) == 7:
            inverted_stroke = invert_hex_color(stroke)
            element.set('stroke', inverted_stroke)
            print(f"Inverted stroke: {stroke} → {inverted_stroke}")
            colors_inverted += 1
    
    # Save the modified SVG
    tree.write(output_file, encoding='utf-8', xml_declaration=True)
    print(f"\nInverted {colors_inverted} colors")
    print(f"Saved inverted SVG to: {output_file}")


# Run the inversion
input_file = 'bw_vector.svg'
output_file = 'inverted_vector.svg'
invert_svg_colors(input_file, output_file)