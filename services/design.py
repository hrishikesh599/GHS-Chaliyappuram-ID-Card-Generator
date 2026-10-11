"""Shared design constants for the ID card.

Both the PDF (card_pdf.py) and the on-screen preview (card_svg.py) read their
numbers from here, so the preview always matches the printed card.

All positions are in millimetres, measured FROM THE TOP-LEFT of the card.
"""
from __future__ import annotations

import math

import config

# Card ------------------------------------------------------------------
CARD_W = 54.0          # CR80 portrait
CARD_H = 85.6
PT = 0.352778          # 1 pt in mm

PHOTO_W = 22.0
PHOTO_H = 28.0
PHOTO_RATIO = PHOTO_W / PHOTO_H

# Palette ---------------------------------------------------------------
NAVY = "#0B2545"
NAVY_TOP = "#16427B"
NAVY_DEEP = "#06182E"
NAVY_GLOW = "#1A4684"          # centre of the radial glow behind the crest
GOLD = "#C9A24B"
GOLD_DARK = "#8F6E27"          # small captions on ivory (readable)
PAPER = "#FBF9F3"
PANEL = "#F3EEDF"              # tinted panel on the back
INK = "#2B3441"
MUTED = "#6B7280"
RULE = "#E4DCC6"
FOIL = ["#9C7A2B", "#E8CF86", "#C9A24B", "#F2E2A5", "#A57F2F"]
FOIL_POS = [0, 0.28, 0.5, 0.72, 1]

# Fonts (files live in static/fonts) -----------------------------------
FONT_DIR = config.BASE_DIR / "static" / "fonts"
FONTS = {
    "PF": ("PlayfairDisplay-Bold", "Playfair GHS", 700),    # serif: school + student name
    "MM": ("Montserrat-Medium", "Montserrat GHS", 500),     # body
    "MS": ("Montserrat-SemiBold", "Montserrat GHS", 600),   # captions
    "MB": ("Montserrat-Bold", "Montserrat GHS", 700),       # values
}

# Layout ----------------------------------------------------------------
# Curved header edge: height at the card sides / in the middle
FRONT_SIDE, FRONT_MID = 27.0, 32.0
BACK_SIDE, BACK_MID = 10.8, 13.2
BAND = 0.9                      # gold foil band hugging the curve
KEYLINE_INSET = 1.7             # thin gold frame inside the card edge

FRONT_FOOT = 7.0
BACK_FOOT = 7.0

# Arched photo window
ARCH_X = (CARD_W - PHOTO_W) / 2
ARCH_TOP = 23.6
ARCH_SHADOW = ((2.0, 0.020), (1.6, 0.025), (1.2, 0.030), (0.8, 0.035))   # (grow mm, alpha)
ARCH_SHADOW_DY = 0.8
FRAME_GROW = 1.2                # gold foil frame thickness
MAT_GROW = 0.55                 # white mat thickness
ARCH_BOTTOM_R = 1.2

# Text styles: (font key, size pt, letter-spacing pt)
ST = {
    "school":      ("PF", 8.6, 0.5),
    "kicker":      ("MS", 3.7, 1.4),
    "name":        ("PF", 10.0, 0.25),
    "capsule":     ("MS", 4.0, 0.9),
    "label":       ("MS", 3.6, 0.55),
    "value":       ("MB", 5.9, 0.0),
    "footer":      ("MS", 3.9, 1.1),
    "sec_title":   ("MS", 3.5, 1.1),
    "body":        ("MM", 5.0, 0.0),
    "locality":    ("MB", 5.8, 0.0),
    "ret_school":  ("PF", 5.8, 0.3),
    "ret_addr":    ("MM", 4.4, 0.0),
    "sig_title":   ("MS", 4.4, 1.2),
    "sig_sub":     ("MM", 3.4, 0.4),
    "email":       ("MM", 4.6, 0.25),
    "monogram":    ("PF", 6.0, 0.0),
}

# Front text positions (baselines, mm)
F_LOGO = (CARD_W / 2, 7.6, 4.6)           # cx, cy, r
F_SCHOOL_Y = 16.4
F_KICKER_Y = 19.8
F_NAME_Y = 58.2
F_CAPSULE_CY = 62.2
F_CAPSULE_H = 4.2
F_ROWS_Y = (68.8, 72.6, 76.4)
F_LABEL_X = 5.0
F_VALUE_X = 19.5
F_VALUE_MAX = 30.5
F_ROW_HAIR = 1.5                          # hairline below baseline
NAME_MAX_W = 46.0
NAME_ONE_LINE_MIN_PT = 7.6                # below this size the name wraps to 2 lines
NAME_TWO_LINE_PT = 8.0
NAME_TWO_Y = (56.4, 59.0)                 # baselines when the name wraps
GUARD_ONE_LINE_MIN_PT = 4.9               # below this the guardian wraps to 2 lines
GUARD_TWO_DY = (-0.6, 1.4)                # baseline offsets when it wraps
GUARD_TWO_HAIR = 2.1

