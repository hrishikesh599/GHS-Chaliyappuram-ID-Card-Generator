"""Draws the two-page (front + back) student ID card as a print-ready PDF.

Card size is CR80 (credit-card size) in portrait: 54 mm x 85.6 mm.
Every position and size comes from services/design.py (millimetres from the
top-left), shared with the on-screen preview (services/card_svg.py).
"""
from __future__ import annotations

from io import BytesIO

from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

import config
from services import design as D
from services.design import CARD_H, CARD_W, PT, balanced_two, wrap_lines

PHOTO_RATIO = D.PHOTO_RATIO

W = CARD_W * mm
H = CARD_H * mm

for _key, (_name, _css, _w) in D.FONTS.items():
    pdfmetrics.registerFont(TTFont(_name, str(D.FONT_DIR / f"{_name}.ttf")))

hx = HexColor
NAVY, NAVY_TOP, NAVY_DEEP = hx(D.NAVY), hx(D.NAVY_TOP), hx(D.NAVY_DEEP)
GOLD, GOLD_DARK = hx(D.GOLD), hx(D.GOLD_DARK)
PAPER, INK, MUTED, RULE = hx(D.PAPER), hx(D.INK), hx(D.MUTED), hx(D.RULE)
FOIL = [hx(h) for h in D.FOIL]
FOIL_LIGHT = FOIL[1]
NAVY_STOPS = ([NAVY_TOP, NAVY, NAVY_DEEP], [0, 0.55, 1])

_EXTS = (".png", ".jpg", ".jpeg", ".webp")


def Y(top_mm: float) -> float:
    """'mm from the top' -> PDF y coordinate."""
    return H - top_mm * mm


def find_branding(stem: str):
    """Locate logo.* / signature.* in the branding folder (or None)."""
    for ext in _EXTS:
        p = config.BRANDING_DIR / f"{stem}{ext}"
        if p.is_file():
            return p
    return None


# ------------------------------------------------------------------ text
def _font(style):
    return D.FONTS[D.ST[style][0]][0]


def _tw(text, style, size=None):
    """Text width in mm (letter-spacing included)."""
    key, sz, sp = D.ST[style]
    sz = size or sz
    return (stringWidth(text, D.FONTS[key][0], sz) + sp * max(len(text) - 1, 0)) / mm


def _fit_size(text, style, max_mm, min_pt=4.6):
    size = D.ST[style][1]
    while size > min_pt and _tw(text, style, size) > max_mm:
        size -= 0.1
    return size


def _text(c, text, x_mm, y_mm, style, color, anchor="middle", size=None):
    """Draw letter-spaced text; x is the centre / left / right per `anchor`."""
    key, sz, sp = D.ST[style]
    sz = size or sz
    font = D.FONTS[key][0]
    w = stringWidth(text, font, sz) + sp * max(len(text) - 1, 0)
    x = x_mm * mm
    if anchor == "middle":
        x -= w / 2
    elif anchor == "end":
        x -= w
    c.setFillColor(color)
    t = c.beginText()
    t.setFont(font, sz)
    t.setCharSpace(sp)
    t.setTextOrigin(x, Y(y_mm))
    t.textOut(text)
    t.setCharSpace(0)   # Tc persists in the page state - always reset
    c.drawText(t)


def _fit_text(c, text, x_mm, y_mm, style, color, max_mm, min_pt=4.6, anchor="middle"):
    """Shrink to fit; trim with '...' only as a last resort."""
    size = _fit_size(text, style, max_mm, min_pt)
    if _tw(text, style, size) > max_mm:
        while text and _tw(text + "...", style, size) > max_mm:
            text = text[:-1]
        text = text.rstrip() + "..."
    _text(c, text, x_mm, y_mm, style, color, anchor, size)


# --------------------------------------------------------------- shapes
def _clip(c, path):
    c.saveState()
    c.clipPath(path, stroke=0, fill=0)


def _rect_path(c, x, y, w, h):
    p = c.beginPath()
    p.rect(x, y, w, h)
    return p


def _foil(c, path, x0, y0, x1, y1):
    _clip(c, path)
    c.linearGradient(x0, y0, x1, y1, FOIL, D.FOIL_POS, extend=True)
    c.restoreState()


