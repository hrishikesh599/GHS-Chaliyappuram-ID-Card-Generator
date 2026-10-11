"""Project-wide settings.

Edit this file to change school details, class/division lists or the server port.
"""
from datetime import date
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Put the school logo and the headmistress signature in this folder
# (see static/branding/README.txt).
BRANDING_DIR = BASE_DIR / "static" / "branding"

# Server ---------------------------------------------------------------
HOST = "127.0.0.1"   # use "0.0.0.0" to reach it from other PCs on the school network
PORT = 5000

# School ---------------------------------------------------------------
SCHOOL = {
    "name": "GHS CHALIYAPPURAM",
    "address_lines": [
        "EDAVANNAPPARA, CHERUVAYOOR - PO",
        "MALAPPURAM, KERALA - 673645",
    ],
    "email": "ghschaliappuram@gmail.com",
}

CREDIT = "Hrishikesh T Hemanth"

# Dropdown options -------------------------------------------------------
CLASSES = ["5", "6", "7", "8", "9", "10"]
DIVISIONS = list("ABCDEFGH")


def current_academic_year() -> str:
    """Kerala academic year starts in June, e.g. Oct 2026 -> '2026-27'."""
    today = date.today()
    start = today.year if today.month >= 6 else today.year - 1
    return f"{start}-{str(start + 1)[-2:]}"
