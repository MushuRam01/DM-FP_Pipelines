import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
import base64
import json
import re
from urllib.parse import urlparse

def cdr_to_pdf(cdr_path: str, pdf_path: str) -> str:
    """
    Convert a CorelDRAW .cdr file to both SVG and PDF using LibreOffice Draw.

    Uses LibreOffice Draw to first convert CDR to SVG (preserving vectors),
    then converts the SVG to PDF. Both SVG and PDF files are kept.
    
    Returns the absolute path to the generated PDF.
    Raises RuntimeError if conversion fails.
    """
    cdr_path = os.path.abspath(cdr_path)
    pdf_path = os.path.abspath(pdf_path)

    if not os.path.exists(cdr_path):
        raise FileNotFoundError(f"Input file not found: {cdr_path}")

    # Check if LibreOffice is available
    libreoffice = shutil.which("libreoffice")
    if libreoffice is None:
        raise RuntimeError(
            "LibreOffice not found. Install with:\n"
            "sudo apt install libreoffice"
        )

    # Step 1: Convert CDR to SVG using LibreOffice Draw
    svg_path = os.path.join(
        os.path.dirname(pdf_path),
        os.path.splitext(os.path.basename(cdr_path))[0] + ".svg"
    )
    
    print(f"[Step 1] Converting {cdr_path} -> {svg_path}")
    cmd_svg = [
        libreoffice,
        "--headless",
        "--convert-to", "svg",
        "--outdir", os.path.dirname(svg_path),
        cdr_path
    ]
    
    result = subprocess.run(cmd_svg, capture_output=True, text=True)
    expected_svg = os.path.join(
        os.path.dirname(svg_path),
        os.path.splitext(os.path.basename(cdr_path))[0] + ".svg"
    )
    
    if result.returncode != 0 or not os.path.exists(expected_svg):
        raise RuntimeError(f"LibreOffice failed to convert CDR to SVG:\n{result.stderr}")
    
    if expected_svg != svg_path:
        shutil.move(expected_svg, svg_path)
    
    print(f"[OK] CDR -> SVG conversion completed: {svg_path}")

    # Step 2: Convert SVG to PDF using LibreOffice Draw
    print(f"[Step 2] Converting {svg_path} -> {pdf_path}")
    cmd_pdf = [
        libreoffice,
        "--headless",
        "--convert-to", "pdf",
        "--outdir", os.path.dirname(pdf_path),
        svg_path
    ]
    
    result = subprocess.run(cmd_pdf, capture_output=True, text=True)
    expected_pdf = os.path.join(
        os.path.dirname(pdf_path),
        os.path.splitext(os.path.basename(svg_path))[0] + ".pdf"
    )
    
    if result.returncode != 0 or not os.path.exists(expected_pdf):
        raise RuntimeError(f"LibreOffice failed to convert SVG to PDF:\n{result.stderr}")
    
    if expected_pdf != pdf_path:
        shutil.move(expected_pdf, pdf_path)
    
    print(f"[OK] SVG -> PDF conversion completed: {pdf_path}")
    
    print(f"[OK] Final conversion complete:")
    print(f"  SVG file: {svg_path}")
    print(f"  PDF file: {pdf_path}")
    return pdf_path


