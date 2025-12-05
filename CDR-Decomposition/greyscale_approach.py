import os
import xml.etree.ElementTree as ET
import re

#usage python3 greyscale_approach.py input.svg output.svg

def convert_svg_to_greyscale(svg_path: str, output_svg_path: str = None) -> str:
    """
    Convert all colors in an SVG to greyscale values.
    
    Preserves all vector elements, fills, strokes, and gradients but converts
    all colors to their greyscale equivalents using luminance calculation.
    
    Args:
        svg_path: Path to the input SVG file
        output_svg_path: Path for the greyscale SVG (defaults to input_greyscale.svg)
    
    Returns:
        Path to the greyscale SVG file
        
    Raises:
        FileNotFoundError: If input SVG doesn't exist
        RuntimeError: If SVG processing fails
    """
    svg_path = os.path.abspath(svg_path)
    
    if not os.path.exists(svg_path):
        raise FileNotFoundError(f"SVG file not found: {svg_path}")
    
    if output_svg_path is None:
        base_name = os.path.splitext(os.path.basename(svg_path))[0]
        output_svg_path = os.path.join(
            os.path.dirname(svg_path),
            f"{base_name}_greyscale.svg"
        )
    
    output_svg_path = os.path.abspath(output_svg_path)
    
    print(f"[Processing] Converting colors to greyscale in {svg_path}")
    
    try:
        # Parse the SVG file
        tree = ET.parse(svg_path)
        root = tree.getroot()
        
        converted_count = 0
        
        # Process gradients in defs first
        defs_elements = root.findall(".//{http://www.w3.org/2000/svg}defs") + root.findall(".//defs")
        for defs in defs_elements:
            for child in defs:
                if child.tag.endswith('linearGradient') or child.tag.endswith('radialGradient'):
                    _convert_gradient_to_greyscale(child)
                    converted_count += 1
        
        # Process all elements
        for elem in root.iter():
            # Convert element colors
            if _convert_element_colors_to_greyscale(elem):
                converted_count += 1
        
        print(f"[OK] Converted {converted_count} elements to greyscale")
        
        # Write the greyscale SVG
        tree.write(output_svg_path, encoding='utf-8', xml_declaration=True)
        
        print(f"[OK] Greyscale SVG saved to: {output_svg_path}")
        return output_svg_path
        
    except ET.ParseError as e:
        raise RuntimeError(f"Failed to parse SVG file: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to process SVG file: {e}")


def _color_to_greyscale(color_value: str) -> str:
    """Convert a color value to its greyscale equivalent using luminance."""
    if not color_value or color_value in ['none', 'transparent', 'inherit', 'currentColor']:
        return color_value
    
    # Already greyscale (pure grays)
    if _is_greyscale_color(color_value):
        return color_value
    
    try:
        # Parse different color formats and calculate luminance
        luminance = 0
        
        if color_value.startswith('#'):
            # Hex color
            hex_color = color_value[1:]
            if len(hex_color) == 3:
                hex_color = ''.join([c*2 for c in hex_color])  # Convert #RGB to #RRGGBB
            
            if len(hex_color) == 6:
                r = int(hex_color[0:2], 16)
                g = int(hex_color[2:4], 16)
                b = int(hex_color[4:6], 16)
                # Calculate relative luminance (ITU-R BT.709)
                luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
        
        elif color_value.startswith('rgb'):
            # RGB color
            rgb_match = re.search(r'rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', color_value)
            if rgb_match:
                r, g, b = map(int, rgb_match.groups())
                luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
            else:
                # Try RGBA format
                rgba_match = re.search(r'rgba\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([0-9.]+)\s*\)', color_value)
                if rgba_match:
                    r, g, b, a = map(float, rgba_match.groups())
                    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
                    # Keep alpha channel
                    grey_value = int(round(luminance))
                    return f"rgba({grey_value}, {grey_value}, {grey_value}, {a})"
        
        elif color_value.lower() in _get_named_color_values():
            # Named colors
            r, g, b = _get_named_color_values()[color_value.lower()]
            luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
        
        # Convert luminance to greyscale hex
        grey_value = int(round(min(255, max(0, luminance))))
        return f"#{grey_value:02x}{grey_value:02x}{grey_value:02x}"
        
    except Exception as e:
        print(f"[Warning] Could not convert color '{color_value}' to greyscale: {e}")
        # Fallback to medium gray
        return "#808080"


