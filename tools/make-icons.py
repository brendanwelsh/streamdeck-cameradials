#!/usr/bin/env python3
"""Render the Camera Scroller icon set as crisp vector PNGs (pycairo).

One mark: a wall-mounted security (CCTV) camera with a single big lens = "scroll the
UniFi Protect cameras". Drawn in a 100x100 logical space and scaled to each Stream Deck
target size, so every output is sharp at its native resolution. Run:
    python tools/make-icons.py

Style is kept in lock-step with the sibling streamdeck-audioswap plugin: same sky
palette, same gradient app tile, same white monochrome action/category glyphs.
"""
import cairo, os, math

IMGS = os.path.join(os.path.dirname(__file__), "..", "com.welsh.cameradials.sdPlugin", "imgs")
IMGS = os.path.abspath(IMGS)
os.makedirs(IMGS, exist_ok=True)

WHITE  = (1, 1, 1)
SKY    = (0.22, 0.74, 0.97)   # #38BDF8 sky-400, the plugin's accent
SKY_HI = (0.06, 0.65, 0.91)   # #0EA5E9 sky-500 (tile gradient top)
SKY_LO = (0.01, 0.41, 0.63)   # #0369A1 sky-800 (tile gradient bottom)


def rrect(ctx, x, y, w, h, r):
    ctx.new_sub_path()
    ctx.arc(x + w - r, y + r,     r, -math.pi / 2, 0)
    ctx.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    ctx.arc(x + r,     y + h - r, r, math.pi / 2, math.pi)
    ctx.arc(x + r,     y + r,     r, math.pi, 1.5 * math.pi)
    ctx.close_path()


def capsule(ctx, x1, y1, x2, y2, r):
    """A line segment with round caps, as a filled path."""
    ang = math.atan2(y2 - y1, x2 - x1)
    nx, ny = math.cos(ang + math.pi / 2), math.sin(ang + math.pi / 2)
    ctx.new_sub_path()
    ctx.arc(x2, y2, r, ang - math.pi / 2, ang + math.pi / 2)
    ctx.arc(x1, y1, r, ang + math.pi / 2, ang + 1.5 * math.pi)
    ctx.close_path()


def draw_glyph(ctx, body, accent, sw=0):
    """Wall-mounted CCTV camera in 0..100 space.

    `body` = the camera silhouette, `accent` = the lens fill (only used when it differs
    from `body`, e.g. the LCD pixmap). The lens is punched as a real hole so it reads on
    the gradient tile (blue lens) and as a monochrome glyph alike.
    """
    cx, cy = 48.0, 46.0          # barrel centre
    th = 0.34                    # barrel tilt (nose down to the right)
    c, s = math.cos(th), math.sin(th)

    def world(lx, ly):           # local barrel frame -> 0..100 space
        return (cx + lx * c - ly * s, cy + lx * s + ly * c)

    back = world(-26, 0)         # barrel back (upper-left)
    lensc = world(27, 0)         # lens centre (front)
    lensR, lensHole = 21.0, 9.0

    ctx.push_group()

    ctx.set_source_rgb(*body)
    # wall plate + bracket arm into the barrel back
    rrect(ctx, 6, 24, 10, 46, 5); ctx.fill()
    capsule(ctx, 16, 48, back[0], back[1], 8); ctx.fill()
    ctx.arc(back[0], back[1], 12, 0, 2 * math.pi); ctx.fill()     # shoulder knuckle

    # barrel (rotated capsule)
    ctx.save()
    ctx.translate(cx, cy); ctx.rotate(th)
    rrect(ctx, -26, -15.5, 52, 31, 15.5); ctx.fill()
    ctx.restore()

    # lens housing (bulges past the barrel)
    ctx.arc(lensc[0], lensc[1], lensR, 0, 2 * math.pi); ctx.fill()

    # punch the lens hole through the whole silhouette
    ctx.set_operator(cairo.OPERATOR_CLEAR)
    ctx.new_sub_path(); ctx.arc(lensc[0], lensc[1], lensHole, 0, 2 * math.pi); ctx.fill()
    ctx.set_operator(cairo.OPERATOR_OVER)

    ctx.pop_group_to_source()
    ctx.paint()

    # tint the lens on two-tone targets (LCD): leave hollow when monochrome
    if accent != body:
        ctx.set_source_rgb(*accent)
        ctx.arc(lensc[0], lensc[1], lensHole, 0, 2 * math.pi); ctx.fill()


def render(path, size, body, accent, tile=False, margin=0.06):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
    ctx = cairo.Context(surf)

    if tile:
        grad = cairo.LinearGradient(0, 0, 0, size)
        grad.add_color_stop_rgb(0.0, *SKY_HI)
        grad.add_color_stop_rgb(1.0, *SKY_LO)
        ctx.set_source(grad)
        rrect(ctx, 0, 0, size, size, size * 0.22)
        ctx.fill()
        glyph_scale = 0.60
    else:
        glyph_scale = 1.0 - 2 * margin

    side = size * glyph_scale
    off = (size - side) / 2.0
    ctx.translate(off, off)
    ctx.scale(side / 100.0, side / 100.0)
    draw_glyph(ctx, body, accent)

    surf.write_to_png(path)
    print("wrote", os.path.relpath(path, IMGS), f"{size}px")


def p(name):
    return os.path.join(IMGS, name)


# Action icon: monochrome white on transparent (20 / 40)
render(p("action-camera.png"),    20, WHITE, WHITE)
render(p("action-camera@2x.png"), 40, WHITE, WHITE)

# Category icon: monochrome white on transparent (28 / 56)
render(p("category.png"),         28, WHITE, WHITE)
render(p("category@2x.png"),      56, WHITE, WHITE)

# Plugin "logo" tile: full-color sky gradient + white glyph (256 / 512)
render(p("plugin-icon.png"),     256, WHITE, WHITE, tile=True)
render(p("plugin-icon@2x.png"),  512, WHITE, WHITE, tile=True)

# LCD dial pixmap: white camera + sky-blue lens on transparent (48 / 96)
render(p("cctv.png"),             48, WHITE, SKY)
render(p("cctv@2x.png"),          96, WHITE, SKY)

print("done ->", IMGS)
