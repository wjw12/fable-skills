"""Make an edit mask the size of <image>: transparent (editable) inside each box x0,y0,x1,y1, opaque (kept) elsewhere."""
import sys

from PIL import Image, ImageDraw

image, out, *boxes = sys.argv[1:]
mask = Image.new("RGBA", Image.open(image).size, (0, 0, 0, 255))
draw = ImageDraw.Draw(mask)
for box in boxes:
    draw.rectangle([int(v) for v in box.split(",")], fill=(0, 0, 0, 0))
mask.save(out)
