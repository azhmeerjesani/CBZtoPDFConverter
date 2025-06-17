#!/usr/bin/env python3
"""
cbz_to_pdf_static.py
~~~~~~~~~~~~~~~~~~~~
Convert every .cbz file in the folder you hard-code below to PDFs that land
next to this script.
Memory efficient version with batch processing.

Edit INPUT_DIR and run:
    python cbz_to_pdf_static.py
"""

from pathlib import Path
import re
import zipfile
from PIL import Image
import gc
from io import BytesIO

# >>>>>>>>>>>>>>>>>>>>>>>  EDIT THIS  <<<<<<<<<<<<<<<<<<<<<<<<<
INPUT_DIR = r"C:\Users\azhme\OneDrive - Clear Creek ISD\Files\Other Folders\Books\Attack On Titan Manga\CBZ"
BATCH_SIZE = 5  # Process images in batches to manage memory
MAX_IMAGE_SIZE = (1200, 1600)  # Smaller max size for manga pages
JPEG_QUALITY = 60  # Lower quality for smaller file size
TARGET_DPI = 100  # Lower DPI for smaller files
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

# ----------------------------------------------------------------

def _natural_key(text: str):
    """Helps sort files like page2 before page10."""
    return [int(tok) if tok.isdigit() else tok.lower() for tok in re.split(r"(\d+)", text)]

def optimize_image(img: Image.Image) -> Image.Image:
    """Optimize image for PDF conversion to reduce file size significantly."""
    # More aggressive resizing for manga
    if img.size[0] > MAX_IMAGE_SIZE[0] or img.size[1] > MAX_IMAGE_SIZE[1]:
        img.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
    
    # Convert to RGB if needed
    if img.mode in ("P", "RGBA"):
        img = img.convert("RGB")
    elif img.mode == "L":
        # Keep grayscale for smaller file size if it's already grayscale
        pass
    else:
        img = img.convert("RGB")
    
    return img

def cbz_to_pdf(cbz_path: Path, out_dir: Path):
    """Memory efficient CBZ to PDF conversion with aggressive compression."""
    try:
        with zipfile.ZipFile(cbz_path, 'r') as zf:
            images = [n for n in zf.namelist() if n.lower().endswith((
                ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tif", ".tiff", ".webp"
            ))]
            if not images:
                print(f"[SKIP] {cbz_path.name}: no images detected")
                return
            images.sort(key=_natural_key)

            pdf_path = out_dir / f"{cbz_path.stem}.pdf"
            all_pages = []
            
            # Process images in batches
            for i in range(0, len(images), BATCH_SIZE):
                batch = images[i:i + BATCH_SIZE]
                batch_pages = []
                
                for name in batch:
                    try:
                        with zf.open(name) as fp:
                            img_data = fp.read()
                        
                        # Load image from memory
                        img = Image.open(BytesIO(img_data))
                        img = optimize_image(img)
                        batch_pages.append(img)
                        
                    except Exception as e:
                        print(f"[WARN] Failed to process {name}: {e}")
                        continue
                
                all_pages.extend(batch_pages)
                
                # Force garbage collection after each batch
                gc.collect()
                
                print(f"Processed batch {i//BATCH_SIZE + 1}/{(len(images) + BATCH_SIZE - 1)//BATCH_SIZE} for {cbz_path.name}")

            if not all_pages:
                print(f"[SKIP] {cbz_path.name}: no valid images processed")
                return

            # Save PDF with aggressive compression
            save_kwargs = {
                "format": "PDF",
                "save_all": True,
                "append_images": all_pages[1:] if len(all_pages) > 1 else [],
                "optimize": True,
                "quality": JPEG_QUALITY,
                "resolution": TARGET_DPI,
                "compress_level": 9  # Maximum compression
            }
            
            # For very large PDFs, try additional compression
            if len(all_pages) > 50:  # Assume large file if many pages
                save_kwargs["quality"] = 50  # Even lower quality for large files
                save_kwargs["resolution"] = 90
                
            all_pages[0].save(pdf_path, **save_kwargs)
            
            # Check file size and warn if still large
            file_size_mb = pdf_path.stat().st_size / (1024 * 1024)
            if file_size_mb > 100:
                print(f"[WARN] {pdf_path.name} is {file_size_mb:.1f}MB (target: <100MB)")
            else:
                print(f"[OK]  {pdf_path.name} ({len(all_pages)} pages, {file_size_mb:.1f}MB)")
            
    except Exception as e:
        print(f"[ERROR] Failed to process {cbz_path.name}: {e}")
    finally:
        # Clean up memory
        if 'all_pages' in locals():
            for img in all_pages:
                img.close()
        gc.collect()

def main():
    source_dir = Path(INPUT_DIR).expanduser().resolve()
    if not source_dir.is_dir():
        raise SystemExit(f"INPUT_DIR not a directory: {source_dir}")

    dest_dir = Path(__file__).parent.resolve()
    print(f"Converting CBZs from {source_dir}\nSaving PDFs to {dest_dir}\n")

    try:
        cbz_files = sorted(source_dir.glob("*.cbz"), key=lambda p: _natural_key(p.name))
        total_files = len(cbz_files)
        
        for i, cbz in enumerate(cbz_files, 1):
            print(f"\n[{i}/{total_files}] Processing {cbz.name}")
            cbz_to_pdf(cbz, dest_dir)
            
            # Memory cleanup between files
            gc.collect()
            
    except KeyboardInterrupt:
        print("\nConversion interrupted by user")
    except Exception as e:
        print(f"Error during conversion: {e}")

if __name__ == "__main__":
    main()
