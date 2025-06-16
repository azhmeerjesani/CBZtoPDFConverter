#!/usr/bin/env python3
"""
cbz_to_pdf_static.py
~~~~~~~~~~~~~~~~~~~~
Convert every .cbz file in the folder you hard-code below to PDFs that land
next to this script.

Edit INPUT_DIR and run:
    python cbz_to_pdf_static.py
"""

from pathlib import Path
import re
import zipfile
from PIL import Image

# >>>>>>>>>>>>>>>>>>>>>>>  EDIT THIS  <<<<<<<<<<<<<<<<<<<<<<<<<
INPUT_DIR = r"C:\Users\azhme\OneDrive - Clear Creek ISD\Files\Other Folders\Books\Attack On Titan Manga\CBZ"
# e.g. INPUT_DIR = r"C:\Users\me\Comics"
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

# ----------------------------------------------------------------

def _natural_key(text: str):
    """Helps sort files like page2 before page10."""
    return [int(tok) if tok.isdigit() else tok.lower() for tok in re.split(r"(\d+)", text)]

def cbz_to_pdf(cbz_path: Path, out_dir: Path):
    with zipfile.ZipFile(cbz_path) as zf:
        images = [n for n in zf.namelist() if n.lower().endswith((
            ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tif", ".tiff", ".webp"
        ))]
        if not images:
            print(f"[SKIP] {cbz_path.name}: no images detected")
            return
        images.sort(key=_natural_key)

        pages = []
        for name in images:
            with zf.open(name) as fp:
                img = Image.open(fp)
                img.load()  # Load image data into memory
                if img.mode in ("P", "RGBA"):
                    img = img.convert("RGB")
                pages.append(img)

    pdf_path = out_dir / f"{cbz_path.stem}.pdf"
    pages[0].save(pdf_path, "PDF", save_all=True, append_images=pages[1:])
    print(f"[OK]  {pdf_path.name}")

def main():
    source_dir = Path(INPUT_DIR).expanduser().resolve()
    if not source_dir.is_dir():
        raise SystemExit(f"INPUT_DIR not a directory: {source_dir}")

    dest_dir = Path(__file__).parent.resolve()
    print(f"Converting CBZs from {source_dir}\nSaving PDFs to {dest_dir}\n")

    for cbz in sorted(source_dir.glob("*.cbz"), key=lambda p: _natural_key(p.name)):
        cbz_to_pdf(cbz, dest_dir)

if __name__ == "__main__":
    main()
