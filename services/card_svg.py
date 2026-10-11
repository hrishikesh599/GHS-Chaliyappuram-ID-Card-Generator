"""SVG version of the card, used for the live preview in the browser.

It is drawn from the same numbers (services/design.py) and the same fonts as
the PDF, in millimetre user units, so the preview matches the printed card.
Static parts are rendered here; the student's details are filled in by
static/js/app.js (elements carry ids such as f_name, b_addr ...).
"""
from __future__ import annotations

from reportlab.lib.units import mm
from reportlab.pdfbase.pdfmetrics import stringWidth

from services import design as D
from services.card_pdf import _tw  # same text metrics as the PDF
from services.design import CARD_H, CARD_W, PT

CX = CARD_W / 2


# ---------------------------------------------------------------- helpers
def _txt(id_, text, x, y, style, fill, anchor="middle", extra=""):
    key, size, spacing = D.ST[style]
    _, family, weight = D.FONTS[key]
    ident = f' id="{id_}"' if id_ else ""
    return (
        f'<text{ident} x="{x:.2f}" y="{y:.2f}" text-anchor="{anchor}" fill="{fill}" '
        f'font-family="\'{family}\', serif" font-weight="{weight}" '
        f'font-size="{size * PT:.3f}" letter-spacing="{spacing * PT:.3f}" {extra}>{text}</text>'
    )


def _weave(lines, color, opacity, width=0.08, clip=None):
    c = f' clip-path="url(#{clip})"' if clip else ""
    out = [f'<g fill="none" stroke="{color}" stroke-opacity="{opacity}" stroke-width="{width}"{c}>']
    for pts in lines:
        out.append('<polyline points="' + " ".join(f"{x},{y}" for x, y in pts) + '"/>')
    out.append("</g>")
    return "".join(out)


def _diamond(cx, cy, r, fill=D.GOLD):
    return f'<path d="M{cx},{cy - r} L{cx + r},{cy} L{cx},{cy + r} L{cx - r},{cy} Z" fill="{fill}"/>'


def _defs(p, mid, arch=True):
    stops = lambda cols, pos: "".join(f'<stop offset="{o}" stop-color="{c}"/>' for c, o in zip(cols, pos))
    foil = stops(D.FOIL, D.FOIL_POS)
    out = [
        "<defs>",
        f'<linearGradient id="{p}navy" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{CARD_W}" y2="{mid}">'
        + stops([D.NAVY_TOP, D.NAVY, D.NAVY_DEEP], [0, 0.55, 1]) + "</linearGradient>",
        f'<linearGradient id="{p}foilH" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="{CARD_W}" y2="0">{foil}</linearGradient>',
        f'<filter id="{p}blur" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="0.55"/></filter>',
    ]
    return out


def _badge(p, spec, logo_id, mono_id):
    cx, cy, r = spec
    ir = r - 0.5
    return (
        f'<defs><linearGradient id="{p}ring" gradientUnits="userSpaceOnUse" x1="{cx - r}" y1="{cy - r}" x2="{cx + r}" y2="{cy + r}">'
        + "".join(f'<stop offset="{o}" stop-color="{c}"/>' for c, o in zip(D.FOIL, D.FOIL_POS))
        + f'</linearGradient><clipPath id="{p}badgeclip"><circle cx="{cx}" cy="{cy}" r="{ir}"/></clipPath></defs>'
        f'<circle cx="{cx + 0.2}" cy="{cy + 0.4}" r="{r + 0.25}" fill="#000" fill-opacity=".25" filter="url(#{p}blur)"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="url(#{p}ring)"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{ir}" fill="#fff"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r + 0.95}" fill="none" stroke="{D.FOIL[1]}" stroke-opacity=".8" stroke-width=".13"/>'
        + _txt(mono_id, "GHS", cx, cy + r * 0.55 * 0.35, "monogram", D.NAVY,
               extra=f'style="font-size:{r * 0.55:.3f}px"')
        + f'<g clip-path="url(#{p}badgeclip)"><image id="{logo_id}" x="{cx - ir * 0.94:.2f}" y="{cy - ir * 0.94:.2f}" '
          f'width="{ir * 1.88:.2f}" height="{ir * 1.88:.2f}" preserveAspectRatio="xMidYMid meet" visibility="hidden"/></g>'
    )


def _keyline():
    i = D.KEYLINE_INSET
    return (f'<rect x="{i}" y="{i}" width="{CARD_W - 2 * i}" height="{CARD_H - 2 * i}" rx="2" '
            f'fill="none" stroke="{D.GOLD}" stroke-opacity=".8" stroke-width=".17"/>')


def _footer(p, h):
    top = CARD_H - h
    return [
        f'<rect x="0" y="{top}" width="{CARD_W}" height="{h}" fill="url(#{p}navy)"/>',
        f'<rect x="0" y="{top - 0.5}" width="{CARD_W}" height="0.5" fill="url(#{p}foilH)"/>',
    ], top + h / 2