def _navy(c, path, x0, y0, x1, y1):
    _clip(c, path)
    c.linearGradient(x0, y0, x1, y1, *NAVY_STOPS, extend=True)
    c.restoreState()


def _diamond(c, cx_mm, cy_mm, r_mm, color=GOLD):
    cx, cy, r = cx_mm * mm, Y(cy_mm), r_mm * mm
    p = c.beginPath()
    p.moveTo(cx, cy + r)
    p.lineTo(cx + r, cy)
    p.lineTo(cx, cy - r)
    p.lineTo(cx - r, cy)
    p.close()
    c.setFillColor(color)
    c.drawPath(p, stroke=0, fill=1)


def _header_path(c, side, mid):
    p = c.beginPath()
    p.moveTo(0, H)
    p.lineTo(W, H)
    p.lineTo(W, Y(side))
    p.curveTo(44 * mm, Y(side), 37 * mm, Y(mid), W / 2, Y(mid))
    p.curveTo(17 * mm, Y(mid), 10 * mm, Y(side), 0, Y(side))
    p.close()
    return p


def _band_path(c, side, mid, t=D.BAND):
    p = c.beginPath()
    p.moveTo(0, Y(side))
    p.curveTo(10 * mm, Y(side), 17 * mm, Y(mid), W / 2, Y(mid))
    p.curveTo(37 * mm, Y(mid), 44 * mm, Y(side), W, Y(side))
    p.lineTo(W, Y(side + t))
    p.curveTo(44 * mm, Y(side + t), 37 * mm, Y(mid + t), W / 2, Y(mid + t))
    p.curveTo(17 * mm, Y(mid + t), 10 * mm, Y(side + t), 0, Y(side + t))
    p.close()
    return p


def _arch_path(c, x, top, w, h, rb):
    """Arched window: semicircular top, softly rounded bottom corners."""
    r = w / 2
    p = c.beginPath()
    p.moveTo(x * mm, Y(top + h - rb))
    p.lineTo(x * mm, Y(top + r))
    p.arcTo(x * mm, Y(top + w), (x + w) * mm, Y(top), startAng=180, extent=-180)
    p.lineTo((x + w) * mm, Y(top + h - rb))
    p.arcTo((x + w - 2 * rb) * mm, Y(top + h), (x + w) * mm, Y(top + h - 2 * rb), startAng=0, extent=-90)
    p.lineTo((x + rb) * mm, Y(top + h))
    p.arcTo(x * mm, Y(top + h), (x + 2 * rb) * mm, Y(top + h - 2 * rb), startAng=270, extent=-90)
    p.close()
    return p


def _weave(c, lines, color, alpha, width=0.08):
    c.setStrokeColor(color)
    c.setStrokeAlpha(alpha)
    c.setLineWidth(width * mm)
    for pts in lines:
        p = c.beginPath()
        p.moveTo(pts[0][0] * mm, Y(pts[0][1]))
        for x, y in pts[1:]:
            p.lineTo(x * mm, Y(y))
        c.drawPath(p, stroke=1, fill=0)
    c.setStrokeAlpha(1)


# ------------------------------------------------------------ components
def _paper(c):
    c.setFillColor(PAPER)
    c.rect(0, 0, W, H, stroke=0, fill=1)


def _header(c, side, mid, rose, inner=None):
    """Navy header: radial glow, guilloche rosette, curved foil band."""
    _clip(c, _header_path(c, side, mid))
    c.setFillColor(NAVY_DEEP)
    c.rect(0, 0, W, H, stroke=0, fill=1)
    c.radialGradient(rose[0] * mm, Y(rose[1]), D.GLOW_R * mm,
                     [hx(D.NAVY_GLOW), NAVY_TOP, NAVY, NAVY_DEEP], [0, 0.28, 0.62, 1], extend=True)
    _weave(c, D.rosette(*rose), white, D.ROSE_ALPHA, 0.07)
    if inner:
        _weave(c, D.rosette(*inner), FOIL_LIGHT, D.ROSE_INNER_ALPHA, 0.07)
    c.restoreState()
    _foil(c, _band_path(c, side, mid), 0, 0, W, 0)


