#!/usr/bin/env python3
"""Compose a preview contact sheet of the icon set on Stream-Deck-like backgrounds."""
from PIL import Image, ImageDraw, ImageFont
import os

IMGS = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "com.welsh.cameradials.sdPlugin", "imgs"))
OUT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "icon-preview.png"))


def load(n):
    return Image.open(os.path.join(IMGS, n)).convert("RGBA")


def font(sz, bold=True):
    for name in (("segoeuib.ttf" if bold else "segoeui.ttf"), "arialbd.ttf", "arial.ttf"):
        try:
            return ImageFont.truetype(name, sz)
        except Exception:
            pass
    return ImageFont.load_default()


W, H = 900, 640
sheet = Image.new("RGBA", (W, H), (24, 24, 27, 255))   # zinc-900
d = ImageDraw.Draw(sheet)
d.text((30, 22), "Camera Scroller — icon set", font=font(26), fill=(255, 255, 255, 255))
d.text((30, 58), "wall-mounted CCTV camera + lens  =  scroll the UniFi Protect cameras",
       font=font(15, False), fill=(160, 160, 168, 255))

# 1) plugin tile (the "logo") at a few sizes
tile = load("plugin-icon.png")
y = 110
d.text((30, y - 28), "Plugin logo tile (256px source)", font=font(15, False), fill=(150, 150, 158, 255))
x = 30
for s in (128, 96, 64, 48):
    sheet.alpha_composite(tile.resize((s, s), Image.LANCZOS), (x, y))
    x += s + 24
d.text((x + 8, y + 40), "full-color\nrounded tile", font=font(14, False), fill=(150, 150, 158, 255))

# 2) action / category monochrome glyphs on the dark sidebar
y2 = 290
d.text((30, y2 - 28), "Action list glyph (white on transparent)", font=font(15, False), fill=(150, 150, 158, 255))
row = Image.new("RGBA", (300, 56), (38, 38, 42, 255))
sheet.alpha_composite(row, (30, y2))
act = load("action-camera@2x.png").resize((28, 28), Image.LANCZOS)
sheet.alpha_composite(act, (30 + 14, y2 + 14))
d.text((30 + 56, y2 + 18), "Camera Scroller", font=font(16, False), fill=(230, 230, 235, 255))
for i, s in enumerate((20, 40)):
    gi = load("action-camera@2x.png").resize((s, s), Image.LANCZOS)
    sheet.alpha_composite(gi, (360 + i * 70, y2 + (40 - s) // 2 + 8))
    d.text((360 + i * 70, y2 + 50), f"{s}px", font=font(12, False), fill=(140, 140, 148, 255))

# 3) the LCD dial mockup (how the dial will look)
y3 = 290
dx = 560
d.text((dx, y3 - 28), "Stream Deck+ dial (LCD)", font=font(15, False), fill=(150, 150, 158, 255))
dial = Image.new("RGBA", (300, 150), (0, 0, 0, 0))
dd = ImageDraw.Draw(dial)
dd.rounded_rectangle([0, 0, 299, 149], radius=16, fill=(12, 12, 14, 255))
lcd_icon = load("cctv@2x.png").resize((72, 72), Image.LANCZOS)
dial.alpha_composite(lcd_icon, (21, 39))
dd.text((105, 30), "Front Door", font=font(28), fill=(255, 255, 255, 255))
dd.text((105, 78), "camera", font=font(18, False), fill=(125, 211, 252, 255))
sheet.alpha_composite(dial, (dx, y3))

# footer
d.text((30, H - 46), "sizes shipped:  action 20/40 · category 28/56 · plugin 256/512 · LCD 48/96",
       font=font(14, False), fill=(140, 140, 148, 255))

sheet.convert("RGB").save(OUT)
print("wrote", OUT)