def _header(p, side, mid, rose, inner=None):
    """Navy header: radial glow, guilloche rosette, curved foil band."""
    stops = "".join(f'<stop offset="{o}" stop-color="{c}"/>' for c, o in
                    zip([D.NAVY_GLOW, D.NAVY_TOP, D.NAVY, D.NAVY_DEEP], [0, 0.28, 0.62, 1]))
    out = [
        f'<defs><clipPath id="{p}hclip"><path d="{D.header_svg_path(side, mid)}"/></clipPath>'
        f'<radialGradient id="{p}glow" gradientUnits="userSpaceOnUse" cx="{rose[0]}" cy="{rose[1]}" r="{D.GLOW_R}">{stops}</radialGradient></defs>',
        f'<path d="{D.header_svg_path(side, mid)}" fill="url(#{p}glow)"/>',
        _weave(D.rosette(*rose), "#fff", D.ROSE_ALPHA, 0.07, clip=f"{p}hclip"),
    ]
    if inner:
        out.append(_weave(D.rosette(*inner), D.FOIL[1], D.ROSE_INNER_ALPHA, 0.07, clip=f"{p}hclip"))
    out.append(f'<path d="{D.band_svg_path(side, mid)}" fill="url(#{p}foilH)"/>')
    return out


def _paper():
    return [f'<rect width="{CARD_W}" height="{CARD_H}" fill="{D.PAPER}"/>']


def _section_title(text, y):
    tw = _tw(text, "sec_title")
    gap = 1.8
    yy = y - 0.55
    st = f'stroke="{D.GOLD}" stroke-opacity=".65" stroke-width=".15"'
    return (
        _txt(None, text, CX, y, "sec_title", D.GOLD_DARK)
        + f'<line x1="5" y1="{yy}" x2="{CX - tw / 2 - gap:.2f}" y2="{yy}" {st}/>'
        + f'<line x1="{CX + tw / 2 + gap:.2f}" y1="{yy}" x2="49" y2="{yy}" {st}/>'
    )


def _wrap(svg_inner):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" class="idsvg" viewBox="0 0 {CARD_W} {CARD_H}" '
            f'width="{CARD_W}mm" height="{CARD_H}mm" role="img">{svg_inner}</svg>')


# ------------------------------------------------------------------ front
def front_svg(school: dict) -> str:
    p = "f_"
    o = _defs(p, D.FRONT_MID)
    o.append("</defs>")
    o += _paper()
    o += _header(p, D.FRONT_SIDE, D.FRONT_MID, D.F_ROSETTE, D.F_ROSETTE_INNER)
    o.append(_badge(p, D.F_LOGO, "f_logo", "f_mono"))
    o.append(_txt("f_school", school["name"], CX, D.F_SCHOOL_Y, "school", "#fff"))
    kw = _tw("STUDENT IDENTITY CARD", "kicker")
    ky = D.F_KICKER_Y - 0.5
    kst = f'stroke="{D.FOIL[1]}" stroke-opacity=".55" stroke-width=".14"'
    o.append(_txt(None, "STUDENT IDENTITY CARD", CX, D.F_KICKER_Y, "kicker", D.FOIL[1]))
    o.append(f'<line x1="5.5" y1="{ky}" x2="{CX - kw / 2 - 2.0:.2f}" y2="{ky}" {kst}/>')
    o.append(f'<line x1="{CX + kw / 2 + 2.0:.2f}" y1="{ky}" x2="{CARD_W - 5.5}" y2="{ky}" {kst}/>')

    # Arched photo window
    x, top, w, h = D.ARCH_X, D.ARCH_TOP, D.PHOTO_W, D.PHOTO_H
    g, m, rb = D.FRAME_GROW, D.MAT_GROW, D.ARCH_BOTTOM_R
    o.append(
        f'<defs><linearGradient id="{p}archfoil" gradientUnits="userSpaceOnUse" x1="{x - g}" y1="{top - g}" x2="{x + w + g}" y2="{top + h + g}">'
        + "".join(f'<stop offset="{po}" stop-color="{c}"/>' for c, po in zip(D.FOIL, D.FOIL_POS))
        + f'</linearGradient><clipPath id="{p}archclip"><path d="{D.arch_svg_path(x, top, w, h, rb)}"/></clipPath></defs>'
    )
    for grow, a in D.ARCH_SHADOW:
        o.append(f'<path d="{D.arch_svg_path(x - grow, top - grow + D.ARCH_SHADOW_DY, w + 2 * grow, h + 2 * grow, rb + grow)}" fill="#0A1F40" fill-opacity="{a}"/>')
    o.append(f'<path d="{D.arch_svg_path(x - g, top - g, w + 2 * g, h + 2 * g, rb + g)}" fill="url(#{p}archfoil)"/>')
    o.append(f'<path d="{D.arch_svg_path(x - m, top - m, w + 2 * m, h + 2 * m, rb + m)}" fill="#fff"/>')
    o.append(
        f'<g clip-path="url(#{p}archclip)"><rect x="{x}" y="{top}" width="{w}" height="{h}" fill="#E9E4D4"/>'
        f'<g id="f_silhouette" fill="#CFC8B2"><circle cx="{CX}" cy="{top + 10.5}" r="4.6"/>'
        f'<path d="M{x + 3},{top + h} C{x + 3},{top + 18} {x + 7},{top + 16.5} {CX},{top + 16.5} C{x + w - 7},{top + 16.5} {x + w - 3},{top + 18} {x + w - 3},{top + h} Z"/></g>'
        f'<image id="f_photo" x="{x}" y="{top}" width="{w}" height="{h}" preserveAspectRatio="none" visibility="hidden"/></g>'
    )

    # Name (1-2 lines), class capsule
    o.append(_txt("f_name1", "", CX, D.F_NAME_Y, "name", D.NAVY))
    o.append(_txt("f_name2", "", CX, D.NAME_TWO_Y[1], "name", D.NAVY))
    o.append(f'<rect id="f_cap_rect" x="{CX - 12}" y="{D.F_CAPSULE_CY - D.F_CAPSULE_H / 2}" width="24" height="{D.F_CAPSULE_H}" '
             f'rx="{D.F_CAPSULE_H / 2}" fill="{D.NAVY}" stroke="{D.GOLD}" stroke-width=".15"/>')
    o.append(_txt("f_cap_text", "", CX, D.F_CAPSULE_CY + 0.52, "capsule", D.FOIL[1]))

    # Detail rows
    labels = ("ADM. NO", "GUARDIAN", "MOBILE")
    ids = ("f_adm", "f_guardian", "f_mobile")
    for i, (lab, ident) in enumerate(zip(labels, ids)):
        y = D.F_ROWS_Y[i]
        o.append(_txt(f"f_lab{i}", lab, D.F_LABEL_X, y, "label", D.GOLD_DARK, "start"))
        o.append(_txt(ident + "1", "", D.F_VALUE_X, y, "value", D.NAVY, "start"))
        o.append(_txt(ident + "2", "", D.F_VALUE_X, y + D.GUARD_TWO_DY[1], "value", D.NAVY, "start"))
    for i in range(2):
        y = D.F_ROWS_Y[i] + D.F_ROW_HAIR
        o.append(f'<line id="f_hair{i}" x1="5" y1="{y:.2f}" x2="49" y2="{y:.2f}" stroke="{D.RULE}" stroke-width=".18"/>')

    foot, mid = _footer(p, D.FRONT_FOOT)
    o += foot
    o.append(_txt("f_year", "", CX, mid + 0.5, "footer", "#fff"))
    o.append(_diamond(11.5, mid, 0.6))
    o.append(_diamond(CARD_W - 11.5, mid, 0.6))
    o.append(_keyline())
    return _wrap("".join(o))