def _footer(c, h_mm):
    """Navy gradient band with a foil strip on top; returns its top edge (mm)."""
    _navy(c, _rect_path(c, 0, 0, W, h_mm * mm), 0, h_mm * mm, W, 0)
    _foil(c, _rect_path(c, 0, h_mm * mm, W, 0.5 * mm), 0, 0, W, 0)
    return CARD_H - h_mm


def _keyline(c):
    i = D.KEYLINE_INSET * mm
    c.setStrokeColor(GOLD)
    c.setStrokeAlpha(0.8)
    c.setLineWidth(0.17 * mm)
    c.roundRect(i, i, W - 2 * i, H - 2 * i, 2.0 * mm, stroke=1, fill=0)
    c.setStrokeAlpha(1)


def _badge(c, spec, logo_path):
    """Round crest: soft shadow, gold foil ring, white disc, logo (or monogram)."""
    cx_mm, cy_mm, r_mm = spec
    cx, cy, r = cx_mm * mm, Y(cy_mm), r_mm * mm
    c.setFillColor(Color(0, 0, 0, alpha=0.25))
    c.circle(cx + 0.2 * mm, cy - 0.4 * mm, r + 0.25 * mm, stroke=0, fill=1)
    c.setFillAlpha(1)
    ring = c.beginPath()
    ring.circle(cx, cy, r)
    _clip(c, ring)
    c.linearGradient(cx - r, cy + r, cx + r, cy - r, FOIL, D.FOIL_POS, extend=True)
    c.restoreState()
    ir = r - 0.5 * mm
    c.setFillColor(white)
    c.circle(cx, cy, ir, stroke=0, fill=1)
    c.setStrokeColor(FOIL_LIGHT)          # fine outer ring
    c.setStrokeAlpha(0.8)
    c.setLineWidth(0.13 * mm)
    c.circle(cx, cy, r + 0.95 * mm, stroke=1, fill=0)
    c.setStrokeAlpha(1)
    if logo_path:
        clip = c.beginPath()
        clip.circle(cx, cy, ir)
        _clip(c, clip)
        side = 2 * ir * 0.94
        c.drawImage(ImageReader(str(logo_path)), cx - side / 2, cy - side / 2, side, side,
                    preserveAspectRatio=True, anchor="c", mask="auto")
        c.restoreState()
    else:
        size_pt = (r_mm * 0.55) / PT
        _text(c, "GHS", cx_mm, cy_mm + r_mm * 0.55 * 0.35, "monogram", NAVY, "middle", size_pt)


def _section_title(c, text, y_mm):
    """Centred caption flanked by thin gold hairlines."""
    cx = CARD_W / 2
    tw = _tw(text, "sec_title")
    _text(c, text, cx, y_mm, "sec_title", GOLD_DARK)
    c.setStrokeColor(GOLD)
    c.setStrokeAlpha(0.65)
    c.setLineWidth(0.15 * mm)
    gap = 1.8
    yy = Y(y_mm - 0.55)
    c.line(5 * mm, yy, (cx - tw / 2 - gap) * mm, yy)
    c.line((cx + tw / 2 + gap) * mm, yy, 49 * mm, yy)
    c.setStrokeAlpha(1)