def remove_raster_from_svg(svg_path: str, output_svg_path: str = None, save_rasters: bool = True) -> str:
    """
    Remove all raster components from an SVG file, keeping only vector elements.
    
    Removes <image> elements and any embedded bitmap data while preserving
    all vector graphics (paths, text, shapes, etc.). Optionally saves extracted
    raster images to a separate folder for reconstruction workflow.
    
    Args:
        svg_path: Path to the input SVG file
        output_svg_path: Path for the cleaned SVG (defaults to input_vectors.svg)
        save_rasters: Whether to save extracted raster images (default: True)
    
    Returns:
        Path to the cleaned SVG file
        
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
            f"{base_name}_vectors.svg"
        )
    
    output_svg_path = os.path.abspath(output_svg_path)
    
    # Create raster extraction folder
    raster_folder = None
    if save_rasters:
        base_name = os.path.splitext(os.path.basename(svg_path))[0]
        raster_folder = os.path.join(
            os.path.dirname(svg_path),
            f"{base_name}_extracted_rasters"
        )
        os.makedirs(raster_folder, exist_ok=True)
        print(f"[Setup] Raster extraction folder: {raster_folder}")
    
    print(f"[Processing] Removing raster elements from {svg_path}")
    
    try:
        # Parse the SVG file
        tree = ET.parse(svg_path)
        root = tree.getroot()
        
        # Counter for removed elements
        removed_count = 0
        saved_count = 0
        
        # Find all elements to remove (iterate through all elements)
        elements_to_remove = []
        
        for elem in root.iter():
            # Check if element is an image tag (handle both namespaced and non-namespaced)
            if elem.tag.endswith('image') or 'image' in elem.tag.lower():
                elements_to_remove.append((elem, 'image_tag'))
                continue
            
            # Check for data URL in href attributes
            href = elem.get('href') or elem.get('{http://www.w3.org/1999/xlink}href')
            if href and href.startswith('data:image/'):
                elements_to_remove.append((elem, 'data_url'))
                continue
        
        # Remove the identified elements and save raster data
        for elem_to_remove, removal_type in elements_to_remove:
            # Save raster data before removing
            if save_rasters and raster_folder:
                saved_file = _save_raster_element(elem_to_remove, raster_folder, saved_count + 1)
                if saved_file:
                    saved_count += 1
                    print(f"[Saved] Raster image: {saved_file}")
            
            # Find the parent and remove the element
            for parent in root.iter():
                if elem_to_remove in list(parent):
                    parent.remove(elem_to_remove)
                    removed_count += 1
                    print(f"[Removed] {removal_type}: {elem_to_remove.tag}")
                    break
        
        print(f"[OK] Removed {removed_count} raster elements")
        if save_rasters:
            print(f"[OK] Saved {saved_count} raster images to {raster_folder}")
        
        # Write the cleaned SVG
        tree.write(output_svg_path, encoding='utf-8', xml_declaration=True)
        
        print(f"[OK] Vector-only SVG saved to: {output_svg_path}")
        return output_svg_path
        
    except ET.ParseError as e:
        raise RuntimeError(f"Failed to parse SVG file: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to process SVG file: {e}")


def remove_colors_from_svg(svg_path: str, output_svg_path: str = None, save_colors: bool = True) -> str:
    """
    Remove fill colors from an SVG file while preserving vector outlines.
    
    Removes fill colors, gradients, and patterns while preserving stroke outlines
    for fold lines, shape boundaries, etc. All outlines are converted to black
    for consistency. Saves color profiles for reconstruction workflow.
    
    Args:
        svg_path: Path to the input SVG file
        output_svg_path: Path for the outline-only SVG (defaults to input_outlines.svg)
        save_colors: Whether to save extracted color data (default: True)
    
    Returns:
        Path to the outline-only SVG file
        
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
            f"{base_name}_outlines.svg"
        )
    
    output_svg_path = os.path.abspath(output_svg_path)
    
    # Create color extraction folder
    color_folder = None
    if save_colors:
        base_name = os.path.splitext(os.path.basename(svg_path))[0]
        color_folder = os.path.join(
            os.path.dirname(svg_path),
            f"{base_name}_extracted_colors"
        )
        os.makedirs(color_folder, exist_ok=True)
        print(f"[Setup] Color extraction folder: {color_folder}")
    
    print(f"[Processing] Removing colors from {svg_path}")
    
    try:
        # Parse the SVG file
        tree = ET.parse(svg_path)
        root = tree.getroot()
        
        # Data structures for color extraction
        color_data = {
            "elements": [],
            "gradients": {},
            "patterns": {},
            "styles": {}
        }
        
        element_index = 0
        
        # First pass: Extract gradient and pattern definitions
        defs_elements = root.findall(".//{http://www.w3.org/2000/svg}defs") + root.findall(".//defs")
        for defs in defs_elements:
            for child in list(defs):
                if child.tag.endswith('linearGradient') or child.tag.endswith('radialGradient'):
                    gradient_id = child.get('id')
                    if gradient_id:
                        color_data["gradients"][gradient_id] = _extract_gradient_data(child)
                        print(f"[Extracted] Gradient: {gradient_id}")
                
                elif child.tag.endswith('pattern'):
                    pattern_id = child.get('id')
                    if pattern_id:
                        color_data["patterns"][pattern_id] = _extract_pattern_data(child)
                        print(f"[Extracted] Pattern: {pattern_id}")
        
        # Second pass: Process all elements and remove colors
        for elem in root.iter():
            # Skip defs, gradients, and patterns (already processed)
            if (elem.tag.endswith('defs') or elem.tag.endswith('linearGradient') or 
                elem.tag.endswith('radialGradient') or elem.tag.endswith('pattern')):
                continue
            
            element_colors = _extract_element_colors(elem, element_index)
            if element_colors:
                color_data["elements"].append(element_colors)
                element_index += 1
            
            # Remove color attributes
            _remove_color_attributes(elem)
        
        # Remove gradient and pattern definitions from defs
        for defs in defs_elements:
            children_to_remove = []
            for child in defs:
                if (child.tag.endswith('linearGradient') or child.tag.endswith('radialGradient') or 
                    child.tag.endswith('pattern')):
                    children_to_remove.append(child)
            
            for child in children_to_remove:
                defs.remove(child)
        
        # Save color data
        if save_colors and color_folder:
            _save_color_data(color_data, color_folder)
        
        print(f"[OK] Removed fill colors from {len(color_data['elements'])} elements (preserved outlines)")
        print(f"[OK] Extracted {len(color_data['gradients'])} gradients and {len(color_data['patterns'])} patterns")
        
        # Write the outline-only SVG
        tree.write(output_svg_path, encoding='utf-8', xml_declaration=True)
        
        print(f"[OK] Outline-only SVG saved to: {output_svg_path}")
        return output_svg_path
        
    except ET.ParseError as e:
        raise RuntimeError(f"Failed to parse SVG file: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to process SVG file: {e}")


