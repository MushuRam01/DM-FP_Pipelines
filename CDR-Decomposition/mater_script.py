# %% [markdown]
# # CDR Decomposition Workflow
# 
# This notebook organizes the complete workflow for converting and decomposing CorelDRAW (CDR) files into various formats for analysis and reconstruction.
# 
# ## Overview
# The workflow consists of:
# 1. **CDR to SVG Conversion** - Using LibreOffice Draw
# 2. **Raster Removal** - Extract bitmap images, keep vectors only
# 3. **Color Extraction** - Remove fills, preserve outlines  
# 4. **Greyscale Conversion** - Convert to greyscale variants
# 5. **Color Inversion** - Create inverted color schemes
# 
# Let's start with the basic CDR to SVG conversion.

# %% [markdown]
# ## 1. Setup and Import Libraries
# 
# First, let's import all the required libraries for our CDR decomposition workflow.

# %%
# Import required libraries for CDR processing
import os
import shutil
import subprocess
import xml.etree.ElementTree as ET
import base64
import json
import re
from urllib.parse import urlparse

print("✅ All required libraries imported successfully!")
print("📁 Current working directory:", os.getcwd())

# Check if LibreOffice is available (required for CDR conversion)
libreoffice_path = shutil.which("libreoffice")
if libreoffice_path:
    print(f"✅ LibreOffice found at: {libreoffice_path}")
else:
    print("❌ LibreOffice not found. Install with: sudo apt install libreoffice")

# %% [markdown]
# ## 2. Define CDR to SVG Conversion Function
# 
# This function uses LibreOffice Draw in headless mode to convert CDR files to SVG format, preserving all vector graphics.