# ------------------------------------------------------------------- back
def back_svg(school: dict) -> str:
    p = "b_"
    o = _defs(p, D.BACK_MID)
    o.append("</defs>")
    o += _paper()
    o += _header(p, D.BACK_SIDE, D.BACK_MID, D.B_ROSETTE)
    o.append(_txt("b_school", school["name"], CX, D.B_SCHOOL_Y, "school", "#fff"))
    o.append(_badge(p, D.B_LOGO, "b_logo", "b_mono"))

    o.append(_section_title("ADDRESS", D.B_ADDR_TITLE_Y))
    o.append(_txt("b_addr", "", CX, D.B_ADDR_Y, "body", D.INK))
    o.append(_section_title("LOCALITY", D.B_LOC_TITLE_Y))
    o.append(_txt("b_loc", "", CX, D.B_LOC_Y, "locality", D.INK))

    px, ptop, pw, ph = D.B_PANEL
    o.append(f'<rect x="{px}" y="{ptop}" width="{pw}" height="{ph}" rx="1.4" fill="{D.PANEL}" '
             f'stroke="{D.GOLD}" stroke-opacity=".7" stroke-width=".15"/>')
    o.append(_txt(None, "IF FOUND, PLEASE RETURN TO", CX, D.B_RET_TITLE_Y, "sec_title", D.GOLD_DARK))
    o.append(_txt(None, school["name"], CX, D.B_RET_SCHOOL_Y, "ret_school", D.NAVY))
    y = D.B_RET_ADDR_Y
    for ln in school["address_lines"]:
        o.append(_txt(None, ln, CX, y, "ret_addr", D.INK))
        y += D.B_RET_STEP

    sl = D.B_SIG_LINE_Y
    bw, bh = D.B_SIG_BOX
    o.append(f'<image id="b_sig" x="{CX - bw / 2}" y="{sl - bh - 0.4}" width="{bw}" height="{bh}" '
             f'preserveAspectRatio="xMidYMid meet" visibility="hidden"/>')
    o.append(f'<line x1="{CX - 14}" y1="{sl}" x2="{CX + 14}" y2="{sl}" stroke="{D.NAVY}" stroke-width=".2"/>')
    o.append(_txt(None, "HEADMISTRESS", CX, sl + 3.0, "sig_title", D.NAVY))
    o.append(_txt(None, school["name"], CX, sl + 5.6, "sig_sub", D.MUTED))

    foot, mid = _footer(p, D.BACK_FOOT)
    o += foot
    o.append(_txt(None, school["email"], CX, mid + 0.5, "email", "#fff"))
    o.append(_keyline())
    return _wrap("".join(o))
