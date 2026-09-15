import sys
import os

try:
    import cairosvg
    from PIL import Image
except ImportError:
    print("Dependencies missing for SVG conversion. Please run: pip install cairosvg pillow")
    sys.exit(1)

if len(sys.argv) < 3:
    print("Usage: python svg_to_ico.py <input.svg> <output.ico>")
    sys.exit(1)

svg_path = sys.argv[1]
ico_path = sys.argv[2]

if not os.path.exists(svg_path):
    print(f"Error: {svg_path} not found.")
    sys.exit(1)

try:
    temp_png = "temp_icon.png"
    # Convert SVG to PNG
    cairosvg.svg2png(url=svg_path, write_to=temp_png)

    # Convert PNG to ICO using Pillow
    img = Image.open(temp_png)
    # Ensure it's square and save as multi-size ICO
    img.save(ico_path, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)])
    img.close()
    
    if os.path.exists(temp_png):
        os.remove(temp_png)
        
    print(f"Successfully converted {svg_path} to {ico_path}")
except Exception as e:
    print(f"Failed to convert SVG to ICO: {e}")
    sys.exit(1)
