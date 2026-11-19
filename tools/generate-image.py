#!/usr/bin/env python3
"""Draw the 18 November 2026 front page (1024x1024) with Pillow only.

A newspaper front page for Wednesday 18 November 2026: masthead,
giant serif date, 13 numbered story panels in 3 rows, a world map
with numbered pins, a 30-item "also" index, and a stat strip. All 13
panels use generated photographs from assets/ instead of drawings.
Deterministic: a fixed seed and fixed photo crops, so every run
writes identical bytes.
Run: python3 tools/generate-image.py
"""
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import math
import os
import random

W, H = 1024, 1024
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(BASE, "entry.png")

SANSB = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SERIFB = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"

NAVY = (19, 33, 61)
PAPER = (246, 240, 221)
INK = (0, 0, 0)
RED = (170, 28, 28)
GREY = (70, 70, 70)
BLUE = (30, 80, 160)
CRIMSON = (168, 48, 32)
GREEN = (34, 112, 68)
PURPLE = (92, 58, 148)
TEAL = (18, 108, 128)
SLATE = (52, 58, 64)

img = Image.new("RGB", (W, H), PAPER)
d = ImageDraw.Draw(img)


def font(path, size):
    return ImageFont.truetype(path, size)


def wrap(text, fnt, width):
    """Greedy word wrap; returns a list of lines that fit `width`."""
    words, lines, cur = text.split(), [], ""
    for w in words:
        trial = (cur + " " + w).strip()
        if d.textlength(trial, font=fnt) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def _lerp(c1, c2, t):
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


def _blend(c, bg, t):
    return tuple(int(c[i] + (bg[i] - c[i]) * t) for i in range(3))


def vgrad(x, y, w, h, c1, c2):
    """Vertical gradient, top c1 -> bottom c2, drawn as 1px lines."""
    if h <= 1:
        d.rectangle([x, y, x + w, y + h], fill=c1)
        return
    for i in range(h):
        d.line([(x, y + i), (x + w, y + i)], fill=_lerp(c1, c2, i / (h - 1)))


def hgrad(x, y, w, h, c1, c2):
    if w <= 1:
        d.rectangle([x, y, x + w, y + h], fill=c1)
        return
    for i in range(w):
        d.line([(x + i, y), (x + i, y + h)], fill=_lerp(c1, c2, i / (w - 1)))


def soft_disc(cx, cy, rx, ry, colour, bg, steps=6):
    """Soft-edged disc: concentric ellipses fading into bg (smoke/glow)."""
    for i in range(steps, 0, -1):
        t = i / steps
        col = _blend(colour, bg, 1 - t * 0.85)
        d.ellipse([cx - rx * t, cy - ry * t, cx + rx * t, cy + ry * t], fill=col)


def sun_glow(cx, cy, r, sky):
    for i in range(4, 0, -1):
        col = _blend((255, 214, 130), sky, 1 - i / 4 * 0.75)
        d.ellipse([cx - r * i, cy - r * i, cx + r * i, cy + r * i], fill=col)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(255, 226, 150))


def mgrad(x, y, w, h, stops):
    """Multi-stop vertical gradient; stops is a list of (pos 0..1, colour)."""
    if h <= 1:
        d.rectangle([x, y, x + w, y + h], fill=stops[-1][1])
        return
    for i in range(h):
        t = i / (h - 1)
        col = stops[-1][1]
        for j in range(len(stops) - 1):
            p0, c0 = stops[j]
            p1, c1 = stops[j + 1]
            if p0 <= t <= p1:
                f = 0 if p1 == p0 else (t - p0) / (p1 - p0)
                col = _lerp(c0, c1, f)
                break
        d.line([(x, y + i), (x + w, y + i)], fill=col)