# ----------------------------------------------------------------- front
def _front(c, d, photo_bytes, logo, school):
    _paper(c)
    _header(c, D.FRONT_SIDE, D.FRONT_MID, D.F_ROSETTE, D.F_ROSETTE_INNER)

    _badge(c, D.F_LOGO, logo)
    _fit_text(c, school["name"], CARD_W / 2, D.F_SCHOOL_Y, "school", white, 48, 5.5)
    kw = _tw("STUDENT IDENTITY CARD", "kicker")
    _text(c, "STUDENT IDENTITY CARD", CARD_W / 2, D.F_KICKER_Y, "kicker", FOIL_LIGHT)
    c.setStrokeColor(FOIL_LIGHT)
    c.setStrokeAlpha(0.55)
    c.setLineWidth(0.14 * mm)
    ky = Y(D.F_KICKER_Y - 0.5)
    c.line(5.5 * mm, ky, (CARD_W / 2 - kw / 2 - 2.0) * mm, ky)
    c.line((CARD_W / 2 + kw / 2 + 2.0) * mm, ky, (CARD_W - 5.5) * mm, ky)
    c.setStrokeAlpha(1)

    # Arched photo: shadow, foil frame, white mat, photo
    x, top, w, h = D.ARCH_X, D.ARCH_TOP, D.PHOTO_W, D.PHOTO_H
    for grow, a in D.ARCH_SHADOW:
        c.setFillColor(Color(0.04, 0.12, 0.25, alpha=a))
        c.drawPath(_arch_path(c, x - grow, top - grow + D.ARCH_SHADOW_DY, w + 2 * grow, h + 2 * grow,
                              D.ARCH_BOTTOM_R + grow), stroke=0, fill=1)
    c.setFillAlpha(1)
    g, m = D.FRAME_GROW, D.MAT_GROW
    _foil(c, _arch_path(c, x - g, top - g, w + 2 * g, h + 2 * g, D.ARCH_BOTTOM_R + g),
          (x - g) * mm, Y(top - g), (x + w + g) * mm, Y(top + h + g))
    c.setFillColor(white)
    c.drawPath(_arch_path(c, x - m, top - m, w + 2 * m, h + 2 * m, D.ARCH_BOTTOM_R + m), stroke=0, fill=1)
    _clip(c, _arch_path(c, x, top, w, h, D.ARCH_BOTTOM_R))
    c.drawImage(ImageReader(photo_bytes), x * mm, Y(top + h), w * mm, h * mm)
    c.restoreState()

    # Name (wraps to two lines when very long) + class capsule
    name = d["name"]
    if _fit_size(name, "name", D.NAME_MAX_W, 1) >= D.NAME_ONE_LINE_MIN_PT or " " not in name:
        _fit_text(c, name, CARD_W / 2, D.F_NAME_Y, "name", NAVY, D.NAME_MAX_W, 5.8)
    else:
        a, b = balanced_two(name, lambda s: _tw(s, "name", D.NAME_TWO_LINE_PT))
        sz = min(D.NAME_TWO_LINE_PT, _fit_size(a, "name", D.NAME_MAX_W, 5.8), _fit_size(b, "name", D.NAME_MAX_W, 5.8))
        _text(c, a, CARD_W / 2, D.NAME_TWO_Y[0], "name", NAVY, "middle", sz)
        _text(c, b, CARD_W / 2, D.NAME_TWO_Y[1], "name", NAVY, "middle", sz)
    cap = f'CLASS {d["student_class"]}  ·  DIV {d["division"]}'
    cw, ch = _tw(cap, "capsule") + 7.0, D.F_CAPSULE_H
    cx0 = (CARD_W - cw) / 2
    c.setFillColor(NAVY)
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.15 * mm)
    c.roundRect(cx0 * mm, Y(D.F_CAPSULE_CY + ch / 2), cw * mm, ch * mm, ch / 2 * mm, stroke=1, fill=1)
    _text(c, cap, CARD_W / 2, D.F_CAPSULE_CY + 0.52, "capsule", FOIL_LIGHT)

    # Detail rows
    mob = d["mobile"]
    rows = [("ADM. NO", d["admission_no"]), ("GUARDIAN", d["guardian"]), ("MOBILE", f"{mob[:5]} {mob[5:]}")]
    for i, (label, value) in enumerate(rows):
        y = D.F_ROWS_Y[i]
        _text(c, label, D.F_LABEL_X, y, "label", GOLD_DARK, "start")
        hair = D.F_ROW_HAIR
        wrapped = None
        if _fit_size(value, "value", D.F_VALUE_MAX, 1) < D.GUARD_ONE_LINE_MIN_PT and " " in value and label == "GUARDIAN":
            wrapped = balanced_two(value, lambda s: _tw(s, "value", D.GUARD_ONE_LINE_MIN_PT))
        if wrapped:
            sz = min(D.GUARD_ONE_LINE_MIN_PT, *[_fit_size(t, "value", D.F_VALUE_MAX, 4.2) for t in wrapped])
            for t, dy in zip(wrapped, D.GUARD_TWO_DY):
                _text(c, t, D.F_VALUE_X, y + dy, "value", NAVY, "start", sz)
            hair = D.GUARD_TWO_HAIR
        else:
            _fit_text(c, value, D.F_VALUE_X, y, "value", NAVY, D.F_VALUE_MAX, 4.6, "start")
        if i < len(rows) - 1:
            c.setStrokeColor(RULE)
            c.setLineWidth(0.18 * mm)
            c.line(5 * mm, Y(y + hair), 49 * mm, Y(y + hair))

    # Footer
    mid = _footer(c, D.FRONT_FOOT) + D.FRONT_FOOT / 2
    _text(c, f'ACADEMIC YEAR {d["academic_year"]}', CARD_W / 2, mid + 0.5, "footer", white)
    _diamond(c, 11.5, mid, 0.6)
    _diamond(c, CARD_W - 11.5, mid, 0.6)
    _keyline(c)