# Back text positions
B_SCHOOL_Y = 7.0
B_LOGO = (CARD_W / 2, 15.0, 4.8)
B_ADDR_TITLE_Y = 24.8
B_ADDR_Y = 28.3
B_ADDR_STEP = 2.85
B_LOC_TITLE_Y = 38.6
B_LOC_Y = 42.0
B_PANEL = (5.0, 46.2, 44.0, 15.6)         # x, top, w, h  ("If found" panel)
B_RET_TITLE_Y = 50.4
B_RET_SCHOOL_Y = 54.4
B_RET_ADDR_Y = 57.2
B_RET_STEP = 2.6
B_SIG_LINE_Y = 71.0
B_SIG_BOX = (26.0, 8.6)                   # w, h

# Guilloche rosettes behind the header text: (cx, cy, R, n ellipses, eccentricity)
F_ROSETTE = (CARD_W / 2, 9.0, 27.0, 36, 0.30)
F_ROSETTE_INNER = (CARD_W / 2, 7.8, 11.5, 24, 0.55)
B_ROSETTE = (CARD_W / 2, 15.0, 24.0, 36, 0.30)
ROSE_ALPHA, ROSE_INNER_ALPHA = 0.075, 0.15   # line opacity of the rosettes
GLOW_R = 40.0                             # radius of the radial navy glow


# Helpers shared by both renderers -----------------------------------------
def guilloche(top: float, bottom: float, spacing: float, a1=2.0, l1=18.0, a2=1.0, l2=8.0,
              p1=0.32, p2=0.55, step=0.6, w=CARD_W):
    """Interwoven sine waves ('banknote' security pattern).

    Returns a list of polylines; each is a list of (x, y) points in mm.
    """
    lines = []
    i = 0
    y = top
    while y <= bottom:
        pts = []
        x = 0.0
        while x <= w + 1e-6:
            yy = y + a1 * math.sin(2 * math.pi * x / l1 + i * p1) + a2 * math.sin(2 * math.pi * x / l2 - i * p2)
            pts.append((round(x, 2), round(yy, 2)))
            x += step
        lines.append(pts)
        y += spacing
        i += 1
    return lines


def rosette(cx: float, cy: float, R: float, n: int, ecc: float, pts: int = 72):
    """Guilloche rosette: n identical ellipses rotated around one centre.

    Their overlap draws the lace-like 'banknote' rose. Returns closed
    polylines [(x, y), ...] in mm.
    """
    lines = []
    for k in range(n):
        th = k * math.pi / n
        ct, st = math.cos(th), math.sin(th)
        poly = []
        for i in range(pts + 1):
            t = 2 * math.pi * i / pts
            x, y = R * math.cos(t), R * ecc * math.sin(t)
            poly.append((round(cx + x * ct - y * st, 2), round(cy + x * st + y * ct, 2)))
        lines.append(poly)
    return lines


def header_curve(side: float, mid: float, drop: float = 0.0):
    """Cubic segments of the header's bottom edge, left -> right.

    Returns (start, [(c1, c2, end), (c1, c2, end)]) in mm.
    """
    s, m = side + drop, mid + drop
    start = (0.0, s)
    segs = [
        ((10.0, s), (17.0, m), (CARD_W / 2, m)),
        ((37.0, m), (44.0, s), (CARD_W, s)),
    ]
    return start, segs


def header_svg_path(side: float, mid: float) -> str:
    start, segs = header_curve(side, mid)
    d = f"M0,0 H{CARD_W} V{side} "
    # right half is traversed right -> left for the closed shape
    d += f"C44,{side} 37,{mid} {CARD_W / 2},{mid} C17,{mid} 10,{side} 0,{side} Z"
    return d


def band_svg_path(side: float, mid: float, t: float = BAND) -> str:
    a, b = side, side + t
    m1, m2 = mid, mid + t
    return (f"M0,{a} C10,{a} 17,{m1} {CARD_W / 2},{m1} C37,{m1} 44,{a} {CARD_W},{a} "
            f"V{b} C44,{b} 37,{m2} {CARD_W / 2},{m2} C17,{m2} 10,{b} 0,{b} Z")


def arch_svg_path(x, top, w, h, rb) -> str:
    r = w / 2
    return (f"M{x},{top + h - rb} L{x},{top + r} A{r},{r} 0 0 1 {x + w},{top + r} "
            f"L{x + w},{top + h - rb} A{rb},{rb} 0 0 1 {x + w - rb},{top + h} "
            f"L{x + rb},{top + h} A{rb},{rb} 0 0 1 {x},{top + h - rb} Z")


def wrap_lines(text: str, width_fn, max_w: float, max_lines: int):
    """Greedy word wrap; width_fn(str)->mm. Last line is trimmed with '...' if needed."""
    words = text.split()
    lines, cur = [], ""
    for wd in words:
        trial = f"{cur} {wd}".strip()
        if width_fn(trial) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = wd
    if cur:
        lines.append(cur)
    if len(lines) > max_lines:
        rest = " ".join(lines[max_lines - 1:])
        lines = lines[:max_lines - 1]
        while rest and width_fn(rest + "...") > max_w:
            rest = rest[:-1]
        lines.append(rest.rstrip() + "...")
    return lines


def balanced_two(text: str, width_fn):
    """Split text into two lines of similar width (None if it has no space)."""
    words = text.split()
    if len(words) < 2:
        return None
    best, best_w = None, 1e9
    for i in range(1, len(words)):
        a, b = " ".join(words[:i]), " ".join(words[i:])
        w = max(width_fn(a), width_fn(b))
        if w < best_w:
            best, best_w = (a, b), w
    return best