def _extract_element_colors(element, element_index: int) -> dict:
    """Extract color information from a single element."""
    colors = {}
    
    # Get element identifier
    elem_id = element.get('id') or f"element_{element_index}"
    colors['element_id'] = elem_id
    colors['tag'] = element.tag
    colors['index'] = element_index
    
    # Extract fill colors
    fill = element.get('fill')
    if fill and fill != 'none':
        colors['fill'] = fill
    
    # Extract stroke colors
    stroke = element.get('stroke')
    if stroke and stroke != 'none':
        colors['stroke'] = stroke
        # Also get stroke properties
        stroke_width = element.get('stroke-width')
        if stroke_width:
            colors['stroke_width'] = stroke_width
        stroke_opacity = element.get('stroke-opacity')
        if stroke_opacity:
            colors['stroke_opacity'] = stroke_opacity
    
    # Extract opacity
    opacity = element.get('opacity')
    if opacity:
        colors['opacity'] = opacity
    
    fill_opacity = element.get('fill-opacity')
    if fill_opacity:
        colors['fill_opacity'] = fill_opacity
    
    # Extract style attribute colors
    style = element.get('style')
    if style:
        style_colors = _parse_style_colors(style)
        if style_colors:
            colors['style'] = style_colors
    
    # Only return if we found colors
    return colors if len(colors) > 3 else None  # More than just id, tag, index


def _parse_style_colors(style_string: str) -> dict:
    """Parse color information from CSS style strings."""
    style_colors = {}
    
    # Parse CSS properties
    properties = [prop.strip() for prop in style_string.split(';') if prop.strip()]
    
    for prop in properties:
        if ':' in prop:
            key, value = prop.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            if key in ['fill', 'stroke', 'opacity', 'fill-opacity', 'stroke-opacity', 'stroke-width']:
                if value != 'none':
                    style_colors[key] = value
    
    return style_colors


def _extract_gradient_data(gradient_elem) -> dict:
    """Extract gradient definition data."""
    gradient_data = {
        'type': 'linear' if gradient_elem.tag.endswith('linearGradient') else 'radial',
        'attributes': dict(gradient_elem.attrib),
        'stops': []
    }
    
    # Extract gradient stops
    for stop in gradient_elem.findall(".//{http://www.w3.org/2000/svg}stop") + gradient_elem.findall(".//stop"):
        stop_data = {
            'offset': stop.get('offset', '0%'),
            'stop_color': stop.get('stop-color'),
            'stop_opacity': stop.get('stop-opacity')
        }
        # Also check style attribute
        style = stop.get('style')
        if style:
            style_colors = _parse_style_colors(style)
            stop_data.update(style_colors)
        
        gradient_data['stops'].append(stop_data)
    
    return gradient_data