def cinema_grade(x, y, w, h, warm=(255, 176, 92), strength=26):
    """Cinematic grade, clipped to one picture: a warm golden wash
    falling from the top, a dark foreground shade at the bottom, and
    a soft vignette at the edges. Alpha only, drawn on an overlay and
    pasted in, so nothing spills outside the rect and text drawn later
    stays crisp."""
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(ov)
    half = max(1, h // 2)
    for i in range(half):
        a = int(strength * (1 - i / half))
        od.line([(x, y + i), (x + w, y + i)], fill=warm + (a,), width=1)
    bot = max(1, h // 3)
    for i in range(bot):
        a = int(44 * (i / bot))
        od.line([(x, y + h - bot + i), (x + w, y + h - bot + i)],
                fill=(8, 14, 28) + (a,), width=1)
    edge = 9
    for i in range(edge):
        a = int(20 * (1 - i / edge))
        od.line([(x + i, y), (x + i, y + h)], fill=(8, 14, 28) + (a,), width=1)
        od.line([(x + w - i, y), (x + w - i, y + h)], fill=(8, 14, 28) + (a,), width=1)
    img.paste(ov, (0, 0), ov)


def missile_trail(x0, y0, x1, y1, sky):
    """A bright diagonal missile trail with a glowing head, like the
    night-sky shots in the reference: white-hot core, gold halo."""
    soft_disc(x1, y1, 5, 3, (255, 220, 140), sky, steps=3)
    d.line([(x0, y0), (x1, y1)], fill=(255, 190, 90), width=3)
    d.line([(x0, y0), (x1, y1)], fill=(255, 255, 230), width=1)
    d.ellipse([x1 - 2, y1 - 2, x1 + 2, y1 + 2], fill=(255, 255, 240))


def speckle(x, y, w, h, n, seed, cols, r=1):
    """Seeded texture flecks clipped to a rect (deterministic)."""
    rr = random.Random(seed)
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + w), min(H, y + h)
    for _ in range(n):
        px = rr.randint(x0, max(x0, x1 - 1))
        py = rr.randint(y0, max(y0, y1 - 1))
        d.ellipse([px, py, px + r, py + r], fill=rr.choice(cols))


def smoke_plume(cx, cy, r, base, sky, seed, n=7):
    """Irregular smoke: clustered soft discs of varying size and shade,
    darker at the base, drifting up — never a single circle."""
    rr = random.Random(seed)
    for _ in range(n):
        ox = rr.randint(-r, r)
        oy = -rr.randint(0, int(r * 1.5))
        s = rr.randint(max(3, r // 3), r)
        col = _blend(base, sky, rr.uniform(0.0, 0.55))
        soft_disc(cx + ox, cy + oy, s, max(2, int(s * 0.65)), col, sky, steps=4)


def flame(cx, cy, r, sky):
    """Layered fire: red edge, orange mid, yellow core, white heart."""
    soft_disc(cx, cy, r, int(r * 0.8), (205, 62, 18), sky, steps=4)
    soft_disc(cx, cy - 1, int(r * 0.66), int(r * 0.55), (255, 140, 30), sky, steps=4)
    soft_disc(cx, cy - 2, int(r * 0.38), int(r * 0.32), (255, 210, 80), sky, steps=3)
    d.ellipse([cx - max(1, r // 4), cy - max(1, r // 4) - 2,
               cx + max(1, r // 4), cy + max(1, r // 4) - 2], fill=(255, 246, 205))


def embers(cx, cy, r, n, seed, sky):
    """Hot ash flecks rising above a fire (seeded, clipped by caller)."""
    rr = random.Random(seed)
    for _ in range(n):
        ex = cx + rr.randint(-r, r)
        ey = cy - rr.randint(0, r * 2)
        d.ellipse([ex - 1, ey - 1, ex + 1, ey + 1], fill=rr.choice(
            [(255, 180, 60), (255, 220, 120), (230, 90, 30)]))


def cloud_puff(cx, cy, s, sky, dark=(110, 112, 130)):
    """Textured cloud: lumpy white top, shaded underside."""
    for dx, dy, r in [(-s, 3, s // 2), (-s // 2, -2, s // 2 + 2), (0, -4, s // 2 + 3),
                      (s // 2, 0, s // 2 + 1), (s, 3, s // 2)]:
        soft_disc(cx + dx, cy + dy, r, max(2, r // 2 + 2), (255, 255, 255), sky, steps=4)
    soft_disc(cx, cy + 4, s, max(2, s // 3), dark, sky, steps=3)


def person(cx, base_y, hgt, shirt, skin=(222, 184, 150)):
    """A small figure with natural proportions, plus a ground shadow."""
    hd = max(3, hgt // 4)
    d.ellipse([cx - 5, base_y + 1, cx + 5, base_y + 3], fill=(70, 62, 55))
    d.ellipse([cx - hd // 2, base_y - hgt, cx + hd // 2, base_y - hgt + hd],
              fill=skin, outline=NAVY, width=1)
    d.polygon([(cx - hgt // 5, base_y - hgt + hd), (cx + hgt // 5, base_y - hgt + hd),
               (cx + hgt // 6, base_y), (cx - hgt // 6, base_y)], fill=shirt)


def palm(ix, iy, s, lean=6):
    """A palm with layered, drooping fronds — not a triangle."""
    d.line([(ix, iy), (ix + lean, iy - s)], fill=(120, 90, 60), width=2)
    top = (ix + lean, iy - s)
    for ang in (-70, -40, -10, 20, 50, 80):
        fx = top[0] + int((s * 0.7) * math.cos(math.radians(ang - 90)))
        fy = top[1] + int((s * 0.7) * math.sin(math.radians(ang - 90))) + 4
        d.line([top, (fx, fy)], fill=(46, 110, 62), width=2)
        d.line([(top[0] + (fx - top[0]) // 2, top[1] + (fy - top[1]) // 2),
                (fx, fy + 3)], fill=(70, 140, 80), width=1)


def cloud(cx, cy, s, sky):
    for dx, dy, r in [(-s, 2, s // 2), (0, -2, s // 2 + 2), (s, 2, s // 2)]:
        soft_disc(cx + dx, cy + dy, r, r // 2 + 2, (255, 255, 255), sky, steps=4)


def fold_shade(x, y, w, h, period=9, amp=0.16):
    """Cloth folds on a flag: sine-wave light/dark vertical bands."""
    px = img.load()
    for xx in range(max(0, x), min(W, x + w)):
        f = 1.0 + amp * math.sin(2 * math.pi * (xx - x) / period)
        for yy in range(max(0, y), min(H, y + h)):
            r, g, b = px[xx, yy]
            px[xx, yy] = (max(0, min(255, int(r * f))),
                          max(0, min(255, int(g * f))),
                          max(0, min(255, int(b * f))))


def hstripes(x, y, w, h, cols):
    n = len(cols)
    for i, c in enumerate(cols):
        d.rectangle([x, y + i * h // n, x + w, y + (i + 1) * h // n], fill=c)


def vstripes(x, y, w, h, cols):
    n = len(cols)
    for i, c in enumerate(cols):
        d.rectangle([x + i * w // n, y, x + (i + 1) * w // n, y + h], fill=c)


def flag(kind, x, y, w, h):
    """Small recognisable flag, drawn from scratch, thin outline."""
    d.rectangle([x, y, x + w, y + h], fill=(255, 255, 255), outline=NAVY, width=1)
    if kind == "us":
        hstripes(x + 1, y + 1, w - 2, h - 2, [(178, 34, 34), (255, 255, 255)] * 4)
        d.rectangle([x + 1, y + 1, x + w // 2, y + h // 2], fill=NAVY)
        for r in range(3):
            for c in range(4):
                d.ellipse([x + 5 + c * 9, y + 4 + r * 7, x + 8 + c * 9, y + 7 + r * 7],
                          fill=(255, 255, 255))
    elif kind == "china":
        d.rectangle([x + 1, y + 1, x + w - 1, y + h - 1], fill=(222, 41, 16))
        for sx, sy in [(8, 5), (16, 8), (16, 14), (8, 17)]:
            d.ellipse([x + sx, y + sy, x + sx + 4, y + sy + 4], fill=(255, 222, 0))
        d.ellipse([x + 4, y + 3, x + 12, y + 11], fill=(255, 222, 0))
    elif kind == "russia":
        hstripes(x + 1, y + 1, w - 2, h - 2, [(255, 255, 255), (0, 57, 166), (213, 0, 50)])
    elif kind == "iran":
        hstripes(x + 1, y + 1, w - 2, h - 2, [(35, 159, 64), (255, 255, 255), (218, 0, 0)])
        d.ellipse([x + w // 2 - 4, y + h // 2 - 4, x + w // 2 + 4, y + h // 2 + 4],
                  outline=(218, 0, 0), width=2)
    elif kind == "philippines":
        d.rectangle([x + 1, y + 1, x + w - 1, y + h // 2], fill=(0, 56, 168))
        d.rectangle([x + 1, y + h // 2, x + w - 1, y + h - 1], fill=(206, 17, 38))
        d.polygon([(x + 1, y + 1), (x + w // 2, y + h // 2), (x + 1, y + h - 1)],
                  fill=(255, 255, 255))
        d.ellipse([x + 6, y + h // 2 - 4, x + 14, y + h // 2 + 4], fill=(255, 215, 0))
    elif kind == "germany":
        hstripes(x + 1, y + 1, w - 2, h - 2, [(0, 0, 0), (221, 0, 0), (255, 204, 0)])
    elif kind == "norway":
        d.rectangle([x + 1, y + 1, x + w - 1, y + h - 1], fill=(186, 12, 47))
        d.rectangle([x + w // 3 - 3, y + 1, x + w // 3 + 5, y + h - 1], fill=(255, 255, 255))
        d.rectangle([x + 1, y + h // 2 - 4, x + w - 1, y + h // 2 + 4], fill=(255, 255, 255))
        d.rectangle([x + w // 3 - 1, y + 1, x + w // 3 + 3, y + h - 1], fill=(0, 32, 91))
        d.rectangle([x + 1, y + h // 2 - 2, x + w - 1, y + h // 2 + 2], fill=(0, 32, 91))
    elif kind == "ethiopia":
        hstripes(x + 1, y + 1, w - 2, h - 2, [(7, 137, 48), (252, 221, 9), (218, 0, 0)])
        d.ellipse([x + w // 2 - 6, y + h // 2 - 6, x + w // 2 + 6, y + h // 2 + 6],
                  fill=(15, 71, 175))
        d.ellipse([x + w // 2 - 2, y + h // 2 - 2, x + w // 2 + 2, y + h // 2 + 2],
                  fill=(252, 221, 9))
    elif kind == "eritrea":
        d.rectangle([x + 1, y + 1, x + w - 1, y + h - 1], fill=(18, 103, 70))
        d.polygon([(x + 1, y + 1), (x + w - 1, y + h // 2), (x + 1, y + h - 1)],
                  fill=(222, 41, 16))
        d.polygon([(x + 1, y + 1), (x + w - 1, y + h // 2), (x + 1, y + h - 1)],
                  outline=(0, 32, 91), width=1)
        d.ellipse([x + 8, y + h // 2 - 5, x + 18, y + h // 2 + 5], fill=(255, 215, 0))
    elif kind == "congo":
        d.rectangle([x + 1, y + 1, x + w - 1, y + h - 1], fill=(0, 127, 214))
        d.polygon([(x + 1, y + h - 1), (x + w - 1, y + 1), (x + w - 1, y + h // 3),
                   (x + w // 3, y + h - 1)], fill=(206, 17, 38))
        d.ellipse([x + 6, y + 4, x + 14, y + 12], fill=(255, 215, 0))
    elif kind == "eu":
        d.rectangle([x + 1, y + 1, x + w - 1, y + h - 1], fill=(0, 51, 153))
        for k in range(8):
            a = math.radians(45 * k)
            d.ellipse([x + w // 2 + 12 * math.cos(a) - 2, y + h // 2 + 9 * math.sin(a) - 2,
                       x + w // 2 + 12 * math.cos(a) + 2, y + h // 2 + 9 * math.sin(a) + 2],
                      fill=(255, 215, 0))
    elif kind == "palestine":
        hstripes(x + 1, y + 1, w - 2, h - 2, [(0, 0, 0), (255, 255, 255), (0, 122, 61)])
        d.polygon([(x + 1, y + 1), (x + w // 3, y + h // 2), (x + 1, y + h - 1)],
                  fill=(206, 17, 38))
    elif kind == "cook":
        d.rectangle([x + 1, y + 1, x + w - 1, y + h - 1], fill=(0, 0, 139))
        d.rectangle([x + 1, y + 1, x + w // 2, y + h // 2], fill=(255, 255, 255))
        d.line([x + 1, y + 1, x + w // 2, y + h // 2], fill=(200, 0, 0), width=2)
        d.line([x + w // 2, y + 1, x + 1, y + h // 2], fill=(200, 0, 0), width=2)
        for sx, sy in [(w - 14, 8), (w - 8, 16), (w - 18, 20)]:
            d.ellipse([x + sx, y + sy, x + sx + 4, y + sy + 4], fill=(255, 255, 255))
    fold_shade(x + 1, y + 1, w - 2, h - 2)


# ---------- paper ----------
vgrad(0, 0, W, H, (248, 243, 226), (236, 227, 203))
d.rectangle([5, 5, W - 6, H - 6], outline=NAVY, width=2)

# ---------- masthead: navy band, date box, white serif date ----------
d.rectangle([0, 0, W, 118], fill=NAVY)
d.rectangle([0, 118, W, 122], fill=(212, 175, 55))
# date box, left: red NOV, big 18, WED 2026
d.rectangle([10, 8, 98, 108], fill=(255, 255, 255), outline=(212, 175, 55), width=1)
d.rectangle([10, 8, 98, 34], fill=RED)
d.text((54 - d.textlength("NOV", font=font(SANSB, 15)) / 2, 12), "NOV",
       font=font(SANSB, 15), fill=(255, 255, 255))
d.text((54 - d.textlength("18", font=font(SERIFB, 42)) / 2, 36), "18",
       font=font(SERIFB, 42), fill=NAVY)
d.text((54 - d.textlength("WED · 2026", font=font(SANSB, 9)) / 2, 88), "WED · 2026",
       font=font(SANSB, 9), fill=GREY)
d.text((112, 10), "THE WORLD'S NEWS IN ONE PICTURE", font=font(SANSB, 13),
       fill=(212, 175, 55))
_right = "43 STORIES  ·  6 CONTINENTS  ·  ONE PAGE"
d.text((W - 16 - d.textlength(_right, font=font(SANSB, 13)), 10), _right,
       font=font(SANSB, 13), fill=(212, 175, 55))
# giant date, auto-fit so the longer Wednesday date still fits
_date = "Wednesday 18 November 2026"
_dsize = 54
while d.textlength(_date, font=font(SERIFB, _dsize)) > W - 112 - 16 and _dsize > 40:
    _dsize -= 1
d.text((112, 34), _date, font=font(SERIFB, _dsize), fill=(255, 255, 255))
_sub = "Everything on this page happened, or was first reported, on Wednesday 18 November 2026."
d.text((112, 92), _sub, font=font(SERIF, 14), fill=(198, 206, 218))

# ---------- generated photos: real photographs composited into all 13 panels ----------
# The photos live in assets/ (committed to the repo) so the generator
# runs offline and deterministically: same files, same fixed crops,
# same bytes every run. Each entry is (file, fy, zoom, fx, bright):
# fy is the fraction of the spare vertical range to skip when
# centre-cropping the photo to the panel's wide aspect ratio; zoom is
# the fraction of the photo's width to keep (zoom < 1 crops tighter
# onto the main subject, so it reads big and clear even in a 60px-tall
# panel); fx is the horizontal centre of that crop as a fraction of
# the photo width; bright lifts dark photos. Subjects were located by
# inspecting each source photo: explosion + warship, the two leaders'
# faces, the Capitol dome, the nurse + child, the PPE worker, the
# cyclone eye, the lit tents, the driverless car, the frosted freezers
# + warning sign, the dish + Earth, the falling red chart, the
# launcher, the troops + flags.
PHOTOS = {
    "gulf": ("panel1-gulf.jpg", 0.65, 0.85, 0.50, 1.05),
    "apec": ("panel2-apec.jpg", 0.35, 0.90, 0.50, 1.00),
    "senate": ("panel3-capitol.jpg", 0.15, 0.90, 0.50, 1.00),
    "measles": ("panel4-measles.jpg", 0.55, 0.55, 0.45, 1.00),
    "ebola": ("panel5-ebola.jpg", 0.45, 0.60, 0.50, 1.00),
    "cyclone": ("panel6-xavier.jpg", 0.50, 0.70, 0.50, 1.00),
    "gaza": ("panel7-gaza.jpg", 0.50, 0.70, 0.65, 1.05),
    "waymo": ("panel8-waymo.jpg", 0.35, 0.65, 0.65, 1.00),
    "cyber": ("panel9-freezer.jpg", 0.30, 0.55, 0.30, 1.14),
    "voyager": ("panel10-voyager.jpg", 0.30, 0.70, 0.62, 1.18),
    "markets": ("panel11-markets.jpg", 0.35, 0.70, 0.50, 1.08),
    "patriot": ("panel12-patriot.jpg", 0.45, 0.70, 0.50, 1.00),
    "border": ("panel13-border.jpg", 0.55, 0.85, 0.50, 1.00),
}
_photo_cache = {}


def paste_photo(kind, x, y, w, h):
    fname, fy, zoom, fx, bright = PHOTOS[kind]
    if kind not in _photo_cache:
        _photo_cache[kind] = Image.open(
            os.path.join(BASE, "assets", fname)).convert("RGB")
    src = _photo_cache[kind]
    sw, sh = src.size
    target = w / h
    # tight crop onto the subject: keep zoom of the width, then fit
    # the panel aspect inside that window
    cw = int(sw * zoom)
    ch = int(cw / target)
    if ch > sh:
        ch, cw = sh, int(sh * target)
    left = int(fx * sw - cw / 2)
    left = max(0, min(sw - cw, left))
    top = int((sh - ch) * fy) if ch < sh else 0
    crop = src.crop((left, top, left + cw, top + ch)).resize((w, h), Image.LANCZOS)
    # sharpen + lift colour/contrast so the photo still reads at 60px
    if bright != 1.0:
        crop = ImageEnhance.Brightness(crop).enhance(bright)
    crop = ImageEnhance.Color(crop).enhance(1.18)
    crop = ImageEnhance.Contrast(crop).enhance(1.12)
    crop = crop.filter(ImageFilter.UnsharpMask(radius=2, percent=85, threshold=2))
    img.paste(crop, (x, y))


# ---------- pictograms: each fills its panel edge to edge ----------
def pic(kind, x, y, w, h):
    if kind in PHOTOS:
        paste_photo(kind, x, y, w, h)
        return
    if kind == "gulf":
        # the Gulf at night: dark sky above, a gold horizon, missile
        # trails streaking diagonally down to the strike on Qeshm
        mgrad(x, y, w, h, [(0.0, (14, 18, 42)), (0.45, (52, 42, 74)),
                           (0.7, (140, 82, 66)), (1.0, (214, 132, 74))])
        sun_glow(x + w - 60, y + 32, 5, (140, 82, 66))
        cloud_puff(x + 50, y + 9, 10, (52, 42, 74))
        cloud_puff(x + w - 130, y + 6, 8, (52, 42, 74), dark=(140, 110, 120))
        # a distant ship silhouette on the horizon, lights on
        d.rectangle([x + w - 168, y + 38, x + w - 136, y + 44], fill=(70, 60, 66))
        d.rectangle([x + w - 158, y + 32, x + w - 146, y + 38], fill=(70, 60, 66))
        for lx_ in (x + w - 164, x + w - 154, x + w - 144):
            d.rectangle([lx_, y + 40, lx_ + 2, y + 42], fill=(255, 210, 120))
        # diagonal missile trails streaking across the night sky,
        # like the reference's Gulf shot: bright heads, gold tails
        missile_trail(x + w - 30, y + 4, x + w // 2 + 30, y + 28, (52, 42, 74))
        missile_trail(x + w - 120, y + 2, x + w // 2 - 6, y + 26, (52, 42, 74))
        missile_trail(x + w - 210, y + 6, x + w // 2 + 44, y + 30, (52, 42, 74))
        # fighter jets with contrails over the open water
        for jx, jy in [(x + 56, y + 34), (x + 260, y + 32)]:
            d.line([(jx - 34, jy + 6), (jx - 6, jy + 2)], fill=(255, 255, 255), width=2)
            d.polygon([(jx - 6, jy), (jx + 10, jy + 2), (jx - 6, jy + 5), (jx - 2, jy + 2)],
                      fill=(60, 60, 70))
            d.polygon([(jx - 2, jy - 3), (jx + 2, jy + 2), (jx - 4, jy + 3)], fill=(60, 60, 70))
        # irregular smoke plumes rising from the strike on Qeshm,
        # with hot ash drifting up
        smoke_plume(x + w // 2 + 14, y + 30, 9, (48, 42, 40), (70, 58, 80), 11, n=8)
        smoke_plume(x + w // 2 - 34, y + 34, 6, (70, 62, 58), (70, 58, 80), 23, n=5)
        embers(x + w // 2 + 14, y + 28, 8, 7, 31, (70, 58, 80))
        # radar tower on the Iranian coast, right of the sun glow
        d.rectangle([x + w - 78, y + 6, x + w - 74, y + 22], fill=(90, 85, 80))
        d.ellipse([x + w - 83, y + 2, x + w - 69, y + 10], fill=(200, 200, 200),
                  outline=(90, 85, 80), width=1)
        # sea: dark multi-stop water, firelight reflected in wobbly
        # streaks, wave highlights catching the dusk light
        mgrad(x, y + h - 30, w, 30, [(0.0, (52, 80, 100)), (0.5, (30, 56, 76)),
                                     (1.0, (14, 34, 52))])
        # firelight from the Qeshm strike reflected on the dark water
        for rw_, rwid, off in [(y + h - 26, 46, 0), (y + h - 20, 36, 3),
                               (y + h - 14, 26, -2), (y + h - 8, 18, 2)]:
            d.line([(x + w // 2 + 14 - rwid // 2 + off, rw_),
                    (x + w // 2 + 14 + rwid // 2 + off, rw_)], fill=(255, 170, 70), width=2)
        speckle(x + 6, y + h - 28, w - 12, 26, 60, 41,
                [(190, 225, 230), (255, 180, 110), (120, 150, 170)], r=1)
        for wy in (y + h - 22, y + h - 14, y + h - 7):
            for wx in range(x + 6, x + w - 12, 26):
                d.arc([wx, wy - 3, wx + 14, wy + 3], 180, 360, fill=(190, 225, 230), width=1)
        # Iran: dark sandy coast along the top edge, at night
        d.polygon([(x, y), (x + w, y), (x + w, y + 18), (x + w * 0.7, y + 26),
                   (x + w * 0.4, y + 16), (x, y + 22)], fill=(176, 146, 108),
                  outline=(150, 120, 80))
        d.text((x + 10, y + 2), "IRAN", font=font(SANSB, 9), fill=(110, 85, 50))
        # Qeshm Island: a long low island mid-frame, with the strike flash
        d.polygon([(x + w // 3, y + 34), (x + w * 0.72, y + 30), (x + w * 0.78, y + 38),
                   (x + w // 3 + 6, y + 42)], fill=(196, 168, 120), outline=(120, 95, 60))
        d.text((x + w // 2 - 16, y + 44), "QESHM", font=font(SANSB, 8), fill=(255, 255, 255))
        flame(x + w // 2 + 14, y + 30, 11, (238, 148, 92))
        embers(x + w // 2 + 14, y + 26, 7, 5, 47, (238, 148, 92))
        # missile trails arcing from the island toward the bases:
        # a quadratic bezier from the flash point to each base marker
        fx0, fy0 = x + w // 2 + 14, y + 30
        for tx, ty in [(x + 34, y + h - 12), (x + w - 40, y + h - 10)]:
            cx0, cy0 = (fx0 + tx) // 2, min(fy0, ty) - 22
            pts = []
            for t in range(0, 21):
                tt = t / 20
                bx = (1 - tt) ** 2 * fx0 + 2 * (1 - tt) * tt * cx0 + tt ** 2 * tx
                by = (1 - tt) ** 2 * fy0 + 2 * (1 - tt) * tt * cy0 + tt ** 2 * ty
                pts.append((bx, by))
            d.line(pts, fill=(255, 255, 255), width=2)
            d.ellipse([tx - 3, ty - 3, tx + 3, ty + 3], fill=(255, 255, 255))
        # base markers: small red stars at Kuwait (left) and Bahrain (right),
        # labels above the stars so nothing is cut off at the picture edge
        for bx, by, lab in [(x + 30, y + h - 12, "KUWAIT"), (x + w - 44, y + h - 10, "BAHRAIN")]:
            d.polygon([(bx, by - 6), (bx + 2, by - 1), (bx + 6, by), (bx + 2, by + 2),
                       (bx + 3, by + 6), (bx, by + 3), (bx - 3, by + 6), (bx - 2, by + 2),
                       (bx - 6, by), (bx - 2, by - 1)], fill=(200, 30, 30))
            d.text((bx - 16, by - 13), lab, font=font(SANSB, 7), fill=(255, 255, 255))
        # a tanker crossing the strait, low in the frame
        d.rectangle([x + w // 2 - 26, y + h - 16, x + w // 2 + 26, y + h - 8], fill=(90, 60, 50))
        d.rectangle([x + w // 2 - 6, y + h - 24, x + w // 2 + 10, y + h - 16], fill=(200, 200, 200))
        d.rectangle([x + w // 2 + 12, y + h - 22, x + w // 2 + 16, y + h - 16], fill=(60, 60, 60))
        # a warship patrolling the strait, mid-left, with mast and radar
        d.rectangle([x + 56, y + h - 26, x + 96, y + h - 16], fill=(96, 104, 112),
                    outline=NAVY, width=1)
        d.rectangle([x + 66, y + h - 34, x + 80, y + h - 26], fill=(120, 128, 136),
                    outline=NAVY, width=1)
        d.line([(x + 73, y + h - 40), (x + 73, y + h - 34)], fill=NAVY, width=2)
        d.ellipse([x + 69, y + h - 44, x + 77, y + h - 38], fill=(200, 200, 200),
                  outline=NAVY, width=1)
        d.rectangle([x + 60, y + h - 25, x + 66, y + h - 21], fill=(200, 210, 220))
        # hull shading, a gun turret, and the ship's dark reflection
        d.rectangle([x + 56, y + h - 19, x + 96, y + h - 16], fill=(70, 78, 86))
        d.rectangle([x + 82, y + h - 30, x + 92, y + h - 26], fill=(80, 88, 96),
                    outline=NAVY, width=1)
        for wy in (y + h - 14, y + h - 10):
            d.line([(x + 58, wy), (x + 94, wy)], fill=(60, 68, 78), width=1)
        # foreground foam breaking along the bottom edge
        for wx in range(x + 10, x + w - 16, 34):
            d.arc([wx, y + h - 5, wx + 12, y + h - 1], 180, 360, fill=(230, 244, 248),
                  width=1)
        # second, smaller tanker on the far right, with a smoke puff
        d.rectangle([x + w - 110, y + h - 16, x + w - 74, y + h - 8], fill=(110, 80, 70))
        d.rectangle([x + w - 98, y + h - 22, x + w - 86, y + h - 16], fill=(210, 210, 210))
        soft_disc(x + w - 92, y + h - 26, 6, 4, (200, 200, 205), (20, 88, 108), steps=3)
        # whitecaps breaking at the warship's bow
        for wx in (x + 100, x + 112):
            d.arc([wx, y + h - 10, wx + 10, y + h - 6], 180, 360, fill=(220, 240, 245),
                  width=1)
    elif kind == "apec":
        # APEC summit in Shenzhen: tower skyline, a long summit table,
        # Chinese and Russian flags on poles, folders and microphones
        mgrad(x, y, w, h, [(0.0, (242, 206, 148)), (0.5, (210, 168, 112)),
                           (1.0, (186, 140, 96))])
        # hanging lamps glowing warm over the table (kept well inside)
        for lampx in (x + w // 2 - 60, x + w // 2 + 60):
            d.line([(lampx, y + 1), (lampx, y + 7)], fill=(120, 90, 50), width=1)
            soft_disc(lampx, y + 10, 4, 4, (255, 220, 130), (242, 206, 148), steps=3)
            d.ellipse([lampx - 3, y + 7, lampx + 3, y + 13], fill=(255, 230, 150))
        cloud_puff(x + 60, y + 8, 9, (242, 206, 148))
        # a fainter second row of towers behind the skyline
        for tx, th in [(x + 20, 18), (x + 48, 14), (x + 84, 20), (x + w - 88, 16),
                       (x + w - 56, 20), (x + w - 26, 14)]:
            d.rectangle([tx, y + 34 - th, tx + 12, y + 34], fill=(170, 182, 200))
        # Shenzhen skyline along the back
        for tx, th in [(x + 8, 26), (x + 34, 36), (x + 62, 22), (x + w - 70, 30),
                       (x + w - 40, 38), (x + w - 14, 24)]:
            d.rectangle([tx, y + 34 - th, tx + 16, y + 34], fill=(120, 135, 160))
            for wy in range(y + 38 - th, y + 32, 8):
                d.rectangle([tx + 3, wy, tx + 6, wy + 3], fill=(255, 230, 140))
                d.rectangle([tx + 10, wy, tx + 13, wy + 3], fill=(255, 230, 140))
        d.rectangle([x, y + 34, x + w, y + 38], fill=(120, 84, 52))
        for wx_ in range(x + 10, x + w - 10, 34):
            d.line([(wx_, y + 2), (wx_, y + 34)], fill=(150, 108, 66), width=1)
        # flags on poles behind the table
        flag("china", x + 14, y + 6, 44, 26)
        d.line([(x + 36, y + 6), (x + 36, y + 34)], fill=NAVY, width=2)
        flag("russia", x + w - 58, y + 6, 44, 26)
        d.line([(x + w - 36, y + 6), (x + w - 36, y + 34)], fill=NAVY, width=2)
        # APEC banner strung between the flags
        d.rectangle([x + w // 2 - 44, y + 8, x + w // 2 + 44, y + 20], fill=BLUE,
                    outline=(255, 255, 255), width=1)
        d.text((x + w // 2 - 14, y + 10), "APEC", font=font(SANSB, 9), fill=(255, 255, 255))
        # delegates seated behind the table: varied heads, hair, suits,
        # and a white name card each on the table edge
        for hx_, skin, hair, suit in [
                (x + 72, (222, 184, 150), (40, 32, 28), (40, 48, 70)),
                (x + 138, (200, 162, 122), (20, 20, 22), (70, 40, 44)),
                (x + 182, (226, 190, 158), (90, 80, 70), (36, 56, 44)),
                (x + 244, (205, 168, 130), (30, 30, 34), (52, 44, 66))]:
            d.ellipse([hx_ - 5, y + 26, hx_ + 5, y + 36], fill=skin, outline=NAVY, width=1)
            d.pieslice([hx_ - 5, y + 26, hx_ + 5, y + 32], 180, 360, fill=hair)
            d.pieslice([hx_ - 11, y + 34, hx_ + 11, y + 48], 180, 360, fill=suit)
            d.line([(hx_ - 1, y + 36), (hx_ - 1, y + 42)], fill=(255, 255, 255), width=1)
        # the two central leaders rise and shake hands across the
        # table, like the airport-welcome shot in the reference:
        # arms reaching to the middle, hands clasped
        d.line([(x + 138, y + 38), (x + 160, y + 40)], fill=(70, 40, 44), width=3)
        d.line([(x + 182, y + 38), (x + 160, y + 40)], fill=(36, 56, 44), width=3)
        d.ellipse([x + 155, y + 36, x + 165, y + 44], fill=(222, 184, 150),
                  outline=NAVY, width=1)
        # the long table: wood top, dark front, red carpet below
        d.rectangle([x + 6, y + 40, x + w - 6, y + h - 14], fill=(146, 102, 66))
        d.rectangle([x + 6, y + 40, x + w - 6, y + 46], fill=(190, 140, 90))
        # wood grain on the table front, and its shadow under the top
        d.line([(x + 6, y + 47), (x + w - 6, y + 47)], fill=(110, 74, 44), width=1)
        for gy in (y + 54, y + 60, y + 66):
            d.line([(x + 10, gy), (x + w - 10, gy)], fill=(122, 84, 52), width=1)
        for gx_ in (x + 60, x + 150, x + 240):
            d.line([(gx_, y + 48), (gx_, y + h - 16)], fill=(122, 84, 52), width=1)
        d.rectangle([x + 6, y + h - 14, x + w - 6, y + h], fill=(150, 50, 45))
        # white name cards standing on the table edge, one per delegate
        for hx_ in (x + 72, x + 138, x + 182, x + 244):
            d.rectangle([hx_ - 9, y + 41, hx_ + 9, y + 46], fill=(250, 248, 240),
                        outline=NAVY, width=1)
            d.line([(hx_ - 6, y + 44), (hx_ + 6, y + 44)], fill=NAVY, width=1)
        # four place settings: folder, glass, microphone
        for px_ in (x + 30, x + w // 3 + 8, x + 2 * w // 3 - 6, x + w - 52):
            d.rectangle([px_, y + 48, px_ + 26, y + 58], fill=(240, 235, 220),
                        outline=NAVY, width=1)
            d.line([(px_ + 4, y + 51), (px_ + 22, y + 51)], fill=NAVY, width=1)
            d.line([(px_ + 4, y + 55), (px_ + 18, y + 55)], fill=NAVY, width=1)
            d.rectangle([px_ + 30, y + 50, px_ + 36, y + 58], fill=(200, 225, 240),
                        outline=NAVY, width=1)
            d.ellipse([px_ + 12, y + 42, px_ + 18, y + 48], fill=(40, 40, 40))
            d.line([(px_ + 15, y + 48), (px_ + 15, y + 54)], fill=(40, 40, 40), width=2)
        d.text((x + w // 2 - 24, y + h - 12), "SHENZHEN", font=font(SANSB, 8),
               fill=(255, 255, 255))
    elif kind == "senate":
        # Alaska Senate race: US Capitol dome, a ballot box, vote bars
        mgrad(x, y, w, h, [(0.0, (252, 196, 138)), (0.45, (236, 164, 140)),
                           (1.0, (168, 128, 152))])
        cloud_puff(x + 70, y + 8, 8, (252, 196, 138))
        cloud_puff(x + w - 120, y + 5, 7, (252, 196, 138), dark=(150, 120, 140))
        sun_glow(x + 18, y + 32, 5, (252, 196, 138))
        # Alaska, top-right, with a star on Anchorage
        ak = [(x + w - 96, y + 22), (x + w - 88, y + 8), (x + w - 66, y + 6),
              (x + w - 44, y + 10), (x + w - 26, y + 8), (x + w - 12, y + 14),
              (x + w - 20, y + 26), (x + w - 40, y + 30), (x + w - 62, y + 28),
              (x + w - 80, y + 30), (x + w - 92, y + 28)]
        d.polygon(ak, fill=(170, 200, 235), outline=(60, 90, 140), width=1)
        d.ellipse([x + w - 52, y + 14, x + w - 46, y + 20], fill=(200, 40, 40))
        flag("us", x + 10, y + 6, 48, 28)
        # Capitol dome, pale stone
        d.pieslice([x + w // 2 - 34, y + 2, x + w // 2 + 34, y + 46], 180, 360,
                   fill=(240, 238, 228), outline=(150, 145, 130), width=1)
        d.rectangle([x + w // 2 - 40, y + 24, x + w // 2 + 40, y + h - 26],
                    fill=(232, 228, 214), outline=(150, 145, 130), width=1)
        # stone texture on the dome, and windows some lit, some dark
        speckle(x + w // 2 - 34, y + 2, 68, 22, 40, 71,
                [(225, 222, 210), (200, 196, 180)], r=1)
        for wx_, lit in [(x + w // 2 - 32, False), (x + w // 2 - 20, True),
                         (x + w // 2 + 12, True), (x + w // 2 + 26, False)]:
            d.rectangle([wx_, y + 32, wx_ + 6, y + 40],
                        fill=(255, 210, 110) if lit else (150, 146, 132))
        for cx in (x + w // 2 - 28, x + w // 2 - 4, x + w // 2 + 20):
            d.rectangle([cx, y + 30, cx + 8, y + h - 26], fill=(210, 204, 186),
                        outline=(150, 145, 130), width=1)
        d.rectangle([x + w // 2 - 3, y - 2, x + w // 2 + 3, y + 6], fill=(200, 180, 120))
        # steps at the base of the Capitol and bunting from the flag
        for sstep in range(3):
            d.rectangle([x + w // 2 - 46 + sstep * 3, y + h - 26 + sstep * 3,
                         x + w // 2 + 46 - sstep * 3, y + h - 23 + sstep * 3],
                        fill=(200, 194, 176))
        d.line([(x + 60, y + 10), (x + 122, y + 8)], fill=(178, 34, 34), width=1)
        # a crowd gathered on the Capitol steps at dusk, varied heights
        # and clothes, each with a shadow on the stone
        for cx_, ch, cshirt in [
                (x + w // 2 - 40, 12, (90, 60, 70)), (x + w // 2 - 27, 10, (60, 80, 110)),
                (x + w // 2 - 14, 13, (70, 60, 70)), (x + w // 2 - 1, 9, (120, 90, 60)),
                (x + w // 2 + 12, 12, (50, 70, 60)), (x + w // 2 + 25, 10, (100, 60, 80)),
                (x + w // 2 + 38, 13, (60, 60, 90))]:
            person(cx_, y + h - 2, ch, cshirt)
        for bx_ in range(x + 66, x + 120, 14):
            d.polygon([(bx_, y + 10), (bx_ + 8, y + 10), (bx_ + 4, y + 17)],
                      fill=(30, 80, 160))
        # confetti drifting over the steps in the foreground
        speckle(x + w // 2 - 46, y + h - 26, 92, 22, 26, 83,
                [(178, 34, 34), (30, 80, 160), (255, 255, 255)], r=1)
        # ballot box in front, a ballot sliding into its slot
        d.rectangle([x + 14, y + h - 30, x + 66, y + h - 6], fill=(70, 90, 130),
                    outline=NAVY, width=1)
        d.rectangle([x + 14, y + h - 30, x + 66, y + h - 22], fill=(50, 66, 100))
        d.rectangle([x + 30, y + h - 30, x + 50, y + h - 28], fill=(20, 20, 30))
        d.polygon([(x + 34, y + h - 40), (x + 52, y + h - 40), (x + 48, y + h - 30),
                   (x + 38, y + h - 30)], fill=(255, 255, 255), outline=NAVY, width=1)
        d.line([(x + 38, y + h - 37), (x + 48, y + h - 37)], fill=NAVY, width=1)
        d.line([(x + 38, y + h - 34), (x + 46, y + h - 34)], fill=NAVY, width=1)
        # vote bars, right side: blue 50.1% over red
        d.text((x + w - 108, y + h - 34), "50.1%", font=font(SANSB, 12), fill=BLUE)
        d.rectangle([x + w - 108, y + h - 20, x + w - 8, y + h - 12], fill=(220, 220, 220),
                    outline=NAVY, width=1)
        d.rectangle([x + w - 108, y + h - 20, x + w - 58, y + h - 12], fill=BLUE)
        d.rectangle([x + w - 58, y + h - 20, x + w - 8, y + h - 12], fill=(200, 60, 60))
    elif kind == "measles":
        # a US map with red case dots spreading, a clinic cross at right
        vgrad(x, y, w, h, (238, 236, 228), (214, 208, 192))
        # simplified contiguous US outline, fitted to the small panel
        us = [(x + 14, y + 14), (x + 50, y + 8), (x + 92, y + 10), (x + 126, y + 6),
              (x + 160, y + 12), (x + 172, y + 22), (x + 152, y + 26), (x + 156, y + 38),
              (x + 136, y + 44), (x + 128, y + 52), (x + 102, y + 46), (x + 86, y + 52),
              (x + 60, y + 48), (x + 34, y + 44), (x + 18, y + 34), (x + 10, y + 24)]
        d.polygon(us, fill=(196, 214, 170), outline=(90, 110, 70), width=1)
        d.line([(x + 10, y + 24), (x + 14, y + 14)], fill=(248, 240, 210), width=1)
        # land texture, then case dots with a hot glow on the biggest cluster
        speckle(x + 14, y + 8, 150, 44, 50, 91, [(180, 200, 155), (210, 226, 185)], r=1)
        soft_disc(x + 98, y + 29, 12, 9, (255, 90, 70), (196, 214, 170), steps=3)
        for dx, dy, r in [(x + 83, y + 24, 4), (x + 98, y + 29, 5), (x + 73, y + 31, 3),
                          (x + 108, y + 20, 3), (x + 88, y + 37, 4), (x + 119, y + 31, 3),
                          (x + 62, y + 24, 3), (x + 79, y + 17, 2)]:
            d.ellipse([dx - r, dy - r, dx + r, dy + r], fill=(200, 30, 30))
        # a rising case chart as an inset, top-left
        d.rectangle([x + 4, y + 2, x + 50, y + 22], fill=(255, 255, 255), outline=NAVY,
                    width=1)
        for bi, bh in enumerate([3, 6, 9, 12]):
            bx0 = x + 10 + bi * 9
            d.rectangle([bx0, y + 18 - bh, bx0 + 6, y + 18], fill=(200, 30, 30))
        # (state labels were tried here; at this panel size they collide
        # with the clinic, the ambulance and the case-count tag, so the
        # map stays unlabelled and clean)
        # a small clinic at bottom-left and an ambulance beside it
        d.rectangle([x + 6, y + h - 18, x + 36, y + h - 4], fill=(255, 255, 255),
                    outline=NAVY, width=1)
        d.rectangle([x + 6, y + h - 18, x + 36, y + h - 12], fill=(200, 60, 60))
        d.rectangle([x + 18, y + h - 12, x + 24, y + h - 4], fill=(200, 60, 60))
        d.rectangle([x + 40, y + h - 16, x + 74, y + h - 6], fill=(255, 255, 255),
                    outline=NAVY, width=1)
        d.rectangle([x + 44, y + h - 13, x + 50, y + h - 9], fill=(200, 30, 30))
        d.ellipse([x + 46, y + h - 6, x + 52, y + h - 2], fill=(30, 30, 30))
        d.ellipse([x + 64, y + h - 6, x + 70, y + h - 2], fill=(30, 30, 30))
        # clinic cross sign, bottom-right
        d.rectangle([x + w - 52, y + h - 34, x + w - 12, y + h - 8], fill=(255, 255, 255),
                    outline=NAVY, width=1)
        d.rectangle([x + w - 38, y + h - 30, x + w - 26, y + h - 12], fill=(200, 30, 30))
        d.rectangle([x + w - 46, y + h - 24, x + w - 18, y + h - 18], fill=(200, 30, 30))
        # the case count, as a tag top-right
        d.rectangle([x + w - 76, y + 6, x + w - 6, y + 20], fill=(255, 255, 255),
                    outline=RED, width=1)
        d.text((x + w - 72, y + 8), "5,412", font=font(SANSB, 9), fill=RED)
    elif kind == "ebola":
        # a clinic in the Congo: warm wall, red roof, virus at right
        vgrad(x, y, w, h, (244, 224, 220), (232, 200, 196))
        d.rectangle([x, y + h - 12, x + w, y + h], fill=(190, 160, 140))
        sun_glow(x + w - 90, y + 30, 6, (244, 224, 220))
        soft_disc(x + w // 2, y + h - 14, 26, 10, (255, 200, 110), (232, 200, 196), steps=4)
        d.polygon([(x + w // 2 - 14, y + h - 12), (x + w // 2 + 14, y + h - 12),
                   (x + w // 2 + 22, y + h), (x + w // 2 - 22, y + h)], fill=(210, 180, 150))
        d.rectangle([x + w // 2 - 40, y + 12, x + w // 2 + 40, y + h - 12], fill=(252, 252, 248),
                    outline=(180, 170, 160), width=1)
        d.polygon([(x + w // 2 - 46, y + 12), (x + w // 2, y + 2), (x + w // 2 + 46, y + 12)],
                  fill=(178, 44, 40))
        for wx0 in (x + w // 2 - 37, x + w // 2 + 31):
            d.rectangle([wx0, y + 20, wx0 + 6, y + 26], fill=(255, 220, 120))
        d.rectangle([x + w // 2 - 6, y + 18, x + w // 2 + 6, y + 30], fill=(200, 40, 40))
        d.rectangle([x + w // 2 - 12, y + 22, x + w // 2 + 12, y + 26], fill=(200, 40, 40))
        d.rectangle([x + w // 2 - 20, y + 32, x + w // 2 + 20, y + h - 12], fill=(120, 70, 60))
        d.rectangle([x + w // 2 - 20, y + 32, x + w // 2 + 20, y + 35], fill=(150, 95, 80))
        for wy in (y + 16, y + 24):
            d.rectangle([x + w // 2 - 28, wy, x + w // 2 - 22, wy + 4], fill=(150, 190, 220))
            d.rectangle([x + w // 2 + 22, wy, x + w // 2 + 28, wy + 4], fill=(150, 190, 220))
        # a health worker in white PPE beside the clinic door
        d.ellipse([x + w // 2 + 24, y + h - 32, x + w // 2 + 30, y + h - 26],
                  fill=(240, 210, 180), outline=NAVY, width=1)
        d.rectangle([x + w // 2 + 22, y + h - 26, x + w // 2 + 32, y + h - 12],
                    fill=(250, 250, 250), outline=(80, 120, 180), width=1)
        d.rectangle([x + w // 2 + 22, y + h - 12, x + w // 2 + 32, y + h - 6],
                    fill=(80, 120, 180))
        # a second worker in blue PPE, ground texture, and a leafy plant
        d.ellipse([x + w // 2 - 34, y + h - 30, x + w // 2 - 28, y + h - 24],
                  fill=(210, 180, 140), outline=NAVY, width=1)
        d.rectangle([x + w // 2 - 36, y + h - 24, x + w // 2 - 26, y + h - 12],
                    fill=(90, 130, 190), outline=(60, 90, 150), width=1)
        d.rectangle([x + w // 2 - 36, y + h - 12, x + w // 2 - 26, y + h - 6],
                    fill=(60, 90, 150))
        speckle(x + 6, y + h - 12, w - 12, 10, 40, 97, [(170, 140, 120), (210, 180, 150)],
                r=1)
        palm(x + 66, y + h - 6, 10, lean=4)
        flag("congo", x + 8, y + 6, 56, 32)
        for tx, ty in [(x + 38, y + h - 24)]:
            d.polygon([(tx, ty), (tx + 5, ty - 10), (tx + 10, ty)], fill=(60, 130, 70))
            d.rectangle([tx + 4, ty, tx + 6, ty + 12], fill=(120, 90, 60))
        for fx_ in range(x + 8, x + 60, 12):
            d.line([(fx_, y + h - 12), (fx_, y + h - 6)], fill=(150, 120, 90), width=1)
        d.line([(x + 8, y + h - 9), (x + 60, y + h - 9)], fill=(150, 120, 90), width=1)
        # a white treatment tent at the left edge of the yard
        d.polygon([(x + 8, y + h - 6), (x + 21, y + h - 22), (x + 34, y + h - 6)],
                  fill=(250, 248, 240), outline=(120, 110, 90), width=1)
        d.rectangle([x + 18, y + h - 12, x + 24, y + h - 6], fill=(200, 40, 40))
        # case dots scattered on the ground by the path
        for dx, dy in [(x + w - 58, y + h - 8), (x + w - 48, y + h - 6),
                       (x + w - 66, y + h - 5)]:
            d.ellipse([dx - 2, dy - 2, dx + 2, dy + 2], fill=(200, 30, 30))
        d.rectangle([x + w - 72, y + 6, x + w - 6, y + 20], fill=(255, 255, 255),
                    outline=RED, width=1)
        d.text((x + w - 68, y + 8), "11,000+", font=font(SANSB, 9), fill=RED)
        # the virus: spiked red ball, lower-right
        cx, cy, r = x + w - 32, y + h // 2 + 10, 14
        soft_disc(cx, cy, 20, 20, (255, 90, 70), (232, 200, 196), steps=3)
        for ang in range(0, 360, 45):
            dx, dy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            d.line([cx + dx * r, cy + dy * r, cx + dx * (r + 8), cy + dy * (r + 8)],
                   fill=RED, width=3)
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(190, 30, 30))
        d.ellipse([cx - r + 3, cy - r + 2, cx - 2, cy - 2], fill=(230, 90, 80))
        d.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(255, 255, 255))
    elif kind == "cyclone":
        # a Category 5 spiral over the Pacific, small islands below
        vgrad(x, y, w, h, (96, 116, 160), (52, 74, 118))
        vgrad(x, y + h - 18, w, 18, (20, 60, 90), (10, 40, 65))
        for wy in (y + h - 12, y + h - 6):
            for wx in range(x + 6, x + w - 12, 24):
                d.arc([wx, wy - 2, wx + 12, wy + 2], 180, 360, fill=(190, 225, 235), width=1)
        # spiral arms: thick concentric arcs shrinking toward the eye,
        # seen from above like the reference's cyclone shot
        cx, cy = x + w // 2, y + h // 2 - 6
        soft_disc(cx, cy, 12, 12, (255, 240, 170), (52, 74, 118), steps=3)
        for rr, a0, a1 in [(34, 20, 200), (26, 160, 340), (18, 300, 120), (10, 80, 260)]:
            d.arc([cx - rr, cy - rr, cx + rr, cy + rr], a0, a1, fill=(255, 255, 255), width=8)
        d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=(255, 235, 150))
        d.ellipse([cx - 3, cy - 3, cx + 3, cy + 3], fill=(255, 255, 255))
        # wind streaks at the edges
        for sx, sy in [(x + 12, y + 12), (x + w - 30, y + 16), (x + 20, y + h - 30),
                       (x + w - 40, y + h - 28)]:
            d.line([(sx, sy), (sx + 18, sy + 3)], fill=(255, 255, 255), width=2)
        # storm clouds crowding the top corners, rain slanting down
        cloud_puff(x + 70, y + 4, 12, (96, 116, 160), dark=(58, 66, 88))
        d.polygon([(x + 66, y + 8), (x + 72, y + 8), (x + 68, y + 18), (x + 74, y + 18), (x + 64, y + 30), (x + 68, y + 18), (x + 62, y + 18)], fill=(255, 230, 120))
        cloud_puff(x + w - 90, y + 2, 10, (96, 116, 160), dark=(58, 66, 88))
        for rx in range(x + 64, x + w - 70, 18):
            d.line([(rx, y + 14), (rx - 3, y + 22)], fill=(220, 230, 240), width=1)
        # bigger waves: a second row of breakers
        for wx in range(x + 6, x + w - 12, 22):
            d.arc([wx, y + h - 24, wx + 12, y + h - 20], 180, 360, fill=(210, 235, 245),
                  width=1)
        # two low islands in the sea at the bottom
        for ix in (x + 26, x + w - 52):
            d.ellipse([ix, y + h - 16, ix + 26, y + h - 8], fill=(90, 140, 90))
            d.polygon([(ix + 10, y + h - 16), (ix + 13, y + h - 24), (ix + 16, y + h - 16)],
                      fill=(60, 110, 70))
        # layered palms bent by the wind, and a coastal house on stilts
        for ix in (x + 26, x + w - 52):
            palm(ix + 13, y + h - 16, 12, lean=7)
        # foreground: a breaking wave crest along the bottom edge
        for wx in range(x + 4, x + w - 10, 30):
            d.arc([wx, y + h - 6, wx + 16, y + h - 1], 180, 360, fill=(235, 245, 250),
                  width=2)
        speckle(x + 4, y + h - 18, w - 8, 16, 30, 101, [(210, 235, 245)], r=1)
        d.rectangle([x + 40, y + h - 28, x + 66, y + h - 18],
                    fill=(240, 230, 210), outline=NAVY, width=1)
        d.polygon([(x + 37, y + h - 28), (x + 53, y + h - 36),
                   (x + 69, y + h - 28)], fill=(178, 44, 40))
        for sx_ in (x + 44, x + 52, x + 56, x + 62):
            d.line([(sx_, y + h - 18), (sx_, y + h - 12)], fill=(120, 90, 60), width=2)
        flag("cook", x + 8, y + 6, 48, 28)
        d.rectangle([x + w - 62, y + 6, x + w - 6, y + 20], fill=(255, 255, 255),
                    outline=TEAL, width=1)
        d.text((x + w - 58, y + 8), "CAT 5", font=font(SANSB, 9), fill=TEAL)
    elif kind == "gaza":
        # tents in the rain: grey-blue sky, flooded ground, tent rows
        vgrad(x, y, w, h, (150, 140, 175), (80, 88, 120))
        soft_disc(x + w - 30, y + 14, 12, 12, (240, 240, 250), (150, 140, 175), steps=4)
        d.ellipse([x + w - 34, y + 6, x + w - 26, y + 14], fill=(250, 250, 255))
        cloud(x + 50, y + 8, 12, (150, 140, 175))
        cloud(x + w - 60, y + 6, 10, (150, 140, 175))
        for rx in range(x + 8, x + w - 8, 22):
            d.line([(rx, y + 22), (rx - 2, y + 30)], fill=(150, 165, 185), width=1)
        # flood water along the bottom
        vgrad(x, y + h - 16, w, 16, (120, 150, 175), (90, 120, 150))
        for wy in (y + h - 10, y + h - 5):
            for wx in range(x + 6, x + w - 12, 26):
                d.arc([wx, wy - 2, wx + 12, wy + 2], 180, 360, fill=(200, 220, 235), width=1)
        # two rows of tents, the front row larger
        for tx, ts in [(x + 12, 26), (x + 52, 30), (x + 96, 26), (x + w - 52, 28)]:
            d.polygon([(tx, y + h - 16), (tx + ts // 2, y + h - 16 - ts),
                       (tx + ts, y + h - 16)], fill=(226, 220, 200), outline=(120, 110, 90), width=1)
            d.rectangle([tx + ts // 2 - 3, y + h - 24, tx + ts // 2 + 3, y + h - 16],
                        fill=(90, 70, 55))
        for tx in (x + 34, x + 78, x + 122):
            d.polygon([(tx, y + h - 30), (tx + 9, y + h - 42), (tx + 18, y + h - 30)],
                      fill=(200, 192, 170), outline=(120, 110, 90), width=1)
        # folds on the front tents, a child sheltering by a door, and
        # rubble scattered in the foreground flood water
        for tx, ts in [(x + 12, 26), (x + 52, 30), (x + 96, 26), (x + w - 52, 28)]:
            d.line([(tx + ts // 2 - 6, y + h - 16), (tx + ts // 2 - 2, y + h - 16 - ts + 6)],
                   fill=(170, 160, 140), width=1)
            d.line([(tx + ts // 2 + 6, y + h - 16), (tx + ts // 2 + 2, y + h - 16 - ts + 6)],
                   fill=(170, 160, 140), width=1)
        person(x + 96, y + h - 6, 10, (140, 90, 80))
        speckle(x + 6, y + h - 8, w - 12, 6, 24, 103, [(120, 110, 100), (150, 140, 125)],
                r=1)
        # warm light glowing in two tent doors, and families sheltering
        for gx_ in (x + 22, x + 64):
            d.rectangle([gx_, y + h - 24, gx_ + 6, y + h - 16], fill=(255, 200, 90))
        soft_disc(x + 25, y + h - 20, 12, 6, (255, 200, 90), (80, 88, 120), steps=3)
        soft_disc(x + 67, y + h - 20, 12, 6, (255, 200, 90), (80, 88, 120), steps=3)
        for fx_ in (x + 30, x + 88, x + 126):
            d.ellipse([fx_, y + h - 26, fx_ + 5, y + h - 21], fill=(70, 70, 80))
            d.polygon([(fx_ + 1, y + h - 21), (fx_ + 4, y + h - 21), (fx_ + 6, y + h - 12),
                       (fx_ - 1, y + h - 12)], fill=(80, 80, 90))
        # puddle reflections in the flood water
        for px_ in (x + 20, x + 90, x + 150):
            d.ellipse([px_, y + h - 9, px_ + 22, y + h - 5], fill=(190, 210, 230))
        flag("palestine", x + 8, y + 6, 48, 28)
        # a cold wind swirl and a tag for the fourth winter
        d.arc([x + w - 46, y + 8, x + w - 14, y + 40], 200, 80, fill=(255, 255, 255), width=2)
        d.rectangle([x + w - 78, y + h - 32, x + w - 6, y + h - 20], fill=(255, 255, 255),
                    outline=NAVY, width=1)
        d.text((x + w - 74, y + h - 30), "4TH WINTER", font=font(SANSB, 8), fill=NAVY)

    elif kind == "waymo":
        # a driverless car on a freeway, under a red ban sign
        vgrad(x, y, w, h, (70, 78, 110), (34, 40, 64))
        # city skyline along the back
        for tx, th in [(x + 8, 20), (x + 30, 30), (x + 54, 18), (x + w - 60, 26),
                       (x + w - 34, 32), (x + w - 12, 20)]:
            d.rectangle([tx, y + 30 - th, tx + 14, y + 30], fill=(60, 66, 90))
        d.rectangle([x, y + 30, x + w, y + 34], fill=(50, 55, 75))
        # lit windows in the skyline towers
        for tx, th in [(x + 8, 20), (x + 30, 30), (x + 54, 18), (x + w - 60, 26),
                       (x + w - 34, 32), (x + w - 12, 20)]:
            for wy in range(y + 32 - th, y + 28, 6):
                d.rectangle([tx + 3, wy, tx + 6, wy + 3], fill=(255, 220, 120))
        # the freeway: dark asphalt, lane dashes, a shoulder line
        d.rectangle([x, y + 34, x + w, y + h], fill=(70, 76, 84))
        d.rectangle([x, y + 34, x + w, y + 38], fill=(200, 200, 200))
        for lx_ in range(x + 6, x + w - 6, 28):
            d.rectangle([lx_, y + h // 2 + 8, lx_ + 14, y + h // 2 + 11], fill=(240, 220, 60))
        # the car: low body, sensor dome on top, glowing lidar ring
        d.rounded_rectangle([x + w // 2 - 52, y + h - 34, x + w // 2 + 52, y + h - 12],
                            radius=6, fill=(240, 244, 248), outline=NAVY, width=2)
        d.rounded_rectangle([x + w // 2 - 30, y + h - 46, x + w // 2 + 30, y + h - 32],
                            radius=5, fill=(180, 210, 235), outline=NAVY, width=1)
        d.ellipse([x + w // 2 - 8, y + h - 52, x + w // 2 + 8, y + h - 44], fill=(40, 50, 60))
        d.ellipse([x + w // 2 - 4, y + h - 50, x + w // 2 + 4, y + h - 46], fill=(80, 200, 255))
        # headlight beams cutting across the dark freeway
        d.polygon([(x + w // 2 + 52, y + h - 24), (x + w - 8, y + h - 29), (x + w - 8, y + h - 19)], fill=(255, 230, 140))
        d.polygon([(x + w // 2 - 52, y + h - 24), (x + 2, y + h - 29), (x + 2, y + h - 19)], fill=(255, 230, 140))
        # headlight pools on the wet asphalt, and the car's dark reflection
        soft_disc(x + w - 20, y + h - 24, 14, 4, (255, 230, 140), (70, 76, 84), steps=3)
        soft_disc(x + 14, y + h - 24, 14, 4, (255, 230, 140), (70, 76, 84), steps=3)
        d.rounded_rectangle([x + w // 2 - 52, y + h - 9, x + w // 2 + 52, y + h - 2],
                            radius=6, fill=(52, 58, 66))
        # foreground: an orange-and-white road barrier at the near shoulder
        for bx_ in range(3):
            d.rectangle([x + w - 46 + bx_ * 14, y + h - 12, x + w - 34 + bx_ * 14, y + h - 6],
                        fill=(255, 120, 30) if bx_ % 2 == 0 else (255, 255, 255),
                        outline=NAVY, width=1)
        d.ellipse([x + w // 2 - 44, y + h - 16, x + w // 2 - 32, y + h - 4], fill=(30, 30, 30))
        d.ellipse([x + w // 2 + 32, y + h - 16, x + w // 2 + 44, y + h - 4], fill=(30, 30, 30))
        d.ellipse([x + w // 2 - 40, y + h - 13, x + w // 2 - 36, y + h - 9], fill=(150, 150, 150))
        d.ellipse([x + w // 2 + 36, y + h - 13, x + w // 2 + 40, y + h - 9], fill=(150, 150, 150))
        # a second, smaller driverless car in the far lane, and lidar rays
        d.rounded_rectangle([x + 12, y + 40, x + 52, y + 50], radius=4,
                            fill=(210, 220, 230), outline=NAVY, width=1)
        d.rounded_rectangle([x + 20, y + 34, x + 44, y + 40], radius=3,
                            fill=(170, 200, 225), outline=NAVY, width=1)
        d.ellipse([x + 30, y + 31, x + 36, y + 35], fill=(40, 50, 60))
        d.ellipse([x + 17, y + 48, x + 23, y + 52], fill=(30, 30, 30))
        d.ellipse([x + 41, y + 48, x + 47, y + 52], fill=(30, 30, 30))
        for rr in (16, 24):
            d.arc([x + w // 2 - rr, y + h - 52 - rr, x + w // 2 + rr, y + h - 52 + rr],
                  200, 340, fill=(120, 210, 255), width=1)
        # a speed-limit sign on a pole at the right shoulder
        d.line([(x + w - 20, y + 58), (x + w - 20, y + h - 4)], fill=NAVY, width=2)
        d.rectangle([x + w - 30, y + 44, x + w - 10, y + 58], fill=(255, 255, 255),
                    outline=NAVY, width=1)
        d.text((x + w - 27, y + 46), "55", font=font(SANSB, 8), fill=NAVY)
        # red ban circle over the car
        d.ellipse([x + w - 44, y + 6, x + w - 12, y + 38], outline=(200, 30, 30), width=4)
        d.line([(x + w - 40, y + 34), (x + w - 16, y + 10)], fill=(200, 30, 30), width=4)
        flag("us", x + 8, y + 6, 48, 28)
    elif kind == "cyber":
        # a supermarket freezer aisle: frosted chests, a warning sign
        vgrad(x, y, w, h, (170, 195, 220), (120, 145, 175))
        # shelf wall along the back, with packs in varied colours
        d.rectangle([x, y, x + w, y + 16], fill=(150, 160, 175))
        for sx, pcol in zip(range(x + 8, x + w - 20, 26),
                            [(240, 200, 120), (200, 120, 110), (140, 180, 140),
                             (180, 160, 220), (240, 200, 120), (200, 170, 90),
                             (160, 200, 200)]):
            d.rectangle([sx, y + 4, sx + 16, y + 14], fill=pcol,
                        outline=(120, 125, 135), width=1)
        # a mini map of Europe with the 7 hit countries dotted
        d.rectangle([x + 54, y + 2, x + 90, y + 16], fill=(255, 255, 255), outline=NAVY,
                    width=1)
        d.polygon([(x + 60, y + 6), (x + 70, y + 4), (x + 82, y + 6), (x + 88, y + 10),
                   (x + 84, y + 14), (x + 72, y + 14), (x + 62, y + 11)],
                  fill=(220, 200, 150), outline=(120, 100, 70), width=1)
        for dx, dy in [(x + 66, y + 8), (x + 74, y + 7), (x + 80, y + 10), (x + 86, y + 9),
                       (x + 70, y + 12), (x + 78, y + 12), (x + 84, y + 12)]:
            d.ellipse([dx - 1, dy - 1, dx + 1, dy + 1], fill=(200, 30, 30))
        # two freezer chests, lids ajar, frost on the rims
        for fx_ in (x + 10, x + w // 2 + 4):
            d.rectangle([fx_, y + 26, fx_ + w // 2 - 18, y + h - 10], fill=(240, 244, 248),
                        outline=NAVY, width=2)
            d.rectangle([fx_, y + 26, fx_ + w // 2 - 18, y + 34], fill=(200, 215, 230))
            d.polygon([(fx_ + 4, y + 26), (fx_ + w // 2 - 22, y + 26), (fx_ + w // 2 - 30, y + 16),
                       (fx_ + 12, y + 16)], fill=(180, 200, 220), outline=NAVY, width=1)
            for ix in range(fx_ + 6, fx_ + w // 2 - 24, 18):
                d.text((ix, y + 40), "*", font=font(SANSB, 12), fill=(150, 200, 230))
            d.rectangle([fx_ + 8, y + h - 22, fx_ + 34, y + h - 14], fill=(200, 225, 245),
                        outline=NAVY, width=1)
        # price tags and extra frost on the chests
        for tx_ in (x + 40, x + w // 2 + 34):
            d.rectangle([tx_, y + h - 30, tx_ + 22, y + h - 24], fill=(255, 255, 255),
                        outline=NAVY, width=1)
            d.text((tx_ + 3, y + h - 29), "€3.99", font=font(SANSB, 6), fill=NAVY)
        for ix in range(x + 14, x + w - 14, 30):
            d.text((ix, y + 20), "*", font=font(SANSB, 10), fill=(255, 255, 255))
        # cold mist hugging the floor, and frost flecks on the chests
        soft_disc(x + w // 2, y + h - 6, 40, 5, (220, 235, 245), (120, 145, 175), steps=3)
        speckle(x + 10, y + 26, w - 20, h - 36, 50, 107,
                [(230, 242, 250), (200, 220, 235)], r=1)
        # a warning triangle between the chests, and a cut cable
        soft_disc(x + w // 2 - 2, y + 20, 16, 10, (255, 210, 0), (170, 195, 220), steps=3)
        d.polygon([(x + w // 2 - 2, y + 8), (x + w // 2 + 12, y + 30), (x + w // 2 - 16, y + 30)],
                  fill=(255, 210, 0), outline=NAVY, width=1)
        d.text((x + w // 2 - 5, y + 16), "!", font=font(SANSB, 12), fill=NAVY)
        d.line([(x + w // 2 - 30, y + h - 4), (x + w // 2 - 10, y + h - 10)], fill=(40, 40, 40),
               width=2)
        d.line([(x + w // 2 + 10, y + h - 10), (x + w // 2 + 30, y + h - 4)], fill=(40, 40, 40),
               width=2)
        d.ellipse([x + w // 2 - 12, y + h - 12, x + w // 2 - 6, y + h - 6], fill=(200, 60, 40))
        d.ellipse([x + w // 2 + 6, y + h - 12, x + w // 2 + 12, y + h - 6], fill=(200, 60, 40))
        flag("eu", x + 8, y + 6, 48, 28)
        d.rectangle([x + w - 72, y + h - 30, x + w - 6, y + h - 18], fill=(255, 255, 255),
                    outline=NAVY, width=1)
        d.text((x + w - 68, y + h - 28), "7 COUNTRIES", font=font(SANSB, 8), fill=NAVY)
    elif kind == "voyager":
        # deep space: a starfield, Voyager's dish and boom, golden disc
        d.rectangle([x, y, x + w, y + h], fill=(8, 12, 30))
        rng2 = random.Random(20261118)
        for _ in range(90):
            sx, sy = x + rng2.randint(2, w - 3), y + rng2.randint(2, h - 3)
            r = rng2.choice([1, 1, 2])
            d.ellipse([sx - r, sy - r, sx + r, sy + r], fill=(255, 255, 255))
        # a faint Milky Way band across the frame
        for mx_ in range(x, x + w, 8):
            my_ = y + h // 3 + int(10 * math.sin((mx_ - x) / 40))
            soft_disc(mx_, my_, 10, 4, (120, 130, 180), (8, 12, 30), steps=3)
        soft_disc(x + 30, y + h - 20, 18, 8, (140, 110, 190), (8, 12, 30), steps=3)
        soft_disc(x + w - 20, y + 30, 14, 7, (90, 120, 200), (8, 12, 30), steps=3)
        # Saturn with its ring, top-right, and orbit arcs kept inside the panel
        d.ellipse([x + w - 52, y + 8, x + w - 36, y + 20], fill=(230, 200, 140))
        d.ellipse([x + w - 58, y + 12, x + w - 30, y + 16], outline=(230, 200, 140), width=2)
        d.arc([x + 4, y + 2, x + w - 4, y + 36], 180, 360, fill=(110, 120, 165), width=1)
        d.arc([x + 4, y + 18, x + w - 4, y + h - 2], 0, 180, fill=(90, 100, 140), width=1)
        # a comet with a glowing tail crossing the lower-left sky,
        # and a few bright stars with cross sparkles
        d.line([(x + 46, y + h - 14), (x + 66, y + h - 26)], fill=(200, 220, 255), width=2)
        soft_disc(x + 46, y + h - 14, 5, 5, (255, 255, 255), (8, 12, 30), steps=3)
        d.ellipse([x + 44, y + h - 16, x + 48, y + h - 12], fill=(255, 255, 255))
        for sx_, sy_ in [(x + 60, y + 40), (x + w - 90, y + 44), (x + 100, y + 12)]:
            d.line([(sx_ - 4, sy_), (sx_ + 4, sy_)], fill=(255, 255, 255), width=1)
            d.line([(sx_, sy_ - 4), (sx_, sy_ + 4)], fill=(255, 255, 255), width=1)
        # a red Mars dot and a distant blue planet
        d.ellipse([x + 132, y + 24, x + 138, y + 30], fill=(220, 90, 60))
        d.ellipse([x + w - 70, y + h - 16, x + w - 62, y + h - 8], fill=(90, 130, 220))
        # Earth, small and blue, bottom-left
        soft_disc(x + 22, y + h - 20, 18, 18, (80, 150, 230), (8, 12, 30), steps=4)
        d.ellipse([x + 8, y + h - 34, x + 36, y + h - 6], fill=(70, 140, 210),
                  outline=(150, 200, 240), width=1)
        d.arc([x + 10, y + h - 32, x + 34, y + h - 8], 200, 340, fill=(80, 170, 90), width=3)
        # Voyager: bus body, big white dish, long boom, RTG fin
        d.rectangle([x + w // 2 - 14, y + h // 2 - 6, x + w // 2 + 14, y + h // 2 + 10],
                    fill=(200, 205, 215), outline=(255, 255, 255), width=1)
        d.pieslice([x + w // 2 - 34, y + h // 2 - 34, x + w // 2 + 34, y + h // 2 + 6],
                   180, 360, fill=(240, 240, 245), outline=(255, 255, 255), width=1)
        d.line([(x + w // 2, y + h // 2 - 6), (x + w // 2, y + h // 2 + 2)], fill=(255, 255, 255),
               width=2)
        d.line([(x + w // 2 + 14, y + h // 2), (x + w // 2 + 44, y + h // 2 - 14)],
               fill=(180, 185, 195), width=3)
        d.ellipse([x + w // 2 + 40, y + h // 2 - 18, x + w // 2 + 48, y + h // 2 - 10],
                  fill=(255, 215, 0))
        d.line([(x + w // 2 - 14, y + h // 2 + 4), (x + w // 2 - 40, y + h // 2 + 16)],
               fill=(180, 185, 195), width=3)
        d.rectangle([x + w // 2 - 46, y + h // 2 + 12, x + w // 2 - 34, y + h // 2 + 20],
                    fill=(120, 125, 135))
        # radio signals arcing out from the dish toward Earth
        for rr in (44, 54):
            d.arc([x + w // 2 - rr, y + h // 2 - 34 - rr, x + w // 2 + rr,
                   y + h // 2 - 34 + rr], 200, 340, fill=(140, 200, 255), width=1)
        # the golden record, a bright disc with grooves
        soft_disc(x + w - 29, y + h - 29, 12, 12, (255, 205, 60), (8, 12, 30), steps=3)
        d.ellipse([x + w - 48, y + h - 48, x + w - 10, y + h - 10], fill=(255, 205, 60),
                  outline=(255, 235, 140), width=1)
        d.ellipse([x + w - 42, y + h - 42, x + w - 16, y + h - 16], outline=(200, 160, 40),
                  width=1)
        d.ellipse([x + w - 34, y + h - 34, x + w - 24, y + h - 24], fill=(200, 160, 40))
        d.rectangle([x + 6, y + 6, x + 108, y + 20], fill=(255, 255, 255), outline=NAVY, width=1)
        d.text((x + 10, y + 8), "1 LIGHT-DAY", font=font(SANSB, 9), fill=NAVY)
    elif kind == "markets":
        # a falling market: dark board, red candles, a plunging line
        d.rectangle([x, y, x + w, y + h], fill=(16, 24, 40))
        # faint grid
        for gy in range(y + 10, y + h - 8, 12):
            d.line([(x + 4, gy), (x + w - 4, gy)], fill=(40, 52, 72), width=1)
        for gx in range(x + 10, x + w - 4, 24):
            d.line([(gx, y + 4), (gx, y + h - 4)], fill=(40, 52, 72), width=1)
        # red candles stepping down left to right, two green up-days
        # breaking the run
        tops = [10, 16, 14, 20, 26, 24, 32, 38, 40, 36]
        for i, t in enumerate(tops):
            cx0 = x + 8 + i * 16
            ccol = (80, 180, 90) if i in (2, 7) else (220, 60, 50)
            d.rectangle([cx0, y + t, cx0 + 10, y + t + 14], fill=ccol)
            d.line([(cx0 + 5, y + t - 4), (cx0 + 5, y + t + 18)], fill=ccol, width=2)
        # the index line, plunging down
        pts = [(x + 10, y + 12), (x + 40, y + 20), (x + 70, y + 18), (x + 100, y + 30),
               (x + 130, y + 38), (x + 160, y + 44), (x + w - 12, y + h - 12)]
        d.line(pts, fill=(255, 80, 70), width=3)
        # a second, shallower index line (S&P) trailing the Dow
        pts2 = [(x + 10, y + 20), (x + 50, y + 24), (x + 90, y + 26), (x + 130, y + 34),
                (x + 160, y + 40), (x + w - 12, y + h - 20)]
        d.line(pts2, fill=(255, 170, 60), width=2)
        d.ellipse([pts[-1][0] - 4, pts[-1][1] - 4, pts[-1][0] + 4, pts[-1][1] + 4],
                  fill=(255, 80, 70))
        soft_disc(pts[-1][0], pts[-1][1], 10, 7, (255, 80, 70), (16, 24, 40), steps=3)
        # volume bars along the bottom and a ticker tape
        for i, vh in enumerate([4, 6, 5, 8, 6, 9, 7, 10]):
            vx0 = x + 100 + i * 10
            d.rectangle([vx0, y + h - 12 - vh, vx0 + 6, y + h - 12], fill=(140, 50, 45))
        d.text((x + 100, y + h - 10), "NVDA DOWN", font=font(SANSB, 7),
               fill=(255, 150, 140))
        # down arrow and the Dow number
        d.polygon([(x + w - 30, y + 8), (x + w - 14, y + 8), (x + w - 22, y + 20)],
                  fill=(255, 80, 70))
        d.rectangle([x + 6, y + h - 22, x + 96, y + h - 8], fill=(255, 255, 255),
                    outline=CRIMSON, width=1)
        d.text((x + 10, y + h - 20), "DOW -566", font=font(SANSB, 9), fill=CRIMSON)
        # gold price at the top centre, clear of the plunging line
        d.text((x + w // 2 - 34, y + 4), "GOLD $3,742", font=font(SANSB, 8),
               fill=(255, 215, 0))
    elif kind == "patriot":
        # Patriot launchers on a truck, German and Norwegian flags
        vgrad(x, y, w, h, (244, 182, 118), (150, 118, 100))
        cloud(x + 50, y + 8, 10, (244, 182, 118))
        d.rectangle([x, y + h - 14, x + w, y + h], fill=(120, 130, 120))
        for gx_ in range(x + 6, x + w - 6, 24):
            d.polygon([(gx_, y + h - 14), (gx_ + 4, y + h - 24), (gx_ + 8, y + h - 14)],
                      fill=(110, 130, 110))
        # two soldiers standing behind the truck, and a second smoke plume
        for sx_ in (x + 24, x + w - 70):
            d.ellipse([sx_, y + h - 44, sx_ + 7, y + h - 37], fill=(220, 190, 150),
                      outline=NAVY, width=1)
            d.polygon([(sx_ + 1, y + h - 37), (sx_ + 6, y + h - 37), (sx_ + 8, y + h - 22),
                       (sx_ - 1, y + h - 22)], fill=(90, 105, 80))
            d.line([(sx_ + 4, y + h - 36), (sx_ + 4, y + h - 46)], fill=(60, 60, 60), width=2)
        cloud(x + w - 90, y + 6, 8, (244, 182, 118))
        soft_disc(x + w // 2 - 20, y + 16, 12, 7, (225, 225, 230), (244, 182, 118), steps=4)
        flag("germany", x + 10, y + 6, 48, 28)
        flag("norway", x + w - 58, y + 6, 48, 28)
        # the launcher truck, low in the frame
        d.rectangle([x + 14, y + h - 30, x + w - 14, y + h - 14], fill=(90, 105, 80),
                    outline=NAVY, width=1)
        d.rectangle([x + w - 52, y + h - 44, x + w - 14, y + h - 30], fill=(110, 125, 100),
                    outline=NAVY, width=1)
        d.rectangle([x + w - 48, y + h - 42, x + w - 30, y + h - 34], fill=(180, 215, 235))
        for wx_ in (x + 30, x + 62, x + w - 70):
            d.ellipse([wx_, y + h - 16, wx_ + 14, y + h - 2], fill=(30, 30, 30))
            d.ellipse([wx_ + 4, y + h - 12, wx_ + 10, y + h - 6], fill=(120, 120, 120))
        # four launcher tubes angled up from the truck bed
        for i in range(4):
            tx0 = x + 26 + i * 22
            d.polygon([(tx0, y + h - 30), (tx0 + 14, y + h - 30), (tx0 + 26, y + 12),
                       (tx0 + 12, y + 12)], fill=(70, 82, 70), outline=NAVY, width=1)
            d.ellipse([tx0 + 12, y + 10, tx0 + 26, y + 18], fill=(50, 60, 50))
            soft_disc(tx0 + 19, y + 14, 6, 4, (255, 160, 60), (244, 182, 118), steps=3)
        # a missile streaking up, with a smoke trail
        d.line([(x + w // 2 + 40, y + 16), (x + w // 2 + 52, y + 6)], fill=(255, 255, 255),
               width=2)
        d.polygon([(x + w // 2 + 52, y + 6), (x + w // 2 + 58, y + 12), (x + w // 2 + 50, y + 14)],
                  fill=(200, 200, 200), outline=NAVY, width=1)
        # smoke puffs trailing the climbing missile, kept clear of the flags
        smoke_plume(x + w // 2 + 30, y + 22, 6, (225, 225, 230), (244, 182, 118), 53, n=5)
        # foreground: dry grass tufts along the bottom edge
        for gx_ in range(x + 8, x + w - 8, 22):
            d.line([(gx_, y + h - 4), (gx_ - 2, y + h - 12)], fill=(140, 150, 110), width=1)
            d.line([(gx_, y + h - 4), (gx_ + 2, y + h - 11)], fill=(160, 170, 125), width=1)
    elif kind == "border":
        # a border line in the highlands: watchtowers, two flags, troops
        vgrad(x, y, w, h, (250, 190, 128), (168, 138, 118))
        sun_glow(x + w - 24, y + 34, 6, (250, 190, 128))
        d.polygon([(x, y + h - 20), (x + 40, y + h - 40), (x + 80, y + h - 20)],
                  fill=(150, 160, 150))
        d.polygon([(x + w - 90, y + h - 20), (x + w - 50, y + h - 44), (x + w - 10, y + h - 20)],
                  fill=(140, 150, 140))
        d.polygon([(x + 32, y + h - 34), (x + 40, y + h - 40), (x + 48, y + h - 34)],
                  fill=(240, 242, 246))
        d.polygon([(x + w - 58, y + h - 38), (x + w - 50, y + h - 44), (x + w - 42, y + h - 38)],
                  fill=(240, 242, 246))
        # a third, fainter ridge behind the mountains
        d.polygon([(x + 60, y + h - 20), (x + 90, y + h - 48), (x + 120, y + h - 20)],
                  fill=(170, 178, 168))
        d.polygon([(x + 82, y + h - 42), (x + 90, y + h - 48), (x + 98, y + h - 42)],
                  fill=(240, 242, 246))
        # shaded slopes on the near peaks, and haze between the ridges
        d.polygon([(x + 40, y + h - 20), (x + 40, y + h - 40), (x + 80, y + h - 20)],
                  fill=(130, 140, 130))
        d.polygon([(x + w - 50, y + h - 20), (x + w - 50, y + h - 44),
                   (x + w - 10, y + h - 20)], fill=(120, 130, 120))
        soft_disc(x + w // 2, y + h - 30, 30, 6, (220, 218, 205), (250, 190, 128), steps=3)
        d.polygon([(x + 82, y + h - 42), (x + 90, y + h - 48), (x + 98, y + h - 42)],
                  fill=(240, 242, 246))
        # barbed wire strung along the border posts
        for bx_ in range(x + 6, x + w - 6, 16):
            d.line([(bx_, y + h - 26), (bx_ + 8, y + h - 22)], fill=(80, 80, 80), width=1)
            d.line([(bx_ + 8, y + h - 22), (bx_ + 16, y + h - 26)], fill=(80, 80, 80), width=1)
        # the border: a dashed line across the ground
        d.rectangle([x, y + h - 20, x + w, y + h - 8], fill=(170, 150, 120))
        for bx_ in range(x + 4, x + w - 4, 20):
            d.rectangle([bx_, y + h - 16, bx_ + 10, y + h - 12], fill=(255, 255, 255))
        # watchtowers on both sides
        for tx in (x + 16, x + w - 40):
            d.rectangle([tx + 8, y + 18, tx + 16, y + h - 20], fill=(120, 95, 70),
                        outline=NAVY, width=1)
            d.rectangle([tx, y + 8, tx + 24, y + 20], fill=(90, 70, 50), outline=NAVY, width=1)
            d.rectangle([tx + 4, y + 11, tx + 20, y + 17], fill=(255, 220, 130))
        flag("ethiopia", x + 48, y + 6, 56, 30)
        flag("eritrea", x + w - 96, y + 6, 56, 30)
        # troops marching along the border, varied heights and kits,
        # rifles on their shoulders, shadows on the dusty ground
        for hx_, th, tshirt in [(x + w // 2 - 42, 14, (70, 80, 60)),
                                (x + w // 2 - 28, 12, (80, 75, 55)),
                                (x + w // 2 - 14, 15, (70, 80, 60)),
                                (x + w // 2 + 2, 12, (60, 70, 55)),
                                (x + w // 2 + 16, 14, (80, 75, 55)),
                                (x + w // 2 + 30, 12, (70, 80, 60)),
                                (x + w // 2 + 42, 13, (60, 70, 55))]:
            person(hx_, y + h - 16, th, tshirt, skin=(190, 160, 120))
            d.line([(hx_ - 2, y + h - 16 - th + 2), (hx_ + 6, y + h - 16 - th - 4)],
                   fill=(60, 60, 60), width=2)
        # a military camp tent at the left edge, dust rising by the troops
        d.polygon([(x + 2, y + h - 8), (x + 12, y + h - 22), (x + 22, y + h - 8)],
                  fill=(200, 190, 150), outline=(120, 110, 90), width=1)
        soft_disc(x + w // 2 + 40, y + h - 18, 10, 5, (200, 185, 150), (226, 220, 200),
                  steps=3)
        # dry ground texture along the bottom edge
        speckle(x + 6, y + h - 8, w - 12, 6, 24, 109, [(140, 120, 95), (190, 170, 140)],
                r=1)


# ---------- panels ----------
# (num, category, colour, headline, dek, caption, pic)
PANELS = [
    (1, "MIDDLE EAST · GULF", CRIMSON, "US Strikes Iran Site; Tehran Fires Back",
     "US hits a missile site on Qeshm; Iran fires at US bases in Kuwait and Bahrain.",
     "QESHM ISLAND • GULF", "gulf"),
    (2, "ASIA · APEC", CRIMSON, "Xi and Putin Meet at APEC",
     "Leaders denounce sanctions in Shenzhen; talks with Trump set for Thursday.",
     "SHENZHEN • CHINA", "apec"),
    (3, "AMERICAS · POLITICS", PURPLE, "Peltola Wins Alaska Senate",
     "Peltola beats Sullivan 50.1%; Democrats take a 56-44 Senate majority.",
     "ANCHORAGE • ALASKA", "senate"),
    (4, "AMERICAS · HEALTH", PURPLE, "US Loses Measles-Free Status",
     "5,412 cases, 10 deaths; first loss in 26 years.",
     "USA • HEALTH", "measles"),
    (5, "AFRICA · HEALTH", GREEN, "Ebola Passes 11,000 Cases",
     "5,635 dead in DR Congo; children hit hardest.",
     "ITURI • DR CONGO", "ebola"),
    (6, "PACIFIC · WEATHER", TEAL, "Cyclone Xavier Hits Cat 5",
     "Strongest November cyclone on record; Cook Islands brace.",
     "COOK ISLANDS • PACIFIC", "cyclone"),
    (7, "MIDDLE EAST · GAZA", CRIMSON, "Gaza Shivers in Flooded Tents",
     "Cold kills in the camps; 950,000 in flood-prone tents.",
     "GAZA STRIP", "gaza"),
    (8, "TECH · USA", PURPLE, "Waymo Halts Freeway Rides",
     "Driverless cars off US freeways; California ban.",
     "CALIFORNIA • USA", "waymo"),
    (9, "EUROPE · CYBER", BLUE, "Hackers Freeze Supermarkets",
     "Cyberattack disables freezers in 7 European countries.",
     "EUROPE • CYBER", "cyber"),
    (10, "SPACE · NASA", PURPLE, "Voyager Hits One Light-Day",
     "First human-made object a light-day from Earth.",
     "DEEP SPACE • NASA", "voyager"),
    (11, "MARKETS · USA", PURPLE, "Markets Slide; Dow Falls 566",
     "S&P falls a 5th day; Nvidia drops despite a beat.",
     "WALL STREET", "markets"),
    (12, "EUROPE · DEFENCE", BLUE, "Berlin, Oslo Fund Ukraine Arms",
     "Each pays $500m for US weapons, Patriots included.",
     "BERLIN • OSLO", "patriot"),
    (13, "AFRICA · CONFLICT", GREEN, "Ethiopia, Eritrea Mass Troops",
     "Troops mass along the border; fears of wider war.",
     "ETHIOPIA • ERITREA", "border"),
]


def draw_panel(x, y, w, h, p, large):
    num, cat, col, head, dek, cap, kind = p
    pic_h = 74 if large else 60
    strip_h = 17 if large else 16
    d.rounded_rectangle([x + 2, y + 2, x + w + 2, y + h + 2], radius=4, fill=(190, 180, 160))
    d.rounded_rectangle([x, y, x + w, y + h], radius=4, fill=(255, 255, 255), outline=NAVY, width=2)
    pic(kind, x + 2, y + 2, w - 4, pic_h)
    # cinematic grade over the picture only (skipped for the photo
    # panels: the photographs already carry their own light)
    if kind in PHOTOS:
        pass
    elif kind in ("voyager", "markets", "waymo"):
        cinema_grade(x + 2, y + 2, w - 4, pic_h, warm=(140, 170, 255), strength=14)
    else:
        cinema_grade(x + 2, y + 2, w - 4, pic_h)
    sy = y + 2 + pic_h
    d.rectangle([x + 2, sy, x + w - 2, sy + strip_h], fill=col)
    d.text((x + 10, sy + 2), cap, font=font(SANSB, 10 if large else 9), fill=(255, 255, 255))
    d.rounded_rectangle([x, y, x + w, y + h], radius=4, outline=NAVY, width=2)
    cy = sy + strip_h + 5
    r = 10 if large else 8
    d.ellipse([x + 10, cy, x + 10 + 2 * r, cy + 2 * r], fill=col)
    d.text((x + 10 + r - 3, cy + 2), str(num), font=font(SANSB, 11 if large else 10),
           fill=(255, 255, 255))
    d.text((x + 14 + 2 * r, cy + 2), cat, font=font(SANSB, 12 if large else 11), fill=col)
    hy = cy + 2 * r + 3
    hf = font(SERIFB, 20 if large else 14)
    hlines = wrap(head, hf, w - 20)
    if len(hlines) > 2:
        raise SystemExit(f"HEADLINE TOO LONG panel {num}: {hlines}")
    for i, ln in enumerate(hlines):
        d.text((x + 10, hy + i * (21 if large else 17)), ln, font=hf, fill=INK)
    dy = hy + len(hlines) * (21 if large else 17) + 1
    df = font(SANS, 12 if large else 11)
    dlines = wrap(dek, df, w - 20)
    if len(dlines) > 2:
        raise SystemExit(f"DEK TOO LONG panel {num}: {dlines}")
    for i, ln in enumerate(dlines):
        d.text((x + 10, dy + i * (13 if large else 12)), ln, font=df, fill=(35, 35, 35))


for i, p in enumerate(PANELS[:3]):
    draw_panel(14 + i * 336, 126, 324, 192, p, True)
for row, group in enumerate((PANELS[3:8], PANELS[8:13])):
    for i, p in enumerate(group):
        draw_panel(14 + i * 201, 326 + row * 164, 191, 164, p, False)

# ---------- bottom: map + also list ----------
by = 670
mx, mw, mh = 14, 360, 292
d.rounded_rectangle([mx + 2, by + 2, mx + mw + 2, by + mh + 2], radius=4, fill=(190, 180, 160))
d.rounded_rectangle([mx, by, mx + mw, by + mh], radius=4, fill=(255, 255, 255), outline=NAVY, width=2)
d.text((mx + 12, by + 10), "WHERE IT HAPPENED", font=font(SANSB, 16), fill=NAVY)
d.line([mx + 12, by + 34, mx + mw - 12, by + 34], fill=NAVY, width=2)
mapx, mapy, mapw, maph = mx + 10, by + 40, mw - 20, 160
vgrad(mapx, mapy, mapw, maph, (202, 226, 238), (164, 196, 222))


def ll(lon, lat):
    """Equirectangular projection: lon -170..190, lat 75..-55."""
    return (mapx + (lon + 170) / 360 * mapw, mapy + (75 - lat) / 130 * maph)


def land(poly, label=None, lab_lon=None, lab_lat=None):
    pts = [ll(lo, la) for lo, la in poly]
    d.polygon([(px + 2, py + 2) for px, py in pts], fill=(206, 184, 138))
    # dotted fill, like the reference's dot-matrix world map: a mask
    # of the polygon, then a grid of small slate dots inside it
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    md.polygon(pts, fill=255)
    mp = mask.load()
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    for gx in range(int(min(xs)) + 2, int(max(xs)), 5):
        for gy in range(int(min(ys)) + 2, int(max(ys)), 5):
            if 0 <= gx < W and 0 <= gy < H and mp[gx, gy]:
                d.ellipse([gx - 1, gy - 1, gx + 1, gy + 1], fill=(96, 128, 138))
    d.polygon(pts, outline=(110, 88, 55), width=1)
    d.line(pts[:3], fill=(248, 236, 200), width=1)
    if label:
        lx_, ly_ = ll(lab_lon, lab_lat)
        f = font(SANSB, 9)
        d.text((lx_ - d.textlength(label, font=f) / 2, ly_ - 5), label, font=f,
               fill=(90, 78, 55))


for lo in range(-150, 181, 30):
    x0, _ = ll(lo, 0)
    d.line([x0, mapy, x0, mapy + maph], fill=(180, 205, 220), width=1)
for la in (60, 30, 0, -30):
    _, y0 = ll(0, la)
    d.line([mapx, y0, mapx + mapw, y0], fill=(180, 205, 220), width=1)

# coarse continent outlines, drawn from the map itself, not traced
LAND = [
    ([(-168, 66), (-140, 70), (-120, 72), (-95, 80), (-80, 73), (-65, 60), (-55, 47),
      (-70, 42), (-75, 35), (-80, 26), (-90, 21), (-97, 16), (-92, 14), (-83, 9),
      (-79, 9), (-83, 15), (-90, 14), (-97, 26), (-105, 20), (-110, 24), (-120, 34),
      (-125, 40), (-125, 49), (-130, 55), (-140, 60), (-155, 58), (-165, 60)],
     "N. AMERICA", -85, 70),
    ([(-79, 9), (-77, 4), (-80, -3), (-81, -6), (-77, -12), (-72, -18), (-70, -23),
      (-70, -30), (-72, -37), (-73, -44), (-70, -50), (-68, -55), (-65, -55), (-62, -48),
      (-58, -38), (-52, -32), (-48, -28), (-41, -23), (-35, -9), (-35, -6), (-44, -3),
      (-50, 0), (-53, 4), (-58, 6), (-62, 9), (-70, 11), (-75, 10)],
     "S. AMERICA", -60, -14),
    ([(-10, 36), (-9, 43), (-2, 44), (-1, 46), (-4, 48), (-1, 50), (2, 51), (5, 53),
      (8, 57), (10, 59), (5, 60), (5, 62), (12, 65), (18, 69), (25, 71), (30, 70),
      (35, 68), (40, 68), (45, 65), (48, 60), (45, 55), (40, 50), (38, 46), (32, 46),
      (28, 45), (23, 40), (26, 38), (23, 36), (19, 40), (15, 44), (12, 44), (8, 44),
      (3, 42), (-9, 37)], "EUROPE", -8, 60),
    ([(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53)], None, None, None),
    ([(-17, 15), (-16, 20), (-13, 27), (-10, 31), (-6, 35), (0, 36), (10, 37), (11, 34),
      (20, 32), (25, 32), (30, 31), (32, 31), (35, 28), (37, 22), (39, 18), (43, 12),
      (48, 11), (51, 10), (46, 5), (41, 0), (40, -5), (40, -10), (36, -18), (33, -26),
      (28, -33), (20, -35), (17, -32), (15, -27), (12, -18), (13, -12), (9, -1), (9, 4),
      (-8, 4), (-13, 8), (-17, 12)], "AFRICA", -2, -22),
    ([(44, -16), (47, -15), (50, -16), (49, -20), (45, -25), (43, -22)], None, None, None),
    ([(30, 70), (40, 68), (50, 69), (60, 69), (70, 72), (80, 73), (90, 75), (100, 77),
      (110, 74), (120, 73), (130, 72), (140, 72), (150, 70), (160, 69), (170, 67),
      (178, 65), (170, 60), (162, 56), (158, 52), (150, 59), (142, 54), (140, 48),
      (135, 43), (130, 42), (127, 40), (122, 38), (120, 32), (122, 28), (118, 25),
      (110, 21), (108, 18), (105, 10), (103, 8), (100, 7), (98, 12), (95, 16),
      (92, 21), (88, 22), (85, 19), (80, 15), (77, 8), (75, 12), (72, 20), (68, 23),
      (66, 25), (62, 25), (58, 26), (56, 27), (52, 26), (50, 29), (48, 30), (44, 29),
      (42, 27), (40, 24), (38, 22), (35, 28), (34, 31), (36, 36), (30, 36), (27, 38),
      (28, 41), (30, 45), (28, 46), (30, 48), (30, 60)], "ASIA", 95, 70),
    ([(130, 31), (133, 33), (136, 34), (139, 35), (141, 38), (142, 41), (144, 44),
      (142, 44), (140, 40), (137, 35), (133, 32)], None, None, None),
    ([(114, -22), (114, -30), (115, -35), (120, -34), (124, -33), (129, -32), (132, -32),
      (135, -35), (138, -35), (140, -38), (145, -38), (150, -37), (153, -32), (153, -27),
      (150, -23), (146, -19), (142, -15), (142, -11), (137, -12), (135, -15), (132, -12),
      (130, -13), (126, -14), (122, -17), (118, -20)], "AUSTRALIA", 134, -28),
]
for poly, lab, llo, lla in LAND:
    land(poly, lab, llo, lla)
for olab, olon, olat in [("ATLANTIC", -42, 8), ("PACIFIC", -120, -35), ("INDIAN", 82, -38)]:
    ox, oy = ll(olon, olat)
    of = font(SANSB, 8)
    d.text((ox - d.textlength(olab, font=of) / 2, oy - 4), olab, font=of, fill=(90, 120, 150))

# numbered pins: (lon, lat, badge dx, badge dy). The dot sits on the true
# spot; a short leader line reaches the badge, so clustered pins spread
# without landing in the wrong ocean or country.
PINS = {1: (56.3, 26.9, 30, -20), 2: (114.1, 22.5, 0, 0), 3: (-152, 64, 0, 0),
        4: (-98, 39, 0, -18), 5: (25, -2, 18, 20), 6: (-160, -21, 0, 0),
        7: (34.5, 31.5, 0, 0), 8: (-122, 37.8, -26, -12), 9: (10, 50, -24, 14),
        10: (-118.2, 34.1, 22, 16), 11: (-74, 40.7, 0, 0), 12: (13.4, 52.5, 20, -14),
        13: (39, 14.5, -26, 18)}
PINCOL = {1: CRIMSON, 2: CRIMSON, 3: PURPLE, 4: PURPLE, 5: GREEN, 6: TEAL,
          7: CRIMSON, 8: PURPLE, 9: BLUE, 10: PURPLE, 11: PURPLE, 12: BLUE, 13: GREEN}
for n, (lo, la, dx, dy) in PINS.items():
    px, py = ll(lo, la)
    cx, cy = px + dx, py + dy
    if dx or dy:
        d.line([px, py, cx, cy], fill=NAVY, width=1)
        d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=PINCOL[n], outline=(255, 255, 255),
                  width=1)
    d.ellipse([cx - 11, cy - 11, cx + 11, cy + 11], fill=PINCOL[n], outline=(255, 255, 255),
              width=2)
    nf = font(SANSB, 12)
    d.text((cx - d.textlength(str(n), font=nf) / 2, cy - 8), str(n), font=nf,
           fill=(255, 255, 255))
ly = by + 206
lx_leg = mx + 12
for col, label in [(BLUE, "Europe"), (CRIMSON, "Asia"), (GREEN, "Africa"),
                   (PURPLE, "N. America"), (TEAL, "Climate")]:
    d.ellipse([lx_leg, ly + 2, lx_leg + 10, ly + 12], fill=col)
    lx_leg += 14
    d.text((lx_leg, ly), label, font=font(SANSB, 10), fill=GREY)
    lx_leg += d.textlength(label, font=font(SANSB, 10)) + 12

# the day in numbers: four key figures of the day, each matching a
# figure already shown in a panel above (no new facts here)
d.text((mx + 12, by + 222), "THE DAY IN NUMBERS", font=font(SANSB, 11), fill=RED)
STATS = [("11,000+", "Ebola cases in DR Congo", GREEN),
         ("5,412", "US measles cases in 2026", PURPLE),
         ("-566", "Dow points", CRIMSON),
         ("Cat 5", "Cyclone Xavier", TEAL)]
sw = (mw - 24 - 3 * 8) // 4
sy0 = by + 238
for i, (num, lab, col) in enumerate(STATS):
    bx0 = mx + 12 + i * (sw + 8)
    d.rounded_rectangle([bx0, sy0, bx0 + sw, sy0 + 48], radius=4,
                        fill=(255, 255, 255), outline=col, width=2)
    d.rectangle([bx0 + 2, sy0 + 2, bx0 + sw - 2, sy0 + 6], fill=col)
    nf = font(SANSB, 15)
    while d.textlength(num, font=nf) > sw - 6 and nf.size > 11:
        nf = font(SANSB, nf.size - 1)
    d.text((bx0 + (sw - d.textlength(num, font=nf)) / 2, sy0 + 5), num, font=nf, fill=col)
    lf = font(SANS, 8)
    for k, ln in enumerate(wrap(lab, lf, sw - 8)[:2]):
        d.text((bx0 + (sw - d.textlength(ln, font=lf)) / 2, sy0 + 24 + k * 10), ln,
               font=lf, fill=(60, 60, 60))

# also list (right)
lx, lw = 386, 624
d.rounded_rectangle([lx + 2, by + 2, lx + lw + 2, by + mh + 2], radius=4, fill=(190, 180, 160))
d.rounded_rectangle([lx, by, lx + lw, by + mh], radius=4, fill=(255, 255, 255), outline=NAVY,
                    width=2)
d.text((lx + 12, by + 10), "ALSO ON WEDNESDAY 18 NOVEMBER", font=font(SANSB, 16), fill=NAVY)
d.line([lx + 12, by + 34, lx + lw - 12, by + 34], fill=NAVY, width=2)
ALSO = [
    ("Shenzhen:", " APEC summit opens in Shenzhen."),
    ("Manila:", " Trump announces Philippines trade deal."),
    ("Manila:", " Quad meets, first summit in 2+ years."),
    ("Kyiv:", " Russia launches 141 drones; 5 killed."),
    ("India:", " Cyclone Akvan eased to 90-100 km/h."),
    ("Papua New Guinea:", " M6 quake hits; no damage."),
    ("Antalya:", " COP31 split on fossil phase-out."),
    ("Israel:", " Knesset elects Kahana speaker, 66-52."),
    ("West Bank:", " UK blocks 8 settlement buildings."),
    ("Australia:", " Sanctions 3 over settlement expansion."),
    ("NSA:", " Classified network goes down."),
    ("Apple:", " Pay, iCloud, App Store outage."),
    ("Anthropic:", " IPO shares set to price above $80."),
    ("Ballon d'Or:", " Vinicius Junior wins the award."),
    ("Fiji:", " National disaster over El Nino drought."),
    ("World Court:", " To rule on Myanmar Rohingya case."),
    ("Sudan:", " Factories struggle after wartime ruin."),
    ("Nigeria:", " Approves new inland dry port in Kebbi."),
    ("Beijing:", " Seoul's Lee strengthens ties at APEC."),
    ("Thailand:", " Arsenic found in border water supplies."),
    ("Hormuz:", " Oman rescues 24 tanker crew; 4 missing."),
    ("Gaza:", " Israel starts operation in central Gaza."),
    ("Trump:", " To raise Ukraine war with Xi, Putin."),
    ("Shenzhen:", " Foreign trade up 40.9% this year."),
    ("Senate:", " Leader floats corporate income tax."),
    ("Manila:", " Hundreds arrested at anti-Trump protests."),
    ("Knesset:", " Eisenkot asked to try forming government."),
    ("Gaza:", " Board of Peace warns ceasefire may fail."),
    ("Canada:", " Home sales flat; Bank of Canada at 2.50%."),
    ("Siberia:", " An-12 crash near Kemerovo kills 19."),
]
assert len(ALSO) == 30, f"ALSO must be 30, got {len(ALSO)}"
col_w = 296
d.line([(lx + col_w + 8, by + 42), (lx + col_w + 8, by + mh - 8)], fill=(200, 190, 165), width=1)
for ci in range(2):
    items = ALSO[ci * 15:(ci + 1) * 15]
    cx = lx + 12 + ci * (col_w + 8)
    yy = by + 40
    for j, (bold, rest) in enumerate(items):
        num = 14 + ci * 15 + j
        d.text((cx, yy), f"{num}.", font=font(SANSB, 10), fill=RED)
        bx = cx + 24
        full = bold + rest
        flines = wrap(full, font(SANS, 10), col_w - 24)
        d.text((bx, yy), bold, font=font(SANSB, 10), fill=INK)
        bw = d.textlength(bold, font=font(SANSB, 10))
        d.text((bx + bw + 2, yy), flines[0][len(bold):], font=font(SANS, 10), fill=INK)
        if len(flines) > 1:
            d.text((bx, yy + 11), flines[1], font=font(SANS, 10), fill=INK)
            yy += 26
        else:
            yy += 16

# ---------- footer ----------
d.text((16, 976), "Every story here happened or was first reported on Wednesday 18 November 2026.",
       font=font(SANS, 12), fill=GREY)
foot_r = "Sources: Reuters, AP, AFP, BBC, Al Jazeera. Illustrations generated."
d.text((W - 16 - d.textlength(foot_r, font=font(SANS, 12)), 976), foot_r,
       font=font(SANS, 12), fill=GREY)

# a whisper of film grain over the whole page (seeded, so it is identical
# every run): it takes the flat digital edge off the paper and the drawings
rng = random.Random(20261118)
noise = Image.new("L", (W, H))
noise.putdata([128 + rng.randint(-7, 7) for _ in range(W * H)])
img = Image.blend(img, Image.merge("RGB", (noise, noise, noise)), 0.02)

img.save(OUT, "PNG", optimize=True)
print("wrote", OUT, os.path.getsize(OUT), "bytes")