# ------------------------------------------------------------------ back
def _back(c, d, signature, logo, school):
    _paper(c)
    _header(c, D.BACK_SIDE, D.BACK_MID, D.B_ROSETTE)
    _fit_text(c, school["name"], CARD_W / 2, D.B_SCHOOL_Y, "school", white, 46, 5.5)
    _badge(c, D.B_LOGO, logo)
    cx = CARD_W / 2

    # Address
    _section_title(c, "ADDRESS", D.B_ADDR_TITLE_Y)
    font, size = _font("body"), D.ST["body"][1]
    y = D.B_ADDR_Y
    for ln in wrap_lines(d["address"], lambda s: stringWidth(s, font, size) / mm, 45.0, 3):
        _text(c, ln, cx, y, "body", INK)
        y += D.B_ADDR_STEP

    # Locality
    _section_title(c, "LOCALITY", D.B_LOC_TITLE_Y)
    _fit_text(c, d["locality"], cx, D.B_LOC_Y, "locality", INK, 45, 4.6)

    # Return address, in a tinted panel
    px, ptop, pw, ph = D.B_PANEL
    c.setFillColor(hx(D.PANEL))
    c.setStrokeColor(GOLD)
    c.setStrokeAlpha(0.7)
    c.setLineWidth(0.15 * mm)
    c.roundRect(px * mm, Y(ptop + ph), pw * mm, ph * mm, 1.4 * mm, stroke=1, fill=1)
    c.setStrokeAlpha(1)
    _text(c, "IF FOUND, PLEASE RETURN TO", cx, D.B_RET_TITLE_Y, "sec_title", GOLD_DARK)
    _text(c, school["name"], cx, D.B_RET_SCHOOL_Y, "ret_school", NAVY)
    y = D.B_RET_ADDR_Y
    for ln in school["address_lines"]:
        _text(c, ln, cx, y, "ret_addr", INK)
        y += D.B_RET_STEP

    # Signature block
    sl = D.B_SIG_LINE_Y
    if signature:
        bw, bh = D.B_SIG_BOX
        c.drawImage(ImageReader(str(signature)), (cx - bw / 2) * mm, Y(sl) + 0.4 * mm, bw * mm, bh * mm,
                    preserveAspectRatio=True, anchor="c", mask="auto")
    c.setStrokeColor(NAVY)
    c.setLineWidth(0.2 * mm)
    c.line((cx - 14) * mm, Y(sl), (cx + 14) * mm, Y(sl))
    _text(c, "HEADMISTRESS", cx, sl + 3.0, "sig_title", NAVY)
    _text(c, school["name"], cx, sl + 5.6, "sig_sub", MUTED)

    # Footer with e-mail
    mid = _footer(c, D.BACK_FOOT) + D.BACK_FOOT / 2
    _text(c, school["email"], cx, mid + 0.5, "email", white)
    _keyline(c)


# ---------------------------------------------------------------- public
def build_card_pdf(data: dict, photo_bytes: BytesIO) -> BytesIO:
    """Return a 2-page PDF (front, back) as a BytesIO."""
    school = config.SCHOOL
    logo = find_branding("logo")
    signature = find_branding("signature")

    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=(W, H))
    c.setTitle(f'ID Card - {data["name"]}')
    c.setAuthor(school["name"])
    c.setSubject("Student Identity Card")
    c.setCreator(f"ID Card Generator by {config.CREDIT}")

    _front(c, data, photo_bytes, logo, school)
    c.showPage()
    _back(c, data, signature, logo, school)
    c.showPage()
    c.save()
    buf.seek(0)
    return buf
