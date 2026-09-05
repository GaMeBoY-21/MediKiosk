#!/usr/bin/env python3
# Owner: Nikki
"""Draw the two document images the demo queue uses.

The seeder used to upload a 1x1 PNG. That proved the upload path and nothing
else: the timeline showed a row, and the viewer — whose entire purpose is
letting a doctor check the extracted findings against the paper — opened onto a
single grey pixel. A reviewer looking at that learns nothing about whether the
feature works.

These are deliberately plain: a lab report the patient brought, and a
prescription the clinician attaches. Both are obviously synthetic (fictional
names, a fictional facility) but laid out like the real thing, so the
side-by-side in the viewer shows a doctor comparing a reading against a page.

Regenerate with:  venv/bin/python scripts/make_demo_documents.py
"""

import pathlib

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "assets"

INK = (26, 32, 28)
SOFT = (110, 120, 114)
RULE = (198, 206, 201)
FLAG = (150, 32, 32)


def _font(size: int, bold: bool = False):
    """A real face if the system has one; PIL's bitmap default if not.

    Never raises. A demo asset that fails to build on someone else's machine
    is worse than one that builds ugly.
    """
    for name in (
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def lab_report(path: pathlib.Path) -> None:
    """The patient's own paper: a CBC with two values out of range.

    The out-of-range rows matter. They are what the console flags, so they are
    what a doctor checks the extraction against.
    """
    img = Image.new("RGB", (1000, 880), "white")
    d = ImageDraw.Draw(img)
    h1, h2, body, small = _font(34, True), _font(20, True), _font(20), _font(16)

    d.text((60, 50), "SUNRISE DIAGNOSTIC CENTRE", font=h1, fill=INK)
    d.text((60, 92), "Ward 4, District Hospital Road  ·  Reg. No. 11/2019", font=small, fill=SOFT)
    d.line((60, 128, 940, 128), fill=INK, width=3)

    d.text((60, 150), "Patient:  Anand Pillai", font=body, fill=INK)
    d.text((60, 180), "Age / Sex:  45 / M", font=body, fill=INK)
    d.text((600, 150), "Collected:  02-09-2026", font=body, fill=INK)
    d.text((600, 180), "Sample:  Blood (EDTA)", font=body, fill=INK)

    d.text((60, 240), "COMPLETE BLOOD COUNT", font=h2, fill=INK)
    d.line((60, 272, 940, 272), fill=RULE, width=2)

    cols = (60, 470, 660, 830)
    for label, x in zip(("TEST", "RESULT", "UNIT", "REFERENCE"), cols):
        d.text((x, 288), label, font=small, fill=SOFT)
    d.line((60, 314, 940, 314), fill=RULE, width=1)

    rows = [
        ("Haemoglobin", "10.2", "g/dL", "13.0 - 17.0", True),
        ("Total WBC count", "8,400", "/cumm", "4,000 - 11,000", False),
        ("Platelet count", "2.4", "lakh/cumm", "1.5 - 4.5", False),
        ("Fasting glucose", "156", "mg/dL", "70 - 100", True),
        ("Serum creatinine", "0.9", "mg/dL", "0.7 - 1.3", False),
        ("Total cholesterol", "182", "mg/dL", "< 200", False),
    ]
    y = 336
    for name, value, unit, ref, out in rows:
        colour = FLAG if out else INK
        d.text((cols[0], y), name, font=body, fill=INK)
        d.text((cols[1], y), value + ("  H" if out else ""), font=_font(20, out), fill=colour)
        d.text((cols[2], y), unit, font=body, fill=SOFT)
        d.text((cols[3], y), ref, font=small, fill=SOFT)
        y += 44
        d.line((60, y - 10, 940, y - 10), fill=RULE, width=1)

    d.text((60, y + 30), "Impression:  Anaemia with impaired fasting glucose.", font=body, fill=INK)
    d.text((60, y + 62), "Clinical correlation advised.", font=body, fill=SOFT)
    d.text((60, 790), "Dr. S. Nair, MD (Path)", font=body, fill=INK)
    d.text((60, 826), "This is a synthetic document for demonstration.", font=small, fill=SOFT)

    img.save(path, "PNG", optimize=True)


def prescription(path: pathlib.Path) -> None:
    """What the doctor attaches after the consultation."""
    img = Image.new("RGB", (1000, 1080), "white")
    d = ImageDraw.Draw(img)
    h1, h2, body, small = _font(32, True), _font(20, True), _font(21), _font(16)

    d.text((60, 50), "DISTRICT HOSPITAL  ·  GENERAL OPD", font=h1, fill=INK)
    d.text((60, 92), "Dr. Priya Menon, MBBS MD  ·  Reg. No. KMC 44821", font=small, fill=SOFT)
    d.line((60, 128, 940, 128), fill=INK, width=3)

    d.text((60, 150), "Patient:  Anand Pillai", font=body, fill=INK)
    d.text((60, 182), "Age / Sex:  45 / M", font=body, fill=INK)
    d.text((600, 150), "Date:  05-09-2026", font=body, fill=INK)
    d.text((600, 182), "Token:  A-44", font=body, fill=INK)

    d.text((60, 244), "Dx:  Chronic low back pain.  T2DM on metformin.", font=body, fill=INK)
    d.text((60, 292), "Rx", font=_font(40, True), fill=INK)
    d.line((60, 340, 940, 340), fill=RULE, width=2)

    meds = [
        ("1.  Tab. Metformin 500 mg", "1-0-1", "after food", "30 days"),
        ("2.  Tab. Naproxen 250 mg", "1-0-1", "after food", "5 days"),
        ("3.  Cap. Omeprazole 20 mg", "1-0-0", "before food", "5 days"),
        ("4.  Tab. Vitamin D3 60K IU", "weekly", "—", "8 weeks"),
    ]
    y = 366
    for name, dose, timing, days in meds:
        d.text((60, y), name, font=body, fill=INK)
        d.text((560, y), dose, font=body, fill=INK)
        d.text((700, y), timing, font=small, fill=SOFT)
        d.text((850, y), days, font=small, fill=SOFT)
        y += 58

    d.text((60, y + 30), "Advice:", font=h2, fill=INK)
    for line in (
        "·  Back-strengthening exercises, 10 minutes twice daily.",
        "·  Avoid lifting weights above 5 kg for two weeks.",
        "·  Repeat fasting glucose in 4 weeks.",
    ):
        y += 40
        d.text((80, y + 20), line, font=body, fill=INK)

    d.text((60, y + 130), "Review after 2 weeks, or earlier if pain radiates to the leg.", font=body, fill=INK)
    d.text((620, 960), "Dr. Priya Menon", font=_font(24, True), fill=INK)
    d.line((620, 996, 900, 996), fill=INK, width=2)
    d.text((60, 1026), "This is a synthetic document for demonstration.", font=small, fill=SOFT)

    img.save(path, "PNG", optimize=True)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    lab_report(OUT / "demo_lab_report.png")
    prescription(OUT / "demo_prescription.png")
    for f in sorted(OUT.glob("demo_*.png")):
        print(f"  {f.relative_to(ROOT)}  {f.stat().st_size // 1024} KB")