# %%
def cdr_to_svg(cdr_path: str, output_dir: str = None) -> str:
    """
    Convert a CorelDRAW .cdr file to SVG using LibreOffice Draw.
    
    Args:
        cdr_path: Path to the input CDR file
        output_dir: Directory for output (defaults to same as input)
    
    Returns:
        Path to the generated SVG file
        
    Raises:
        FileNotFoundError: If input file doesn't exist
        RuntimeError: If LibreOffice conversion fails
    """
    cdr_path = os.path.abspath(cdr_path)
    
    # Validate input file
    if not os.path.exists(cdr_path):
        raise FileNotFoundError(f"CDR file not found: {cdr_path}")
    
    # Set output directory
    if output_dir is None:
        output_dir = os.path.dirname(cdr_path)
    
    # Check LibreOffice availability
    libreoffice = shutil.which("libreoffice")
    if libreoffice is None:
        raise RuntimeError("LibreOffice not found. Install with: sudo apt install libreoffice")
    
    print(f"🔄 Converting CDR to SVG...")
    print(f"📁 Input:  {cdr_path}")
    print(f"📁 Output: {output_dir}")
    
    # Execute LibreOffice conversion
    cmd = [
        libreoffice,
        "--headless",
        "--convert-to", "svg",
        "--outdir", output_dir,
        cdr_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    # Check if conversion succeeded
    expected_svg = os.path.join(
        output_dir,
        os.path.splitext(os.path.basename(cdr_path))[0] + ".svg"
    )
    
    if result.returncode != 0 or not os.path.exists(expected_svg):
        print(f"❌ Conversion failed!")
        print(f"Command: {' '.join(cmd)}")
        print(f"Error: {result.stderr}")
        raise RuntimeError(f"LibreOffice failed to convert CDR to SVG")
    
    print(f"✅ Conversion successful!")
    print(f"📄 SVG file created: {expected_svg}")
    
    return expected_svg

# Test the function definition
print("✅ CDR to SVG conversion function defined successfully!")

# %% [markdown]
# ## 3. Convert Your CDR File to SVG
# 
# Now let's use the function to convert your CDR file. Make sure you have a CDR file in your workspace.

# %%
# Convert your CDR file to SVG
# Update the file path to match your CDR file
cdr_file = "test.cdr"  # Change this to your CDR file name

try:
    # Check if the CDR file exists
    if os.path.exists(cdr_file):
        print(f"📁 Found CDR file: {cdr_file}")
        
        # Perform the conversion
        svg_file = cdr_to_svg(cdr_file)
        
        # Store the SVG path for use in next steps
        original_svg = svg_file
        
        print(f"\n🎉 Conversion completed successfully!")
        print(f"📄 Original SVG: {original_svg}")
        
    else:
        print(f"❌ CDR file '{cdr_file}' not found in current directory.")
        print("Available files:")
        for file in os.listdir():
            if file.endswith(('.cdr', '.svg')):
                print(f"  📄 {file}")
                
except Exception as e:
    print(f"❌ Error during conversion: {e}")
    print("Make sure LibreOffice is installed and the CDR file is valid.")

# %% [markdown]
# ## 4. Verify Conversion Results
# 
# Let's examine the SVG file that was created to understand its structure and content.

# %%
# Verify the SVG conversion results
try:
    if 'original_svg' in globals() and os.path.exists(original_svg):
        print("📊 SVG File Analysis")
        print("=" * 50)
        
        # File size information
        file_size = os.path.getsize(original_svg)
        print(f"📄 File: {os.path.basename(original_svg)}")
        print(f"📁 Path: {original_svg}")
        print(f"💾 Size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        
        # Parse SVG to analyze structure
        tree = ET.parse(original_svg)
        root = tree.getroot()
        
        print(f"🏷️  Root tag: {root.tag}")
        print(f"📐 Dimensions: {root.get('width', 'auto')} x {root.get('height', 'auto')}")
        
        # Count different element types
        element_counts = {}
        total_elements = 0
        
        for elem in root.iter():
            # Clean tag name (remove namespace)
            tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            element_counts[tag_name] = element_counts.get(tag_name, 0) + 1
            total_elements += 1
        
        print(f"🔢 Total elements: {total_elements}")
        print("\n📋 Element breakdown:")
        for tag, count in sorted(element_counts.items()):
            if count > 1:
                print(f"  {tag}: {count}")
        
        # Look for colors
        colors_found = set()
        for elem in root.iter():
            fill = elem.get('fill')
            stroke = elem.get('stroke')
            if fill and fill != 'none':
                colors_found.add(fill)
            if stroke and stroke != 'none':
                colors_found.add(stroke)
        
        print(f"\n🎨 Colors found: {len(colors_found)}")
        if colors_found and len(colors_found) <= 10:
            for color in sorted(colors_found):
                print(f"  {color}")
        elif len(colors_found) > 10:
            print(f"  (Too many to display - first 5)")
            for color in list(sorted(colors_found))[:5]:
                print(f"  {color}")
        
        print(f"\n✅ SVG file is ready for further processing!")
        
    else:
        print("❌ No SVG file found. Please run the conversion step first.")
        
except Exception as e:
    print(f"❌ Error analyzing SVG: {e}")
    print("The SVG file might be corrupted or in an unexpected format.")

# %% [markdown]
# ## 5. Remove Raster Images from SVG
# 
# Now we'll extract any raster/bitmap images from the SVG and keep only the vector elements. This creates a clean vector-only version while saving extracted images for later use.

# %%
def remove_raster_from_svg(svg_path: str, output_svg_path: str = None, save_rasters: bool = True) -> str:
    """
    Remove all raster components from an SVG file, keeping only vector elements.
    
    Args:
        svg_path: Path to the input SVG file
        output_svg_path: Path for the cleaned SVG (defaults to input_vectors.svg)
        save_rasters: Whether to save extracted raster images (default: True)
    
    Returns:
        Path to the cleaned SVG file
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
        print(f"📁 Raster extraction folder: {raster_folder}")
    
    print(f"🔄 Removing raster elements from SVG...")
    
    try:
        # Parse the SVG file
        tree = ET.parse(svg_path)
        root = tree.getroot()
        
        # Counter for removed elements
        removed_count = 0
        saved_count = 0
        
        # Find all elements to remove
        elements_to_remove = []
        
        for elem in root.iter():
            # Check if element is an image tag
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
                    print(f"💾 Saved raster: {os.path.basename(saved_file)}")
            
            # Find the parent and remove the element
            for parent in root.iter():
                if elem_to_remove in list(parent):
                    parent.remove(elem_to_remove)
                    removed_count += 1
                    print(f"🗑️  Removed {removal_type}: {elem_to_remove.tag}")
                    break
        
        print(f"✅ Removed {removed_count} raster elements")
        if save_rasters:
            print(f"💾 Saved {saved_count} raster images")
        
        # Write the cleaned SVG
        tree.write(output_svg_path, encoding='utf-8', xml_declaration=True)
        
        print(f"📄 Vector-only SVG saved to: {output_svg_path}")
        return output_svg_path
        
    except ET.ParseError as e:
        raise RuntimeError(f"Failed to parse SVG file: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to process SVG file: {e}")


def _save_raster_element(element, raster_folder: str, image_index: int) -> str:
    """Save a raster element (image) from SVG to a file."""
    try:
        # Get image data from href attributes
        href = element.get('href') or element.get('{http://www.w3.org/1999/xlink}href')
        
        if not href:
            print(f"⚠️  No href found in image element")
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
                
                # Save metadata
                metadata_file = os.path.join(raster_folder, f"raster_{image_index:03d}_metadata.txt")
                with open(metadata_file, 'w') as f:
                    f.write(f"MIME type: {mime_part}\n")
                    f.write(f"File size: {len(image_data)} bytes\n")
                    f.write("Element attributes:\n")
                    for key, value in element.attrib.items():
                        if not key.endswith('href'):  # Skip the long data URL
                            f.write(f"  {key}: {value}\n")
                
                return filepath
                
            except Exception as e:
                print(f"❌ Failed to decode base64 image: {e}")
                return None
                
        else:
            # Handle file references or external URLs
            filename = f"raster_{image_index:03d}_reference.txt"
            filepath = os.path.join(raster_folder, filename)
            
            with open(filepath, 'w') as f:
                f.write(f"Image reference: {href}\n")
                f.write("Element attributes:\n")
                for key, value in element.attrib.items():
                    f.write(f"  {key}: {value}\n")
            
            return filepath
            
    except Exception as e:
        print(f"❌ Failed to save raster element: {e}")
        return None

print("✅ Raster removal functions defined successfully!")

# %%
# Remove raster images from the SVG
try:
    if 'original_svg' in globals() and os.path.exists(original_svg):
        print(f"🔄 Processing: {os.path.basename(original_svg)}")
        
        # Remove raster images and create vector-only version
        vectors_svg = remove_raster_from_svg(original_svg, save_rasters=True)
        
        print(f"\n📊 Raster Removal Results")
        print("=" * 50)
        
        # Compare file sizes
        original_size = os.path.getsize(original_svg)
        vectors_size = os.path.getsize(vectors_svg)
        size_reduction = original_size - vectors_size
        
        print(f"📄 Original SVG: {original_size:,} bytes ({original_size/1024:.1f} KB)")
        print(f"📄 Vector-only SVG: {vectors_size:,} bytes ({vectors_size/1024:.1f} KB)")
        print(f"💾 Size reduction: {size_reduction:,} bytes ({size_reduction/1024:.1f} KB)")
        
        # Check what was removed
        if size_reduction > 1000:  # More than 1KB reduction
            print(f"🎉 Significant raster content removed!")
        elif size_reduction > 0:
            print(f"✅ Some raster content removed")
        else:
            print(f"ℹ️  No raster images found in SVG")
        
        # Store for next steps
        vectors_only_svg = vectors_svg
        
        print(f"\n✅ Vector-only SVG ready: {os.path.basename(vectors_svg)}")
        
    else:
        print("❌ No original SVG found. Please run the CDR conversion first.")
        
except Exception as e:
    print(f"❌ Error during raster removal: {e}")
    print("The SVG might have an unexpected structure or be corrupted.")

# %% [markdown]
# ## 6. Convert SVG to Greyscale
# 
# Now we'll convert the vector-only SVG to greyscale using proper luminance calculations for natural-looking results.

# %%
def convert_svg_to_greyscale(svg_path: str, output_svg_path: str = None, black_threshold: int = 50, white_threshold: int = 200) -> str:
    """
    Convert all colors in an SVG to greyscale values using luminance calculation.
    Colors close to black are converted to perfect black for die-line isolation.
    Colors close to white are converted to perfect white for background isolation.
    
    Args:
        svg_path: Path to the input SVG file
        output_svg_path: Path for the greyscale SVG (defaults to input_greyscale.svg)
        black_threshold: Luminance threshold below which colors become pure black (0-255)
        white_threshold: Luminance threshold above which colors become pure white (0-255)
    
    Returns:
        Path to the greyscale SVG file
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
    
    print(f"🔄 Converting colors to greyscale (black ≤ {black_threshold}, white ≥ {white_threshold})...")
    
    try:
        # Parse the SVG file
        tree = ET.parse(svg_path)
        root = tree.getroot()
        
        converted_count = 0
        black_count = 0
        white_count = 0
        
        # Process gradients in defs first
        defs_elements = root.findall(".//{http://www.w3.org/2000/svg}defs") + root.findall(".//defs")
        for defs in defs_elements:
            for child in defs:
                if child.tag.endswith('linearGradient') or child.tag.endswith('radialGradient'):
                    result = _convert_gradient_to_greyscale(child, black_threshold, white_threshold)
                    converted_count += result[0]
                    black_count += result[1]
                    white_count += result[2]
        
        # Process all elements
        for elem in root.iter():
            result = _convert_element_colors_to_greyscale(elem, black_threshold, white_threshold)
            if result[0]:  # If any changes were made
                converted_count += 1
            black_count += result[1]
            white_count += result[2]
        
        print(f"✅ Converted {converted_count} elements to greyscale")
        print(f"🖤 Converted {black_count} colors to pure black (die-lines)")
        print(f"🤍 Converted {white_count} colors to pure white (backgrounds)")
        
        # Write the greyscale SVG
        tree.write(output_svg_path, encoding='utf-8', xml_declaration=True)
        
        print(f"📄 Greyscale SVG saved to: {output_svg_path}")
        return output_svg_path
        
    except ET.ParseError as e:
        raise RuntimeError(f"Failed to parse SVG file: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to process SVG file: {e}")


def _color_to_greyscale(color_value: str, black_threshold: int = 50, white_threshold: int = 200) -> tuple:
    """
    Convert a color value to its greyscale equivalent using luminance.
    Colors close to black are converted to perfect black for die-line isolation.
    Colors close to white are converted to perfect white for background isolation.
    
    Returns: (converted_color, was_converted_to_black, was_converted_to_white)
    """
    if not color_value or color_value in ['none', 'transparent', 'inherit', 'currentColor']:
        return color_value, False, False
    
    # Already greyscale (pure grays)
    if _is_greyscale_color(color_value):
        # Check if already grey but should be black or white
        if color_value.startswith('#'):
            hex_color = color_value[1:]
            if len(hex_color) == 6:
                grey_val = int(hex_color[0:2], 16)
                if grey_val <= black_threshold and grey_val > 0:
                    return '#000000', True, False
                elif grey_val >= white_threshold and grey_val < 255:
                    return '#ffffff', False, True
        return color_value, False, False
    
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
                    # Check thresholds
                    if luminance <= black_threshold:
                        return f"rgba(0, 0, 0, {a})", True, False
                    elif luminance >= white_threshold:
                        return f"rgba(255, 255, 255, {a})", False, True
                    # Keep alpha channel with grey value
                    grey_value = int(round(luminance))
                    return f"rgba({grey_value}, {grey_value}, {grey_value}, {a})", False, False
        
        elif color_value.lower() in _get_named_color_values():
            # Named colors
            r, g, b = _get_named_color_values()[color_value.lower()]
            luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
        
        # Check thresholds for black and white conversion
        if luminance <= black_threshold:
            return '#000000', True, False
        elif luminance >= white_threshold:
            return '#ffffff', False, True
        
        # Convert luminance to greyscale hex
        grey_value = int(round(min(255, max(0, luminance))))
        return f"#{grey_value:02x}{grey_value:02x}{grey_value:02x}", False, False
        
    except Exception as e:
        print(f"⚠️  Could not convert color '{color_value}' to greyscale: {e}")
        # Fallback to medium gray
        return "#808080", False, False


def _is_greyscale_color(color_value: str) -> bool:
    """Check if a color is already greyscale."""
    try:
        if color_value.startswith('#'):
            hex_color = color_value[1:]
            if len(hex_color) == 3:
                return hex_color[0] == hex_color[1] == hex_color[2]
            elif len(hex_color) == 6:
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
        'red': (255, 0, 0), 'green': (0, 128, 0), 'blue': (0, 0, 255),
        'yellow': (255, 255, 0), 'cyan': (0, 255, 255), 'magenta': (255, 0, 255),
        'orange': (255, 165, 0), 'purple': (128, 0, 128), 'pink': (255, 192, 203),
        'brown': (165, 42, 42), 'black': (0, 0, 0), 'white': (255, 255, 255),
        'gray': (128, 128, 128), 'grey': (128, 128, 128), 'lime': (0, 255, 0),
        'navy': (0, 0, 128), 'olive': (128, 128, 0), 'maroon': (128, 0, 0),
        'teal': (0, 128, 128), 'silver': (192, 192, 192), 'gold': (255, 215, 0)
    }


def _convert_element_colors_to_greyscale(element, black_threshold: int = 50, white_threshold: int = 200) -> tuple:
    """
    Convert all colors in an element to greyscale. 
    Returns: (changed, black_count, white_count)
    """
    changed = False
    black_count = 0
    white_count = 0
    
    # Convert fill
    fill = element.get('fill')
    if fill:
        new_fill, was_black, was_white = _color_to_greyscale(fill, black_threshold, white_threshold)
        if new_fill != fill:
            element.set('fill', new_fill)
            changed = True
            if was_black:
                black_count += 1
            elif was_white:
                white_count += 1
    
    # Convert stroke
    stroke = element.get('stroke')
    if stroke:
        new_stroke, was_black, was_white = _color_to_greyscale(stroke, black_threshold, white_threshold)
        if new_stroke != stroke:
            element.set('stroke', new_stroke)
            changed = True
            if was_black:
                black_count += 1
            elif was_white:
                white_count += 1
    
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
                    new_value, was_black, was_white = _color_to_greyscale(value, black_threshold, white_threshold)
                    new_style_parts.append(f"{key}: {new_value}")
                    if new_value != value:
                        changed = True
                        if was_black:
                            black_count += 1
                        elif was_white:
                            white_count += 1
                else:
                    new_style_parts.append(prop)
            else:
                new_style_parts.append(prop)
        
        if changed:
            element.set('style', '; '.join(new_style_parts))
    
    # Convert stop-color for gradient stops
    stop_color = element.get('stop-color')
    if stop_color:
        new_stop_color, was_black, was_white = _color_to_greyscale(stop_color, black_threshold, white_threshold)
        if new_stop_color != stop_color:
            element.set('stop-color', new_stop_color)
            changed = True
            if was_black:
                black_count += 1
            elif was_white:
                white_count += 1
    
    return changed, black_count, white_count


def _convert_gradient_to_greyscale(gradient_elem, black_threshold: int = 50, white_threshold: int = 200) -> tuple:
    """
    Convert all colors in a gradient to greyscale.
    Returns: (converted_count, black_count, white_count)
    """
    converted_count = 0
    black_count = 0
    white_count = 0
    
    for stop in gradient_elem.findall(".//{http://www.w3.org/2000/svg}stop") + gradient_elem.findall(".//stop"):
        result = _convert_element_colors_to_greyscale(stop, black_threshold, white_threshold)
        if result[0]:
            converted_count += 1
        black_count += result[1]
        white_count += result[2]
    
    return converted_count, black_count, white_count

print("✅ Die-line and background optimized greyscale conversion functions defined successfully!")

# %%
# Convert the vector-only SVG to greyscale with die-line and background isolation
try:
    if 'vectors_only_svg' in globals() and os.path.exists(vectors_only_svg):
        print(f"🔄 Processing: {os.path.basename(vectors_only_svg)}")
        
        # Set thresholds for die-line and background detection (adjust as needed)
        BLACK_THRESHOLD = 50   # Colors with luminance ≤ 50 become pure black
        WHITE_THRESHOLD = 200  # Colors with luminance ≥ 200 become pure white
        print(f"🎯 Black threshold: {BLACK_THRESHOLD} (die-line isolation)")
        print(f"🎯 White threshold: {WHITE_THRESHOLD} (background isolation)")
        
        # Convert to greyscale with die-line and background optimization
        greyscale_svg = convert_svg_to_greyscale(vectors_only_svg, 
                                                black_threshold=BLACK_THRESHOLD, 
                                                white_threshold=WHITE_THRESHOLD)
        
        print(f"\n📊 Optimized Greyscale Results")
        print("=" * 50)
        
        # Analyze what was converted
        tree = ET.parse(greyscale_svg)
        root = tree.getroot()
        
        # Count colors by type
        black_colors = 0
        white_colors = 0
        grey_colors = set()
        total_color_attrs = 0
        
        for elem in root.iter():
            fill = elem.get('fill')
            stroke = elem.get('stroke')
            
            if fill and fill != 'none':
                total_color_attrs += 1
                if fill in ['#000000', '#000', 'black']:
                    black_colors += 1
                elif fill in ['#ffffff', '#fff', 'white']:
                    white_colors += 1
                else:
                    grey_colors.add(fill)
                    
            if stroke and stroke != 'none':
                total_color_attrs += 1
                if stroke in ['#000000', '#000', 'black']:
                    black_colors += 1
                elif stroke in ['#ffffff', '#fff', 'white']:
                    white_colors += 1
                else:
                    grey_colors.add(stroke)
        
        print(f"🎨 Total color attributes: {total_color_attrs}")
        print(f"🖤 Pure black elements (die-lines): {black_colors}")
        print(f"🤍 Pure white elements (backgrounds): {white_colors}")
        print(f"🔘 Unique grey shades: {len(grey_colors)}")
        
        # Calculate percentages
        if total_color_attrs > 0:
            die_line_percentage = (black_colors / total_color_attrs) * 100
            background_percentage = (white_colors / total_color_attrs) * 100
            grey_percentage = (len(grey_colors) / total_color_attrs) * 100 if grey_colors else 0
            
            print(f"📊 Die-line coverage: {die_line_percentage:.1f}%")
            print(f"📊 Background coverage: {background_percentage:.1f}%")
            print(f"📊 Detailed grey coverage: {grey_percentage:.1f}%")
        
        # Show sample of grey colors found
        if grey_colors:
            print(f"\n🎯 Sample greyscale colors (detailed elements):")
            for i, color in enumerate(sorted(grey_colors)[:6]):  # Show first 6
                print(f"  {color}")
            if len(grey_colors) > 6:
                print(f"  ... and {len(grey_colors) - 6} more shades")
        
        # File size comparison
        original_size = os.path.getsize(vectors_only_svg)
        grey_size = os.path.getsize(greyscale_svg)
        
        print(f"\n📄 Vector SVG: {original_size:,} bytes")
        print(f"📄 Greyscale SVG: {grey_size:,} bytes")
        
        if grey_size < original_size:
            reduction = original_size - grey_size
            print(f"💾 Size reduction: {reduction} bytes (color simplification)")
        
        print(f"\n✅ Dual-threshold greyscale conversion complete!")
        print(f"📁 Output: {os.path.basename(greyscale_svg)}")
        print(f"🎯 Die-lines: pure black (#000000) | Backgrounds: pure white (#ffffff)")
        
        # Store for potential further processing
        optimized_greyscale_svg = greyscale_svg
        
    else:
        print("❌ No vector-only SVG found. Please run the raster removal step first.")
        
except Exception as e:
    print(f"❌ Error during greyscale conversion: {e}")
    print("The SVG might contain unsupported color formats.")

# %% [markdown]
# ## 7. Invert Greyscale Colors
# 
# Now we'll create an inverted version of the greyscale SVG - useful for negative views, alternative visualizations, or design validation.

# %%
def invert_svg_colors(svg_path: str, output_svg_path: str = None) -> str:
    """
    Invert all colors in an SVG file - black becomes white, white becomes black, etc.
    
    Args:
        svg_path: Path to the input SVG file
        output_svg_path: Path for the inverted SVG (defaults to input_inverted.svg)
    
    Returns:
        Path to the inverted SVG file
    """
    svg_path = os.path.abspath(svg_path)
    
    if not os.path.exists(svg_path):
        raise FileNotFoundError(f"SVG file not found: {svg_path}")
    
    if output_svg_path is None:
        base_name = os.path.splitext(os.path.basename(svg_path))[0]
        output_svg_path = os.path.join(
            os.path.dirname(svg_path),
            f"{base_name}_inverted.svg"
        )
    
    output_svg_path = os.path.abspath(output_svg_path)
    
    print(f"🔄 Inverting colors in SVG...")
    
    try:
        # Parse the SVG file
        tree = ET.parse(svg_path)
        root = tree.getroot()
        
        inverted_count = 0
        
        # Process gradients in defs first
        defs_elements = root.findall(".//{http://www.w3.org/2000/svg}defs") + root.findall(".//defs")
        for defs in defs_elements:
            for child in defs:
                if child.tag.endswith('linearGradient') or child.tag.endswith('radialGradient'):
                    if _invert_gradient_colors(child):
                        inverted_count += 1
        
        # Process all elements
        for elem in root.iter():
            if _invert_element_colors(elem):
                inverted_count += 1
        
        print(f"✅ Inverted colors in {inverted_count} elements")
        
        # Write the inverted SVG
        tree.write(output_svg_path, encoding='utf-8', xml_declaration=True)
        
        print(f"📄 Inverted SVG saved to: {output_svg_path}")
        return output_svg_path
        
    except ET.ParseError as e:
        raise RuntimeError(f"Failed to parse SVG file: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to process SVG file: {e}")


def _invert_hex_color(hex_color: str) -> str:
    """Convert hex color to its inverse."""
    if not hex_color or hex_color in ['none', 'transparent', 'inherit', 'currentColor']:
        return hex_color
    
    try:
        # Remove the # symbol
        hex_color = hex_color.replace('#', '')
        
        # Handle 3-digit hex
        if len(hex_color) == 3:
            hex_color = ''.join([c*2 for c in hex_color])  # Convert #RGB to #RRGGBB
        
        if len(hex_color) == 6:
            # Convert each pair of hex digits to decimal, invert, convert back to hex
            r = 255 - int(hex_color[0:2], 16)
            g = 255 - int(hex_color[2:4], 16) 
            b = 255 - int(hex_color[4:6], 16)
            
            # Format back to hex with leading zeros
            return f"#{r:02x}{g:02x}{b:02x}"
        
        return hex_color  # Return unchanged if invalid format
        
    except Exception as e:
        print(f"⚠️  Could not invert color '{hex_color}': {e}")
        return hex_color


def _invert_rgb_color(rgb_color: str) -> str:
    """Convert RGB color to its inverse."""
    try:
        # Parse rgb(r, g, b) format
        rgb_match = re.search(r'rgb\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)', rgb_color)
        if rgb_match:
            r, g, b = map(int, rgb_match.groups())
            return f"rgb({255-r}, {255-g}, {255-b})"
        
        # Parse rgba(r, g, b, a) format
        rgba_match = re.search(r'rgba\s*\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([0-9.]+)\s*\)', rgb_color)
        if rgba_match:
            r, g, b, a = map(float, rgba_match.groups())
            return f"rgba({255-int(r)}, {255-int(g)}, {255-int(b)}, {a})"
        
        return rgb_color  # Return unchanged if no match
        
    except Exception as e:
        print(f"⚠️  Could not invert RGB color '{rgb_color}': {e}")
        return rgb_color


def _invert_named_color(color_name: str) -> str:
    """Convert named colors to their inverted equivalents."""
    inversions = {
        'black': 'white',
        'white': 'black',
        'red': 'cyan',
        'green': 'magenta', 
        'blue': 'yellow',
        'cyan': 'red',
        'magenta': 'green',
        'yellow': 'blue',
        'gray': 'gray',  # Gray inverts to itself (128 -> 127, close enough)
        'grey': 'grey'
    }
    
    return inversions.get(color_name.lower(), color_name)


def _invert_color(color_value: str) -> str:
    """Invert any color format to its opposite."""
    if not color_value or color_value in ['none', 'transparent', 'inherit', 'currentColor']:
        return color_value
    
    # Handle hex colors
    if color_value.startswith('#'):
        return _invert_hex_color(color_value)
    
    # Handle rgb/rgba colors
    elif color_value.startswith('rgb'):
        return _invert_rgb_color(color_value)
    
    # Handle named colors
    elif color_value.lower() in ['black', 'white', 'red', 'green', 'blue', 'cyan', 'magenta', 'yellow', 'gray', 'grey']:
        return _invert_named_color(color_value)
    
    # For other named colors, try to convert to hex first, then invert
    else:
        named_colors = _get_named_color_values()
        if color_value.lower() in named_colors:
            r, g, b = named_colors[color_value.lower()]
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            return _invert_hex_color(hex_color)
    
    return color_value  # Return unchanged if unable to process


def _invert_element_colors(element) -> bool:
    """Invert all colors in an element. Returns True if any changes made."""
    changed = False
    
    # Invert fill
    fill = element.get('fill')
    if fill:
        new_fill = _invert_color(fill)
        if new_fill != fill:
            element.set('fill', new_fill)
            changed = True
    
    # Invert stroke
    stroke = element.get('stroke')
    if stroke:
        new_stroke = _invert_color(stroke)
        if new_stroke != stroke:
            element.set('stroke', new_stroke)
            changed = True
    
    # Invert style attribute
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
                    new_value = _invert_color(value)
                    new_style_parts.append(f"{key}: {new_value}")
                    if new_value != value:
                        changed = True
                else:
                    new_style_parts.append(prop)
            else:
                new_style_parts.append(prop)
        
        if changed:
            element.set('style', '; '.join(new_style_parts))
    
    # Invert stop-color for gradient stops
    stop_color = element.get('stop-color')
    if stop_color:
        new_stop_color = _invert_color(stop_color)
        if new_stop_color != stop_color:
            element.set('stop-color', new_stop_color)
            changed = True
    
    # Invert color attribute (for text elements)
    color = element.get('color')
    if color:
        new_color = _invert_color(color)
        if new_color != color:
            element.set('color', new_color)
            changed = True
    
    return changed


def _invert_gradient_colors(gradient_elem) -> bool:
    """Invert all colors in a gradient. Returns True if any changes made."""
    changed = False
    
    for stop in gradient_elem.findall(".//{http://www.w3.org/2000/svg}stop") + gradient_elem.findall(".//stop"):
        if _invert_element_colors(stop):
            changed = True
    
    return changed

print("✅ Color inversion functions defined successfully!")

# %%
# Invert the greyscale SVG colors
try:
    if 'optimized_greyscale_svg' in globals() and os.path.exists(optimized_greyscale_svg):
        print(f"🔄 Processing: {os.path.basename(optimized_greyscale_svg)}")
        
        # Create inverted version
        inverted_svg = invert_svg_colors(optimized_greyscale_svg)
        
        print(f"\n📊 Color Inversion Results")
        print("=" * 50)
        
        # Analyze the inverted colors
        tree = ET.parse(inverted_svg)
        root = tree.getroot()
        
        # Count inverted colors
        inverted_colors = set()
        total_color_attrs = 0
        
        for elem in root.iter():
            fill = elem.get('fill')
            stroke = elem.get('stroke')
            
            if fill and fill != 'none':
                inverted_colors.add(fill)
                total_color_attrs += 1
                
            if stroke and stroke != 'none':
                inverted_colors.add(stroke)
                total_color_attrs += 1
        
        print(f"🎨 Total color attributes: {total_color_attrs}")
        print(f"🔄 Unique inverted colors: {len(inverted_colors)}")
        
        # Show sample of inverted colors
        if inverted_colors:
            print(f"\n🎯 Sample inverted colors:")
            for i, color in enumerate(sorted(inverted_colors)[:8]):  # Show first 8
                print(f"  {color}")
            if len(inverted_colors) > 8:
                print(f"  ... and {len(inverted_colors) - 8} more colors")
        
        # File size comparison
        original_size = os.path.getsize(optimized_greyscale_svg)
        inverted_size = os.path.getsize(inverted_svg)
        
        print(f"\n📄 Greyscale SVG: {original_size:,} bytes")
        print(f"📄 Inverted SVG: {inverted_size:,} bytes")
        
        if inverted_size != original_size:
            diff = abs(inverted_size - original_size)
            direction = "increase" if inverted_size > original_size else "decrease"
            print(f"📊 Size {direction}: {diff} bytes")
        else:
            print(f"📊 Same file size (perfect inversion)")
        
        # Show color transformations
        print(f"\n🔄 Color Transformations:")
        print(f"  • Black (#000000) → White (#ffffff)")
        print(f"  • White (#ffffff) → Black (#000000)")
        print(f"  • Light greys → Dark greys")
        print(f"  • Dark greys → Light greys")
        
        print(f"\n✅ Color inversion complete!")
        print(f"📁 Output: {os.path.basename(inverted_svg)}")
        print(f"🎯 Perfect for negative views and design validation")
        
        # Store for potential further processing
        inverted_colors_svg = inverted_svg
        
    else:
        print("❌ No greyscale SVG found. Please run the greyscale conversion step first.")
        
except Exception as e:
    print(f"❌ Error during color inversion: {e}")
    print("The SVG might contain unsupported color formats or be corrupted.")

# %% [markdown]
# ## 8. Extract Perfect Black-White Bijection Elements
# 
# Now we'll compare the greyscale and inverted SVGs to find elements that perfectly transition from black to white (or white to black). These represent the purest die-line elements with perfect contrast inversion.

# %%
def extract_bijection_bw_elements(greyscale_svg_path: str, inverted_svg_path: str, output_svg_path: str = None) -> str:
    """
    Compare greyscale and inverted SVGs to extract only elements that have perfect 
    black-to-white or white-to-black bijection. These represent the purest die-line elements.
    
    Args:
        greyscale_svg_path: Path to the greyscale SVG file
        inverted_svg_path: Path to the inverted SVG file  
        output_svg_path: Path for the bijection SVG (defaults to input_bijectionBW.svg)
    
    Returns:
        Path to the bijection SVG file containing only perfect BW transition elements
    """
    if not os.path.exists(greyscale_svg_path):
        raise FileNotFoundError(f"Greyscale SVG not found: {greyscale_svg_path}")
    
    if not os.path.exists(inverted_svg_path):
        raise FileNotFoundError(f"Inverted SVG not found: {inverted_svg_path}")
    
    if output_svg_path is None:
        base_name = os.path.splitext(os.path.basename(greyscale_svg_path))[0]
        # Remove any existing suffixes like _greyscale
        base_name = base_name.replace('_greyscale', '').replace('_vectors', '')
        output_svg_path = os.path.join(
            os.path.dirname(greyscale_svg_path),
            f"{base_name}_bijectionBW.svg"
        )
    
    output_svg_path = os.path.abspath(output_svg_path)
    
    print(f"🔄 Analyzing perfect black-white bijection elements...")
    print(f"📄 Greyscale: {os.path.basename(greyscale_svg_path)}")
    print(f"📄 Inverted:  {os.path.basename(inverted_svg_path)}")
    
    try:
        # Parse both SVG files
        grey_tree = ET.parse(greyscale_svg_path)
        grey_root = grey_tree.getroot()
        
        inv_tree = ET.parse(inverted_svg_path)
        inv_root = inv_tree.getroot()
        
        # Create a new SVG with the same structure as greyscale
        bijection_tree = ET.parse(greyscale_svg_path)  # Start with greyscale as base
        bijection_root = bijection_tree.getroot()
        
        # Track statistics
        total_elements = 0
        perfect_bijection_elements = 0
        black_to_white_count = 0
        white_to_black_count = 0
        removed_elements = []
        
        # Create mappings of elements by their unique identifiers
        grey_elements = _build_element_map(grey_root)
        inv_elements = _build_element_map(inv_root)
        
        print(f"🔍 Found {len(grey_elements)} elements in greyscale SVG")
        print(f"🔍 Found {len(inv_elements)} elements in inverted SVG")
        
        # Process all elements in the bijection tree
        for elem in list(bijection_root.iter()):
            total_elements += 1
            
            # Get element's position/path for matching
            elem_key = _get_element_key(elem)
            
            # Skip root and non-graphics elements
            if elem == bijection_root or not _is_graphics_element(elem):
                continue
                
            # Find corresponding elements in both source files
            grey_elem = grey_elements.get(elem_key)
            inv_elem = inv_elements.get(elem_key)
            
            if grey_elem is None or inv_elem is None:
                # Element not found in one of the files, remove it
                removed_elements.append(elem)
                continue
            
            # Check if this element has perfect bijection
            bijection_result = _check_perfect_bijection(grey_elem, inv_elem)
            
            if bijection_result['has_bijection']:
                perfect_bijection_elements += 1
                if bijection_result['black_to_white']:
                    black_to_white_count += 1
                if bijection_result['white_to_black']:
                    white_to_black_count += 1
                    
                # Keep the element (it's already in bijection_tree)
                pass
            else:
                # No perfect bijection, mark for removal
                removed_elements.append(elem)
        
        # Remove elements that don't have perfect bijection
        for elem in removed_elements:
            parent = _find_parent(bijection_root, elem)
            if parent is not None:
                parent.remove(elem)
        
        print(f"✅ Analysis complete!")
        print(f"🔢 Total elements analyzed: {total_elements}")
        print(f"🎯 Perfect bijection elements: {perfect_bijection_elements}")
        print(f"⚫→⚪ Black-to-white transitions: {black_to_white_count}")
        print(f"⚪→⚫ White-to-black transitions: {white_to_black_count}")
        print(f"🗑️  Elements removed: {len(removed_elements)}")
        
        # Calculate retention percentage
        if total_elements > 0:
            retention_rate = (perfect_bijection_elements / total_elements) * 100
            print(f"📊 Element retention rate: {retention_rate:.1f}%")
        
        # Write the bijection SVG
        bijection_tree.write(output_svg_path, encoding='utf-8', xml_declaration=True)
        
        print(f"📄 Perfect bijection SVG saved to: {output_svg_path}")
        
        # Verify the output file
        if os.path.exists(output_svg_path):
            file_size = os.path.getsize(output_svg_path)
            print(f"💾 File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
        
        return output_svg_path
        
    except ET.ParseError as e:
        raise RuntimeError(f"Failed to parse SVG files: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to extract bijection elements: {e}")


def _build_element_map(root) -> dict:
    """Build a mapping of elements using their identifying characteristics."""
    element_map = {}
    
    for elem in root.iter():
        if _is_graphics_element(elem):
            key = _get_element_key(elem)
            element_map[key] = elem
    
    return element_map


def _get_element_key(elem) -> str:
    """Generate a unique key for an element based on its characteristics."""
    # Use tag, position attributes, and parent structure for identification
    key_parts = [elem.tag.split('}')[-1]]  # Clean tag name
    
    # Add identifying attributes (but not color attributes)
    for attr in ['id', 'class', 'x', 'y', 'cx', 'cy', 'r', 'rx', 'ry', 'width', 'height', 'd', 'points']:
        if elem.get(attr):
            key_parts.append(f"{attr}:{elem.get(attr)}")
    
    # Add parent tag for context
    parent = _find_parent_tag(elem)
    if parent:
        key_parts.insert(0, f"parent:{parent}")
    
    return '|'.join(key_parts)


def _find_parent_tag(elem) -> str:
    """Find the parent element's tag name."""
    # This is a simplified approach - in practice we'd walk the tree
    return "svg"  # Default parent for now


def _is_graphics_element(elem) -> bool:
    """Check if element is a graphics element that can have colors."""
    tag = elem.tag.split('}')[-1].lower()  # Remove namespace
    graphics_tags = {
        'rect', 'circle', 'ellipse', 'line', 'polyline', 'polygon', 
        'path', 'text', 'tspan', 'g', 'use', 'image'
    }
    return tag in graphics_tags


def _check_perfect_bijection(grey_elem, inv_elem) -> dict:
    """
    Check if two corresponding elements have perfect black-white bijection.
    Returns dict with bijection analysis.
    """
    result = {
        'has_bijection': False,
        'black_to_white': False,
        'white_to_black': False,
        'matched_attributes': [],
        'mismatched_attributes': []
    }
    
    # Check fill attributes
    grey_fill = grey_elem.get('fill', 'none')
    inv_fill = inv_elem.get('fill', 'none')
    
    if _is_perfect_color_bijection(grey_fill, inv_fill):
        result['has_bijection'] = True
        result['matched_attributes'].append('fill')
        
        if _is_black_color(grey_fill) and _is_white_color(inv_fill):
            result['black_to_white'] = True
        elif _is_white_color(grey_fill) and _is_black_color(inv_fill):
            result['white_to_black'] = True
    elif grey_fill != 'none' or inv_fill != 'none':
        result['mismatched_attributes'].append('fill')
    
    # Check stroke attributes
    grey_stroke = grey_elem.get('stroke', 'none')
    inv_stroke = inv_elem.get('stroke', 'none')
    
    if _is_perfect_color_bijection(grey_stroke, inv_stroke):
        result['has_bijection'] = True
        result['matched_attributes'].append('stroke')
        
        if _is_black_color(grey_stroke) and _is_white_color(inv_stroke):
            result['black_to_white'] = True
        elif _is_white_color(grey_stroke) and _is_black_color(inv_stroke):
            result['white_to_black'] = True
    elif grey_stroke != 'none' or inv_stroke != 'none':
        result['mismatched_attributes'].append('stroke')
    
    # Check style attributes
    grey_style = grey_elem.get('style', '')
    inv_style = inv_elem.get('style', '')
    
    if grey_style or inv_style:
        style_bijection = _check_style_bijection(grey_style, inv_style)
        if style_bijection['has_bijection']:
            result['has_bijection'] = True
            result['matched_attributes'].append('style')
            if style_bijection['black_to_white']:
                result['black_to_white'] = True
            if style_bijection['white_to_black']:
                result['white_to_black'] = True
        else:
            result['mismatched_attributes'].append('style')
    
    # Element must have at least one perfect color bijection and no mismatches
    result['has_bijection'] = result['has_bijection'] and len(result['mismatched_attributes']) == 0
    
    return result


def _is_perfect_color_bijection(color1: str, color2: str) -> bool:
    """Check if two colors form a perfect bijection (black<->white)."""
    if color1 == 'none' and color2 == 'none':
        return True
    
    # Check black -> white
    if _is_black_color(color1) and _is_white_color(color2):
        return True
    
    # Check white -> black  
    if _is_white_color(color1) and _is_black_color(color2):
        return True
    
    return False


def _is_black_color(color: str) -> bool:
    """Check if a color is perfect black."""
    if not color or color == 'none':
        return False
    
    black_values = ['#000000', '#000', 'black', 'rgb(0, 0, 0)', 'rgba(0, 0, 0, 1)', 'rgba(0,0,0,1)']
    return color.lower().replace(' ', '') in [v.lower() for v in black_values]


def _is_white_color(color: str) -> bool:
    """Check if a color is perfect white."""
    if not color or color == 'none':
        return False
    
    white_values = ['#ffffff', '#fff', 'white', 'rgb(255, 255, 255)', 'rgba(255, 255, 255, 1)', 'rgba(255,255,255,1)']
    return color.lower().replace(' ', '') in [v.lower() for v in white_values]


def _check_style_bijection(style1: str, style2: str) -> dict:
    """Check style attributes for perfect bijection."""
    result = {'has_bijection': False, 'black_to_white': False, 'white_to_black': False}
    
    if not style1 and not style2:
        result['has_bijection'] = True
        return result
    
    # Parse style properties
    props1 = _parse_style_properties(style1)
    props2 = _parse_style_properties(style2)
    
    # Check each color property
    for prop in ['fill', 'stroke', 'color', 'stop-color']:
        val1 = props1.get(prop)
        val2 = props2.get(prop)
        
        if val1 or val2:
            if _is_perfect_color_bijection(val1 or 'none', val2 or 'none'):
                result['has_bijection'] = True
                if _is_black_color(val1) and _is_white_color(val2):
                    result['black_to_white'] = True
                elif _is_white_color(val1) and _is_black_color(val2):
                    result['white_to_black'] = True
            else:
                # Mismatch in style colors
                result['has_bijection'] = False
                break
    
    return result


def _parse_style_properties(style: str) -> dict:
    """Parse CSS style string into property dictionary."""
    props = {}
    if style:
        for prop in style.split(';'):
            if ':' in prop:
                key, value = prop.split(':', 1)
                props[key.strip()] = value.strip()
    return props


def _find_parent(root, target_elem):
    """Find the parent of target_elem in the tree."""
    for elem in root.iter():
        if target_elem in list(elem):
            return elem
    return None

print("✅ Perfect black-white bijection extraction functions defined successfully!")

# %%
# Extract perfect black-white bijection elements
try:
    if 'optimized_greyscale_svg' in globals() and 'inverted_colors_svg' in globals():
        if os.path.exists(optimized_greyscale_svg) and os.path.exists(inverted_colors_svg):
            print(f"🔄 Extracting perfect bijection elements...")
            print(f"📄 Comparing: {os.path.basename(optimized_greyscale_svg)}")
            print(f"📄      with: {os.path.basename(inverted_colors_svg)}")
            
            # Extract bijection elements
            test_bijectionBW = extract_bijection_bw_elements(
                optimized_greyscale_svg, 
                inverted_colors_svg
            )
            
            print(f"\n📊 Perfect Bijection Analysis")
            print("=" * 50)
            
            # Analyze the bijection results
            if os.path.exists(test_bijectionBW):
                # Parse the bijection SVG to analyze what was kept
                tree = ET.parse(test_bijectionBW)
                root = tree.getroot()
                
                # Count elements and colors
                graphics_elements = 0
                black_elements = 0
                white_elements = 0
                unique_colors = set()
                
                for elem in root.iter():
                    if _is_graphics_element(elem):
                        graphics_elements += 1
                        
                        fill = elem.get('fill')
                        stroke = elem.get('stroke')
                        
                        if fill and fill != 'none':
                            unique_colors.add(fill)
                            if _is_black_color(fill):
                                black_elements += 1
                            elif _is_white_color(fill):
                                white_elements += 1
                        
                        if stroke and stroke != 'none':
                            unique_colors.add(stroke)
                            if _is_black_color(stroke):
                                black_elements += 1
                            elif _is_white_color(stroke):
                                white_elements += 1
                
                print(f"🎯 Graphics elements retained: {graphics_elements}")
                print(f"⚫ Perfect black attributes: {black_elements}")
                print(f"⚪ Perfect white attributes: {white_elements}")
                print(f"🎨 Unique colors in bijection: {len(unique_colors)}")
                
                # Show the colors found
                if unique_colors:
                    print(f"\n🎨 Colors in perfect bijection:")
                    for color in sorted(unique_colors):
                        color_type = "BLACK" if _is_black_color(color) else "WHITE" if _is_white_color(color) else "OTHER"
                        print(f"  {color} ({color_type})")
                
                # File size information
                original_grey_size = os.path.getsize(optimized_greyscale_svg)
                bijection_size = os.path.getsize(test_bijectionBW)
                reduction = original_grey_size - bijection_size
                reduction_percent = (reduction / original_grey_size) * 100 if original_grey_size > 0 else 0
                
                print(f"\n📄 File Size Analysis:")
                print(f"📄 Original greyscale: {original_grey_size:,} bytes")
                print(f"📄 Perfect bijection:  {bijection_size:,} bytes")
                print(f"💾 Reduction: {reduction:,} bytes ({reduction_percent:.1f}%)")
                
                # Quality assessment
                if graphics_elements > 0:
                    if black_elements > 0 and white_elements > 0:
                        print(f"\n✅ SUCCESS: Found perfect die-line bijection elements!")
                        print(f"🎯 Die-lines isolated with perfect black-white contrast")
                        print(f"🔄 Elements maintain perfect inversion relationship")
                    elif black_elements > 0:
                        print(f"\n⚠️  PARTIAL: Found black die-lines but no white elements")
                    elif white_elements > 0:
                        print(f"\n⚠️  PARTIAL: Found white backgrounds but no black elements") 
                    else:
                        print(f"\n⚠️  WARNING: No perfect black/white elements found")
                else:
                    print(f"\n❌ No graphics elements retained - bijection filter too strict")
                
                # Store the result
                print(f"\n📁 Perfect bijection SVG: {os.path.basename(test_bijectionBW)}")
                print(f"🎯 This file contains only elements with perfect black↔white inversion")
                print(f"🔧 Ideal for die-line isolation and contrast analysis")
            
            else:
                print(f"❌ Failed to create bijection file")
        
        else:
            missing_files = []
            if not os.path.exists(optimized_greyscale_svg):
                missing_files.append("greyscale SVG")
            if not os.path.exists(inverted_colors_svg):
                missing_files.append("inverted SVG")
            print(f"❌ Missing required files: {', '.join(missing_files)}")
    
    else:
        print("❌ Please run the greyscale conversion and color inversion steps first.")
        
except Exception as e:
    print(f"❌ Error during bijection extraction: {e}")
    print("This could be due to SVG structure differences or parsing issues.")

# %% [markdown]
# ## 9. Filter to Lines, Rectangles and Squares Only
# 
# Now we'll filter the perfect bijection elements to keep only basic geometric shapes: lines, rectangles, and squares. This removes complex curves and keeps only the structural die-line elements.

# %%
def filter_to_geometric_shapes(svg_path: str, output_svg_path: str = None) -> str:
    """
    Filter SVG to keep only lines, rectangles, and squares. Remove all other shapes
    like circles, ellipses, complex paths, curves, etc.
    
    Args:
        svg_path: Path to the input SVG file
        output_svg_path: Path for the filtered SVG (defaults to input_geometric.svg)
    
    Returns:
        Path to the filtered SVG file containing only basic geometric shapes
    """
    svg_path = os.path.abspath(svg_path)
    
    if not os.path.exists(svg_path):
        raise FileNotFoundError(f"SVG file not found: {svg_path}")
    
    if output_svg_path is None:
        base_name = os.path.splitext(os.path.basename(svg_path))[0]
        output_svg_path = os.path.join(
            os.path.dirname(svg_path),
            f"{base_name}_geometric.svg"
        )
    
    output_svg_path = os.path.abspath(output_svg_path)
    
    print(f"🔄 Filtering to geometric shapes only (lines, rectangles, squares)...")
    
    try:
        # Parse the SVG file
        tree = ET.parse(svg_path)
        root = tree.getroot()
        
        # Statistics
        total_elements = 0
        kept_elements = 0
        removed_elements = []
        shape_counts = {
            'lines': 0,
            'rectangles': 0, 
            'squares': 0,
            'removed_circles': 0,
            'removed_ellipses': 0,
            'removed_complex_paths': 0,
            'removed_polygons': 0,
            'removed_other': 0
        }
        
        # Process all elements
        for elem in list(root.iter()):
            total_elements += 1
            
            # Skip root and container elements
            if elem == root or _is_container_element(elem):
                continue
            
            # Check if element is a basic geometric shape
            shape_analysis = _analyze_shape_type(elem)
            
            if shape_analysis['keep']:
                kept_elements += 1
                shape_counts[shape_analysis['type']] += 1
                print(f"✅ Keeping {shape_analysis['type']}: {shape_analysis['description']}")
            else:
                removed_elements.append(elem)
                removed_key = f"removed_{shape_analysis['type']}"
                if removed_key in shape_counts:
                    shape_counts[removed_key] += 1
                else:
                    shape_counts['removed_other'] += 1
                print(f"🗑️  Removing {shape_analysis['type']}: {shape_analysis['description']}")
        
        # Remove the unwanted elements
        for elem in removed_elements:
            parent = _find_parent(root, elem)
            if parent is not None:
                parent.remove(elem)
        
        print(f"\n📊 Geometric Filtering Results")
        print("=" * 50)
        print(f"🔢 Total elements processed: {total_elements}")
        print(f"✅ Elements kept: {kept_elements}")
        print(f"🗑️  Elements removed: {len(removed_elements)}")
        
        print(f"\n🎯 Kept Shapes:")
        print(f"  📏 Lines: {shape_counts['lines']}")
        print(f"  📐 Rectangles: {shape_counts['rectangles']}")
        print(f"  ⬜ Squares: {shape_counts['squares']}")
        
        print(f"\n🗑️  Removed Shapes:")
        print(f"  ⭕ Circles: {shape_counts['removed_circles']}")
        print(f"  🥚 Ellipses: {shape_counts['removed_ellipses']}")
        print(f"  🌀 Complex paths: {shape_counts['removed_complex_paths']}")
        print(f"  🔷 Polygons: {shape_counts['removed_polygons']}")
        print(f"  ❓ Other shapes: {shape_counts['removed_other']}")
        
        # Calculate retention rate
        if total_elements > 0:
            retention_rate = (kept_elements / total_elements) * 100
            print(f"\n📊 Shape retention rate: {retention_rate:.1f}%")
        
        # Write the filtered SVG
        tree.write(output_svg_path, encoding='utf-8', xml_declaration=True)
        
        print(f"\n📄 Geometric shapes SVG saved to: {output_svg_path}")
        
        # File size comparison
        original_size = os.path.getsize(svg_path)
        filtered_size = os.path.getsize(output_svg_path)
        reduction = original_size - filtered_size
        
        print(f"💾 Original: {original_size:,} bytes")
        print(f"💾 Filtered: {filtered_size:,} bytes")
        if reduction > 0:
            reduction_percent = (reduction / original_size) * 100
            print(f"💾 Reduction: {reduction:,} bytes ({reduction_percent:.1f}%)")
        
        return output_svg_path
        
    except ET.ParseError as e:
        raise RuntimeError(f"Failed to parse SVG file: {e}")
    except Exception as e:
        raise RuntimeError(f"Failed to filter geometric shapes: {e}")


def _is_container_element(elem) -> bool:
    """Check if element is a container that should not be filtered."""
    tag = elem.tag.split('}')[-1].lower()  # Remove namespace
    container_tags = {'svg', 'g', 'defs', 'clipPath', 'mask', 'marker', 'pattern', 'symbol'}
    return tag in container_tags


def _analyze_shape_type(elem) -> dict:
    """
    Analyze an element to determine if it's a basic geometric shape.
    Returns dict with type classification and whether to keep it.
    """
    tag = elem.tag.split('}')[-1].lower()  # Remove namespace
    
    # Lines
    if tag == 'line':
        return {
            'keep': True,
            'type': 'lines',
            'description': f"Line from ({elem.get('x1', '0')},{elem.get('y1', '0')}) to ({elem.get('x2', '0')},{elem.get('y2', '0')})"
        }
    
    # Rectangles and squares
    elif tag == 'rect':
        width = elem.get('width', '0')
        height = elem.get('height', '0')
        
        # Try to determine if it's a square
        try:
            w_val = float(width.replace('px', '').replace('pt', '').replace('mm', ''))
            h_val = float(height.replace('px', '').replace('pt', '').replace('mm', ''))
            is_square = abs(w_val - h_val) < 0.1  # Allow small tolerance for squares
        except:
            is_square = width == height  # Fallback to string comparison
        
        shape_type = 'squares' if is_square else 'rectangles'
        return {
            'keep': True,
            'type': shape_type,
            'description': f"{shape_type.capitalize()[:-1]} {width}×{height}"
        }
    
    # Polylines that are effectively lines (2 points only)
    elif tag == 'polyline':
        points = elem.get('points', '')
        if points:
            # Count coordinate pairs
            point_pairs = [p.strip() for p in points.split() if p.strip()]
            # Remove empty strings and count comma-separated pairs
            clean_points = []
            for p in point_pairs:
                if ',' in p:
                    clean_points.append(p)
                else:
                    # Handle space-separated coordinates
                    coords = p.split()
                    if len(coords) >= 2:
                        clean_points.append(f"{coords[0]},{coords[1]}")
            
            if len(clean_points) == 2:
                return {
                    'keep': True,
                    'type': 'lines',
                    'description': f"Polyline with 2 points: {points[:50]}..."
                }
        
        return {
            'keep': False,
            'type': 'polygons',
            'description': f"Polyline with multiple points: {points[:50]}..."
        }
    
    # Paths - analyze if they're simple rectangles or lines
    elif tag == 'path':
        d = elem.get('d', '')
        path_analysis = _analyze_path_geometry(d)
        
        if path_analysis['is_simple_rectangle']:
            return {
                'keep': True,
                'type': 'rectangles',
                'description': f"Path rectangle: {d[:50]}..."
            }
        elif path_analysis['is_simple_line']:
            return {
                'keep': True,
                'type': 'lines', 
                'description': f"Path line: {d[:50]}..."
            }
        else:
            return {
                'keep': False,
                'type': 'complex_paths',
                'description': f"Complex path: {d[:50]}..."
            }
    
    # Circles - remove
    elif tag == 'circle':
        return {
            'keep': False,
            'type': 'circles',
            'description': f"Circle r={elem.get('r', '0')} at ({elem.get('cx', '0')},{elem.get('cy', '0')})"
        }
    
    # Ellipses - remove
    elif tag == 'ellipse':
        return {
            'keep': False,
            'type': 'ellipses',
            'description': f"Ellipse {elem.get('rx', '0')}×{elem.get('ry', '0')} at ({elem.get('cx', '0')},{elem.get('cy', '0')})"
        }
    
    # Polygons - remove (unless they're simple rectangles)
    elif tag == 'polygon':
        points = elem.get('points', '')
        if _is_rectangle_polygon(points):
            return {
                'keep': True,
                'type': 'rectangles',
                'description': f"Polygon rectangle: {points[:50]}..."
            }
        else:
            return {
                'keep': False,
                'type': 'polygons',
                'description': f"Polygon: {points[:50]}..."
            }
    
    # Text and other elements - remove
    else:
        return {
            'keep': False,
            'type': 'other',
            'description': f"{tag} element"
        }


def _analyze_path_geometry(d: str) -> dict:
    """Analyze SVG path data to determine if it represents simple geometry."""
    if not d:
        return {'is_simple_rectangle': False, 'is_simple_line': False}
    
    d = d.strip().upper()
    
    # Simple line: M x y L x y (move to, line to)
    line_pattern = re.match(r'^M\s*[\d\.\-\s,]+L\s*[\d\.\-\s,]+$', d)
    if line_pattern:
        return {'is_simple_rectangle': False, 'is_simple_line': True}
    
    # Simple rectangle patterns:
    # M x y H x V y H x Z (move, horizontal, vertical, horizontal, close)
    # M x y L x y L x y L x y Z (move, line, line, line, close)
    rect_pattern1 = re.match(r'^M\s*[\d\.\-\s,]+H\s*[\d\.\-\s,]+V\s*[\d\.\-\s,]+H\s*[\d\.\-\s,]+Z?$', d)
    rect_pattern2 = re.match(r'^M\s*[\d\.\-\s,]+(L\s*[\d\.\-\s,]+){3}Z?$', d)
    rect_pattern3 = re.match(r'^M\s*[\d\.\-\s,]+V\s*[\d\.\-\s,]+H\s*[\d\.\-\s,]+V\s*[\d\.\-\s,]+Z?$', d)
    
    if rect_pattern1 or rect_pattern2 or rect_pattern3:
        return {'is_simple_rectangle': True, 'is_simple_line': False}
    
    # Check for curves, arcs, or complex commands
    complex_commands = ['C', 'S', 'Q', 'T', 'A']
    has_curves = any(cmd in d for cmd in complex_commands)
    
    if has_curves:
        return {'is_simple_rectangle': False, 'is_simple_line': False}
    
    # Count move/line commands - simple shapes should have few commands
    command_count = len(re.findall(r'[MLHVZ]', d))
    if command_count <= 5:  # Simple rectangle or line
        return {'is_simple_rectangle': True, 'is_simple_line': False}
    
    return {'is_simple_rectangle': False, 'is_simple_line': False}


def _is_rectangle_polygon(points: str) -> bool:
    """Check if polygon points define a simple rectangle."""
    if not points:
        return False
    
    try:
        # Parse coordinate pairs
        coords = []
        point_pairs = points.replace(',', ' ').split()
        
        i = 0
        while i < len(point_pairs) - 1:
            try:
                x = float(point_pairs[i])
                y = float(point_pairs[i + 1])
                coords.append((x, y))
                i += 2
            except ValueError:
                return False
        
        # Rectangle should have 4 points
        if len(coords) != 4:
            return False
        
        # Check if points form a rectangle (opposite sides equal, 90-degree angles)
        # This is a simplified check - could be enhanced for more precision
        x_coords = sorted(set(coord[0] for coord in coords))
        y_coords = sorted(set(coord[1] for coord in coords))
        
        # Should have exactly 2 unique X and 2 unique Y coordinates
        return len(x_coords) == 2 and len(y_coords) == 2
        
    except Exception:
        return False

print("✅ Geometric shape filtering functions defined successfully!")

# %%
# Filter bijection SVG to keep only lines, rectangles, and squares
try:
    if 'test_bijectionBW' in globals() and os.path.exists(test_bijectionBW):
        print(f"🔄 Filtering bijection elements to basic geometric shapes...")
        print(f"📄 Input: {os.path.basename(test_bijectionBW)}")
        
        # Apply geometric filtering
        geometric_svg = filter_to_geometric_shapes(test_bijectionBW)
        
        print(f"\n📊 Final Geometric Filtering Results")
        print("=" * 50)
        
        # Analyze the final filtered SVG
        if os.path.exists(geometric_svg):
            tree = ET.parse(geometric_svg)
            root = tree.getroot()
            
            # Count final elements by shape type
            final_stats = {
                'lines': 0,
                'rectangles': 0,
                'squares': 0,
                'total_elements': 0,
                'black_elements': 0,
                'white_elements': 0
            }
            
            for elem in root.iter():
                if _is_container_element(elem):
                    continue
                    
                tag = elem.tag.split('}')[-1].lower()
                if tag in ['line', 'rect', 'path', 'polygon', 'polyline']:
                    final_stats['total_elements'] += 1
                    
                    # Classify by shape
                    shape_info = _analyze_shape_type(elem)
                    if shape_info['keep']:
                        final_stats[shape_info['type']] += 1
                    
                    # Count colors
                    fill = elem.get('fill', 'none')
                    stroke = elem.get('stroke', 'none')
                    
                    if _is_black_color(fill) or _is_black_color(stroke):
                        final_stats['black_elements'] += 1
                    elif _is_white_color(fill) or _is_white_color(stroke):
                        final_stats['white_elements'] += 1
            
            print(f"🎯 Final Element Count:")
            print(f"  📏 Lines: {final_stats['lines']}")
            print(f"  📐 Rectangles: {final_stats['rectangles']}")
            print(f"  ⬜ Squares: {final_stats['squares']}")
            print(f"  🔢 Total shapes: {final_stats['total_elements']}")
            
            print(f"\n🎨 Color Distribution:")
            print(f"  ⚫ Black elements: {final_stats['black_elements']}")
            print(f"  ⚪ White elements: {final_stats['white_elements']}")
            
            # File size progression
            original_bijection_size = os.path.getsize(test_bijectionBW)
            geometric_size = os.path.getsize(geometric_svg)
            final_reduction = original_bijection_size - geometric_size
            
            print(f"\n📄 File Size Progression:")
            print(f"  📄 Perfect bijection: {original_bijection_size:,} bytes")
            print(f"  📄 Geometric filtered: {geometric_size:,} bytes")
            
            if final_reduction > 0:
                reduction_percent = (final_reduction / original_bijection_size) * 100
                print(f"  💾 Final reduction: {final_reduction:,} bytes ({reduction_percent:.1f}%)")
            else:
                print(f"  📊 No size change (all elements were geometric)")
            
            # Quality assessment
            if final_stats['total_elements'] > 0:
                print(f"\n✅ SUCCESS: Geometric die-line elements isolated!")
                print(f"🎯 {final_stats['total_elements']} basic geometric shapes retained")
                print(f"🔧 Perfect for structural die-line analysis")
                
                if final_stats['lines'] > 0:
                    print(f"📏 Contains {final_stats['lines']} lines (cutting paths)")
                if final_stats['rectangles'] > 0:
                    print(f"📐 Contains {final_stats['rectangles']} rectangles (panels/windows)")
                if final_stats['squares'] > 0:
                    print(f"⬜ Contains {final_stats['squares']} squares (registration marks)")
                    
            else:
                print(f"\n⚠️  WARNING: No geometric elements found!")
                print(f"🔍 The design may contain only complex curves or text")
            
            # Store final result
            final_geometric_svg = geometric_svg
            
            print(f"\n📁 Final filtered SVG: {os.path.basename(geometric_svg)}")
            print(f"🎯 Contains only: lines, rectangles, squares with perfect B/W contrast")
            print(f"🔧 Ideal for die-line cutting and structural analysis")
            
        else:
            print(f"❌ Failed to create geometric filtered file")
    
    else:
        print("❌ No bijection SVG found. Please run the bijection extraction step first.")
        
except Exception as e:
    print(f"❌ Error during geometric filtering: {e}")
    print("This could be due to complex SVG structure or unsupported shape formats.")