def _extract_pattern_data(pattern_elem) -> dict:
    """Extract pattern definition data."""
    pattern_data = {
        'attributes': dict(pattern_elem.attrib),
        'content': ET.tostring(pattern_elem, encoding='unicode')
    }
    return pattern_data


def _remove_color_attributes(element):
    """Remove fill colors but preserve stroke outlines from an element."""
    # Always remove fill colors (solid fills, gradients, patterns)
    fill_attrs = ['fill', 'fill-opacity']
    
    for attr in fill_attrs:
        if attr in element.attrib:
            del element.attrib[attr]
    
    # Keep stroke properties but remove stroke colors
    stroke = element.get('stroke')
    if stroke and stroke not in ['none', 'transparent']:
        # Convert colored strokes to black outline for visibility
        element.set('stroke', '#000000')  # Black outline
        
        # Preserve stroke properties but ensure visibility
        stroke_width = element.get('stroke-width')
        if not stroke_width or stroke_width == '0':
            element.set('stroke-width', '1px')  # Default visible width
    
    # Remove opacity but preserve stroke opacity for outlines
    opacity_attrs = ['opacity', 'fill-opacity']
    for attr in opacity_attrs:
        if attr in element.attrib:
            del element.attrib[attr]
    
    # Process style attribute - remove fills, preserve strokes
    style = element.get('style')
    if style:
        new_style_parts = []
        properties = [prop.strip() for prop in style.split(';') if prop.strip()]
        
        for prop in properties:
            if ':' in prop:
                key, value = prop.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove fill properties
                if key in ['fill', 'fill-opacity', 'opacity']:
                    continue
                
                # Convert stroke color to black but keep stroke properties
                elif key == 'stroke' and value not in ['none', 'transparent']:
                    new_style_parts.append('stroke: #000000')
                elif key == 'stroke-width':
                    # Ensure minimum visible width
                    if value == '0' or value == '0px':
                        new_style_parts.append('stroke-width: 1px')
                    else:
                        new_style_parts.append(prop)
                elif key in ['stroke-opacity', 'stroke-dasharray', 'stroke-linecap', 'stroke-linejoin']:
                    # Keep other stroke properties
                    new_style_parts.append(prop)
                else:
                    # Keep non-color, non-fill properties
                    if key not in ['fill', 'fill-opacity', 'opacity']:
                        new_style_parts.append(prop)
        
        if new_style_parts:
            element.set('style', '; '.join(new_style_parts))
        elif 'style' in element.attrib:
            del element.attrib['style']


def _save_color_data(color_data: dict, color_folder: str):
    """Save extracted color data to files."""
    
    # Save main color data as JSON
    color_file = os.path.join(color_folder, "color_data.json")
    with open(color_file, 'w') as f:
        json.dump(color_data, f, indent=2)
    print(f"[Saved] Color data: {color_file}")
    
    # Save human-readable summary
    summary_file = os.path.join(color_folder, "color_summary.txt")
    with open(summary_file, 'w') as f:
        f.write("=== SVG Color Extraction Summary ===\n\n")
        
        f.write(f"Elements with colors: {len(color_data['elements'])}\n")
        f.write(f"Gradients extracted: {len(color_data['gradients'])}\n")
        f.write(f"Patterns extracted: {len(color_data['patterns'])}\n\n")
        
        # List gradients
        if color_data['gradients']:
            f.write("GRADIENTS:\n")
            for grad_id, grad_data in color_data['gradients'].items():
                f.write(f"  {grad_id} ({grad_data['type']}): {len(grad_data['stops'])} stops\n")
            f.write("\n")
        
        # List patterns
        if color_data['patterns']:
            f.write("PATTERNS:\n")
            for pat_id in color_data['patterns'].keys():
                f.write(f"  {pat_id}\n")
            f.write("\n")
        
        # Sample of element colors
        f.write("SAMPLE ELEMENT COLORS:\n")
        for i, elem_data in enumerate(color_data['elements'][:10]):  # First 10
            f.write(f"  Element {elem_data['element_id']} ({elem_data['tag']}):\n")
            for key, value in elem_data.items():
                if key not in ['element_id', 'tag', 'index']:
                    f.write(f"    {key}: {value}\n")
        
        if len(color_data['elements']) > 10:
            f.write(f"  ... and {len(color_data['elements']) - 10} more elements\n")
    
        print(f"[Saved] Color summary: {summary_file}")


