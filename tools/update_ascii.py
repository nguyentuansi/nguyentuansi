"""Regenerate the ASCII portrait in dark_mode.svg and light_mode.svg from an image.

Usage:
    python tools/update_ascii.py <image_path> [--crop L,T,R,B] [--contrast N] [--cols N] [--rows N]

Examples:
    # From a local file
    python tools/update_ascii.py avatar.png

    # From your GitHub avatar (download first)
    curl -sL https://avatars.githubusercontent.com/nguyentuansi -o /tmp/avatar.png
    python tools/update_ascii.py /tmp/avatar.png

    # Tweak crop / contrast if the portrait looks off (crop skips borders/other faces)
    python tools/update_ascii.py avatar.png --crop 80,30,410,460 --contrast 1.6

Only the 25 ASCII-art tspans (x=15, y=30..510) are replaced. All stat fields,
LinkedIn, email, etc. are left alone.

Requires: pip install Pillow
"""
import argparse
import re
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image, ImageEnhance, ImageOps

RAMP = " .',:;!|ijlwkmg%M@@"
REPO = Path(__file__).resolve().parent.parent


def make_ascii(image_path, crop, contrast, cols, rows):
    img = Image.open(image_path).convert("RGB")
    if crop:
        img = img.crop(crop)
    img = img.convert("L")
    img = ImageOps.autocontrast(img, cutoff=2)
    img = ImageEnhance.Contrast(img).enhance(contrast)
    img = img.resize((cols, rows))
    px = img.load()
    lines = []
    for y in range(rows):
        line = "".join(RAMP[int((255 - px[x, y]) / 255 * (len(RAMP) - 1))] for x in range(cols))
        lines.append(line.rstrip())
    return lines


def replace_ascii(svg_path, lines):
    s = svg_path.read_text()
    for i, line in enumerate(lines):
        y = 30 + 20 * i
        pattern = re.compile(rf'<tspan x="15" y="{y}">[^<]*</tspan>')
        assert pattern.search(s), f'no ascii tspan at y={y} in {svg_path}'
        s = pattern.sub(f'<tspan x="15" y="{y}">{escape(line)}</tspan>', s, count=1)
    svg_path.write_text(s)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('image', help='Path to source image (jpg/png)')
    ap.add_argument('--crop', help='L,T,R,B pixel coords to crop before resize', default=None)
    ap.add_argument('--contrast', type=float, default=1.6, help='Contrast multiplier (default 1.6)')
    ap.add_argument('--cols', type=int, default=38, help='ASCII columns (default 38 — matches SVG left column width)')
    ap.add_argument('--rows', type=int, default=25, help='ASCII rows (default 25 — must equal 25 to match y=30..510 slots)')
    args = ap.parse_args()

    if args.rows != 25:
        ap.error('--rows must be 25 to align with the SVG y-slot layout (30..510 in 20px steps)')

    crop = tuple(int(v) for v in args.crop.split(',')) if args.crop else None
    lines = make_ascii(args.image, crop, args.contrast, args.cols, args.rows)
    print('Preview:')
    print('\n'.join(lines))
    print()
    for name in ('dark_mode.svg', 'light_mode.svg'):
        replace_ascii(REPO / name, lines)
        print(f'updated {name}')


if __name__ == '__main__':
    main()
