#!/usr/bin/env python3
"""Draw the tab icon: a blue line with three ring stops on a navy rounded square.

    python3 tools/make_icons.py     (needs Pillow)

Writes docs/favicon.svg, docs/favicon.ico and docs/apple-touch-icon.png from the numbers below.
"""
from pathlib import Path

from PIL import Image, ImageDraw

DOCS = Path(__file__).resolve().parent.parent / "docs"
NAVY, BLUE = "#16233b", "#3987e5"
BOX, CORNER = 64, 14            # the drawing is laid out on a 64-unit square
LINE_Y, LINE_W = 32, 6
STOPS, RING_R, RING_W = (13, 32, 51), 5.75, 4.5

SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {BOX} {BOX}">
<rect width="{BOX}" height="{BOX}" rx="{CORNER}" fill="{NAVY}"/>
<path d="M{STOPS[0]} {LINE_Y}H{STOPS[-1]}" stroke="{BLUE}" stroke-width="{LINE_W}" stroke-linecap="round"/>
{"".join(f'<circle cx="{x}" cy="{LINE_Y}" r="{RING_R}" fill="{NAVY}" stroke="{BLUE}" stroke-width="{RING_W}"/>' for x in STOPS)}
</svg>
"""


def draw(size, rounded=True, oversample=8):
    k = size * oversample / BOX
    img = Image.new("RGBA", (size * oversample, size * oversample), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, BOX * k - 1, BOX * k - 1], radius=CORNER * k if rounded else 0, fill=NAVY)
    d.line([STOPS[0] * k, LINE_Y * k, STOPS[-1] * k, LINE_Y * k], fill=BLUE, width=round(LINE_W * k))
    outer, inner = RING_R + RING_W / 2, RING_R - RING_W / 2
    for x in STOPS:
        d.ellipse([(x - outer) * k, (LINE_Y - outer) * k, (x + outer) * k, (LINE_Y + outer) * k], fill=BLUE)
        d.ellipse([(x - inner) * k, (LINE_Y - inner) * k, (x + inner) * k, (LINE_Y + inner) * k], fill=NAVY)
    return img.resize((size, size), Image.LANCZOS)


def main():
    (DOCS / "favicon.svg").write_text(SVG, encoding="utf-8")
    draw(48).save(DOCS / "favicon.ico", sizes=[(16, 16), (32, 32), (48, 48)])
    draw(180, rounded=False).convert("RGB").save(DOCS / "apple-touch-icon.png")
    print("icons written to", DOCS)


if __name__ == "__main__":
    main()