def create_black_white_svg(svg_path: str, output_svg_path: str = None) -> str:
    """
    Convert all non-black colors in an SVG to white.
    
    Preserves all vector elements, fills, strokes, and gradients but converts
    any color that is not black to white. Black colors remain black.
    
    Args:
        svg_path: Path to the input SVG file
        output_svg_path: Path for the black/white SVG (defaults to input_bw.svg)
    
    Returns:
        Path to the black and white SVG file
        
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
            f"{base_name}_bw.svg"
        )
    
    output_svg_path = os.path.abspath(output_svg_path)
    
    print(f"[Processing] Converting non-black colors to white in {svg_path}")
    
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
                    _convert_gradient_to_bw(child)
                    converted_count += 1
        
        # Process all elements
        for elem in root.iter():
            # Convert element colors
            if _convert_element_colors_to_bw(elem):
                converted_count += 1
        
        print(f"[OK] Converted {converted_count} elements (non-black → white)")
        
        # Write the black/white SVG
        tree.write(output_svg_path, encoding='utf-8', xml_declaration=True)
        
        print(f"[OK] Black/white SVG saved to: {output_svg_path}")
        return output_svg_path
        
    except ET.ParseError as e:
        raise RuntimeError(f"Failed to parse SVG file: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to process SVG file: {e}")


def _color_to_bw(color_value: str) -> str:
    """Convert a color value: keep black, change everything else to white."""
    if not color_value or color_value in ['none', 'transparent', 'inherit', 'currentColor']:
        return color_value
    
    # Keep black colors as black
    if color_value.lower() in ['#000000', '#000', 'black']:
        return '#000000'
    
    # Convert everything else to white
    try:
        # Check if it's actually black in different formats
        if color_value.startswith('#'):
            # Hex color
            hex_color = color_value[1:]
            if len(hex_color) == 3:
                hex_color = ''.join([c*2 for c in hex_color])  # Convert #RGB to #RRGGBB
            
            if len(hex_color) == 6 and hex_color.lower() == '000000':
                return '#000000'  # Keep pure black
        
        elif color_value.startswith('rgb'):
            # RGB color
            import re
            rgb_match = re.search(r'rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', color_value)
            if rgb_match:
                r, g, b = map(int, rgb_match.groups())
                if r == 0 and g == 0 and b == 0:
                    return '#000000'  # Keep pure black
        
        # Everything else becomes white
        return '#ffffff'
        
    except:
        # Fallback to white for unparseable colors
        return '#ffffff'


def _convert_element_colors_to_bw(element) -> bool:
    """Convert all non-black colors in an element to white. Returns True if any changes made."""
    changed = False
    
    # Convert fill
    fill = element.get('fill')
    if fill:
        new_fill = _color_to_bw(fill)
        if new_fill != fill:
            element.set('fill', new_fill)
            changed = True
    
    # Convert stroke
    stroke = element.get('stroke')
    if stroke:
        new_stroke = _color_to_bw(stroke)
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
                
                if key in ['fill', 'stroke', 'stop-color']:
                    new_value = _color_to_bw(value)
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
        new_stop_color = _color_to_bw(stop_color)
        if new_stop_color != stop_color:
            element.set('stop-color', new_stop_color)
            changed = True
    
    return changed


def _convert_gradient_to_bw(gradient_elem):
    """Convert all non-black colors in a gradient to white."""
    # Find all stop elements
    for stop in gradient_elem.findall(".//{http://www.w3.org/2000/svg}stop") + gradient_elem.findall(".//stop"):
        _convert_element_colors_to_bw(stop)
def _save_raster_element(element, raster_folder: str, image_index: int) -> str:
    """
    Save a raster element (image) from SVG to a file.
    
    Args:
        element: XML element containing image data
        raster_folder: Folder to save extracted images
        image_index: Index for naming the image file
    
    Returns:
        Path to saved image file, or None if failed
    """
    try:
        # Get image data from href attributes
        href = element.get('href') or element.get('{http://www.w3.org/1999/xlink}href')
        
        if not href:
            print(f"[Warning] No href found in image element")
            return None
        
        if href.startswith('data:image/'):
            # Handle embedded base64 data
            try:
                # Parse data URL: data:image/png;base64,iVBORw0KGgo...
                header, data = href.split(',', 1)
                mime_part = header.split(';')[0].split(':')[1]  # Extract mime type
                
                # Determine file extension from mime type
                if 'png' in mime_part.lower():
                    ext = 'png'
                elif 'jpeg' in mime_part.lower() or 'jpg' in mime_part.lower():
                    ext = 'jpg'
                elif 'gif' in mime_part.lower():
                    ext = 'gif'
                elif 'svg' in mime_part.lower():
                    ext = 'svg'
                else:
                    ext = 'bin'  # Unknown format
                
                # Create filename
                filename = f"raster_{image_index:03d}.{ext}"
                filepath = os.path.join(raster_folder, filename)
                
                # Decode and save
                image_data = base64.b64decode(data)
                with open(filepath, 'wb') as f:
                    f.write(image_data)
                
                # Also save metadata
                metadata_file = os.path.join(raster_folder, f"raster_{image_index:03d}_metadata.txt")
                with open(metadata_file, 'w') as f:
                    f.write(f"Original href: {href[:100]}...\n")
                    f.write(f"MIME type: {mime_part}\n")
                    f.write(f"File size: {len(image_data)} bytes\n")
                    # Save element attributes
                    f.write("Element attributes:\n")
                    for key, value in element.attrib.items():
                        if not key.endswith('href'):  # Skip the long data URL
                            f.write(f"  {key}: {value}\n")
                
                return filepath
                
            except Exception as e:
                print(f"[Error] Failed to decode base64 image: {e}")
                return None
                
        elif href.startswith('http://') or href.startswith('https://'):
            # Handle external URLs
            filename = f"raster_{image_index:03d}_external_url.txt"
            filepath = os.path.join(raster_folder, filename)
            
            with open(filepath, 'w') as f:
                f.write(f"External image URL: {href}\n")
                f.write("Element attributes:\n")
                for key, value in element.attrib.items():
                    f.write(f"  {key}: {value}\n")
            
            print(f"[Info] External URL saved as reference: {filepath}")
            return filepath
            
        else:
            # Handle relative file paths
            filename = f"raster_{image_index:03d}_file_reference.txt"
            filepath = os.path.join(raster_folder, filename)
            
            with open(filepath, 'w') as f:
                f.write(f"File reference: {href}\n")
                f.write("Element attributes:\n")
                for key, value in element.attrib.items():
                    f.write(f"  {key}: {value}\n")
            
            return filepath
            
    except Exception as e:
        print(f"[Error] Failed to save raster element: {e}")
        return None


if __name__ == "__main__":
    # Convert CDR to both SVG and PDF
    pdf_file = cdr_to_pdf("test.cdr", "output.pdf")
    
    # Extract the SVG path (it's created alongside the PDF)
    svg_file = os.path.join(
        os.path.dirname(pdf_file),
        os.path.splitext(os.path.basename("test.cdr"))[0] + ".svg"
    )
    
    # Remove raster components from SVG, keeping only vectors
    vectors_svg = remove_raster_from_svg(svg_file)
    
    # Remove colors from the vector-only SVG, keeping only outlines
    outlines_svg = remove_colors_from_svg(vectors_svg)
    
    # Create black and white version of the vector SVG
    bw_svg = create_black_white_svg(vectors_svg)
    
    print(f"\n=== DECOMPOSITION COMPLETE ===")
    print(f"Original SVG (with rasters): {svg_file}")
    print(f"Vector-only SVG: {vectors_svg}")
    print(f"Outline-only SVG (fold lines & shapes): {outlines_svg}")
    print(f"Black/White SVG: {bw_svg}")
    print(f"PDF file: {pdf_file}")