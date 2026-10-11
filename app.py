"""Student ID card generator - Flask backend.

Run:  python app.py   then open http://127.0.0.1:5000
"""
import re

from flask import Flask, abort, jsonify, render_template, request, send_file

import config
from services import design
from services.card_pdf import PHOTO_RATIO, build_card_pdf, find_branding
from services.card_svg import back_svg, front_svg
from services.image_utils import prepare_photo

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB upload cap

ALLOWED_PHOTO_TYPES = {"image/jpeg", "image/png", "image/webp"}


def design_for_js():
    """Numbers the browser needs to lay out the live preview exactly like the PDF."""
    D = design
    return {
        "cx": D.CARD_W / 2, "pt": D.PT,
        "name": {"base": D.ST["name"][1], "max": D.NAME_MAX_W, "oneMin": D.NAME_ONE_LINE_MIN_PT,
                 "twoPt": D.NAME_TWO_LINE_PT, "twoY": D.NAME_TWO_Y, "minPt": 5.8, "y": D.F_NAME_Y},
        "value": {"base": D.ST["value"][1], "max": D.F_VALUE_MAX, "minPt": 4.6, "rows": D.F_ROWS_Y,
                  "x": D.F_VALUE_X, "hair": D.F_ROW_HAIR, "guardMin": D.GUARD_ONE_LINE_MIN_PT,
                  "guardDy": D.GUARD_TWO_DY, "guardHair": D.GUARD_TWO_HAIR},
        "capsule": {"cy": D.F_CAPSULE_CY, "h": D.F_CAPSULE_H},
        "arch": {"x": D.ARCH_X, "top": D.ARCH_TOP, "w": D.PHOTO_W, "h": D.PHOTO_H, "bias": 0.25},
        "addr": {"pt": D.ST["body"][1], "y": D.B_ADDR_Y, "step": D.B_ADDR_STEP, "max": 45.0, "lines": 3},
        "loc": {"base": D.ST["locality"][1], "max": 45.0, "minPt": 4.6},
    }


@app.route("/")
def index():
    return render_template(
        "index.html",
        school=config.SCHOOL,
        classes=config.CLASSES,
        divisions=config.DIVISIONS,
        academic_year=config.current_academic_year(),
        credit=config.CREDIT,
        front_svg=front_svg(config.SCHOOL),
        back_svg=back_svg(config.SCHOOL),
        fonts=design.FONTS,
        d=design_for_js(),
    )


@app.route("/branding/<asset>")
def branding(asset):
    """Serves logo / signature for the live preview (404 if not added yet)."""
    if asset not in ("logo", "signature"):
        abort(404)
    path = find_branding(asset)
    if not path:
        abort(404)
    return send_file(path, max_age=0)


def _clean(value: str) -> str:
    return " ".join((value or "").split())


def _validate(form):
    errors, data = {}, {}

    data["name"] = _clean(form.get("name")).upper()
    if not data["name"]:
        errors["name"] = "Enter the student's name."
    elif len(data["name"]) > 40:
        errors["name"] = "Name is too long (max 40 characters)."

    data["admission_no"] = _clean(form.get("admission_no")).upper()
    if not re.fullmatch(r"[A-Z0-9/\-]{1,15}", data["admission_no"]):
        errors["admission_no"] = "Use letters, numbers, / or - (max 15)."

    data["student_class"] = _clean(form.get("student_class"))
    if data["student_class"] not in config.CLASSES:
        errors["student_class"] = "Select a class."

    data["division"] = _clean(form.get("division")).upper()
    if data["division"] not in config.DIVISIONS:
        errors["division"] = "Select a division."

    data["guardian"] = _clean(form.get("guardian")).upper()
    if not data["guardian"]:
        errors["guardian"] = "Enter the guardian's name."
    elif len(data["guardian"]) > 40:
        errors["guardian"] = "Too long (max 40 characters)."

    mobile = re.sub(r"\D", "", form.get("mobile") or "")
    if len(mobile) == 12 and mobile.startswith("91"):
        mobile = mobile[2:]
    data["mobile"] = mobile
    if not re.fullmatch(r"\d{10}", mobile):
        errors["mobile"] = "Enter a 10-digit mobile number."

    data["locality"] = _clean(form.get("locality"))
    if not data["locality"]:
        errors["locality"] = "Enter the locality."
    elif len(data["locality"]) > 40:
        errors["locality"] = "Too long (max 40 characters)."

    data["address"] = _clean(form.get("address"))
    if not data["address"]:
        errors["address"] = "Enter the address."
    elif len(data["address"]) > 140:
        errors["address"] = "Too long (max 140 characters)."

    data["academic_year"] = _clean(form.get("academic_year")) or config.current_academic_year()
    if not re.fullmatch(r"[0-9]{4}(-[0-9]{2,4})?", data["academic_year"]):
        errors["academic_year"] = "Use a format like 2026-27."

    return data, errors


@app.route("/api/generate", methods=["POST"])
def generate():
    data, errors = _validate(request.form)

    photo = request.files.get("photo")
    photo_bytes = None
    if not photo or not photo.filename:
        errors["photo"] = "Upload the student's photo."
    elif photo.mimetype not in ALLOWED_PHOTO_TYPES:
        errors["photo"] = "Photo must be a JPG, PNG or WEBP image."
    else:
        try:
            photo_bytes = prepare_photo(photo.stream, PHOTO_RATIO)
        except ValueError as exc:
            errors["photo"] = str(exc)

    if errors:
        return jsonify({"errors": errors}), 400

    pdf = build_card_pdf(data, photo_bytes)
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", f'{data["admission_no"]}_{data["name"]}').strip("_")
    return send_file(
        pdf,
        mimetype="application/pdf",
        download_name=f"ID_{safe}.pdf",
        max_age=0,
    )


@app.errorhandler(413)
def too_large(_):
    return jsonify({"errors": {"photo": "Photo is too large (max 8 MB)."}}), 413


if __name__ == "__main__":
    print(f"\n  GHS Chaliyappuram ID Card Generator\n  Open  http://{config.HOST}:{config.PORT}\n")
    app.run(host=config.HOST, port=config.PORT, debug=False)
