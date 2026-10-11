"""Photo preparation: fix rotation, crop to the card's photo ratio, resize."""
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError

OUT_WIDTH = 600  # px; plenty for a 20 mm wide photo at print resolution


def prepare_photo(stream, target_ratio: float) -> BytesIO:
    """Return a cropped JPEG (as BytesIO) with width/height == target_ratio.

    The crop is centred horizontally and biased towards the top vertically,
    so faces in passport-style photos are not cut off.
    (The browser preview uses object-position: center 25% to match.)
    """
    try:
        img = Image.open(stream)
        img = ImageOps.exif_transpose(img)
        img = img.convert("RGB")
    except (UnidentifiedImageError, OSError, ValueError):
        raise ValueError("Please upload a valid image file (JPG, PNG or WEBP).")

    w, h = img.size
    if w / h > target_ratio:
        new_w = int(round(h * target_ratio))
        left = (w - new_w) // 2
        box = (left, 0, left + new_w, h)
    else:
        new_h = int(round(w / target_ratio))
        top = int(round((h - new_h) * 0.25))
        box = (0, top, w, top + new_h)

    img = img.crop(box)
    out_h = int(round(OUT_WIDTH / target_ratio))
    img = img.resize((OUT_WIDTH, out_h), Image.LANCZOS)

    buf = BytesIO()
    img.save(buf, "JPEG", quality=92, optimize=True)
    buf.seek(0)
    return buf