def _is_greyscale_color(color_value: str) -> bool:
    """Check if a color is already greyscale."""
    try:
        if color_value.startswith('#'):
            hex_color = color_value[1:]
            if len(hex_color) == 3:
                # #RGB format - check if R=G=B
                return hex_color[0] == hex_color[1] == hex_color[2]
            elif len(hex_color) == 6:
                # #RRGGBB format - check if RR=GG=BB
                return hex_color[0:2] == hex_color[2:4] == hex_color[4:6]
        
        elif color_value.startswith('rgb'):
            rgb_match = re.search(r'rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', color_value)
            if rgb_match:
                r, g, b = map(int, rgb_match.groups())
                return r == g == b
        
        elif color_value.lower() in ['black', 'white', 'gray', 'grey']:
            return True
            
        return False
        
    except:
        return False


def _get_named_color_values() -> dict:
    """Get RGB values for common named colors."""
    return {
        'red': (255, 0, 0),
        'green': (0, 128, 0),
        'blue': (0, 0, 255),
        'yellow': (255, 255, 0),
        'cyan': (0, 255, 255),
        'magenta': (255, 0, 255),
        'orange': (255, 165, 0),
        'purple': (128, 0, 128),
        'pink': (255, 192, 203),
        'brown': (165, 42, 42),
        'black': (0, 0, 0),
        'white': (255, 255, 255),
        'gray': (128, 128, 128),
        'grey': (128, 128, 128),
        'lime': (0, 255, 0),
        'navy': (0, 0, 128),
        'olive': (128, 128, 0),
        'maroon': (128, 0, 0),
        'teal': (0, 128, 128),
        'silver': (192, 192, 192),
        'gold': (255, 215, 0),
        'violet': (238, 130, 238),
        'indigo': (75, 0, 130),
        'tan': (210, 180, 140),
        'coral': (255, 127, 80)
    }


def _convert_element_colors_to_greyscale(element) -> bool:
    """Convert all colors in an element to greyscale. Returns True if any changes made."""
    changed = False
    
    # Convert fill
    fill = element.get('fill')
    if fill:
        new_fill = _color_to_greyscale(fill)
        if new_fill != fill:
            element.set('fill', new_fill)
            changed = True
    
    # Convert stroke
    stroke = element.get('stroke')
    if stroke:
        new_stroke = _color_to_greyscale(stroke)
        if new_stroke != stroke:
            element.set('stroke', new_stroke)
            changed = True
    
    # Convert style attribute
    style = element.get('style')
    if style:
        new_style_parts = []
        properties = [prop.strip() for prop in style.split(';') if prop.strip()]
        
        for prop in properties:
            if ':' in prop:
                key, value = prop.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                if key in ['fill', 'stroke', 'stop-color', 'color']:
                    new_value = _color_to_greyscale(value)
                    new_style_parts.append(f"{key}: {new_value}")
                    if new_value != value:
                        changed = True
                else:
                    new_style_parts.append(prop)
            else:
                new_style_parts.append(prop)
        
        if changed:
            element.set('style', '; '.join(new_style_parts))
    
    # Convert stop-color for gradient stops
    stop_color = element.get('stop-color')
    if stop_color:
        new_stop_color = _color_to_greyscale(stop_color)
        if new_stop_color != stop_color:
            element.set('stop-color', new_stop_color)
            changed = True
    
    # Convert color attribute (for text elements)
    color = element.get('color')
    if color:
        new_color = _color_to_greyscale(color)
        if new_color != color:
            element.set('color', new_color)
            changed = True
    
    return changed


def _convert_gradient_to_greyscale(gradient_elem):
    """Convert all colors in a gradient to greyscale."""
    # Find all stop elements
    for stop in gradient_elem.findall(".//{http://www.w3.org/2000/svg}stop") + gradient_elem.findall(".//stop"):
        _convert_element_colors_to_greyscale(stop)


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python greyscale_approach.py <input_svg_file> [output_svg_file]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        result = convert_svg_to_greyscale(input_file, output_file)
        print(f"\n=== GREYSCALE CONVERSION COMPLETE ===")
        print(f"Input:  {input_file}")
        print(f"Output: {result}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)