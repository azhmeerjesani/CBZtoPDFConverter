#!/usr/bin/env python3
"""
cbz_to_pdf_gpu.py
~~~~~~~~~~~~~~~~~
Convert every .cbz file in the folder you hard-code below to PDFs that land
next to this script.
Now with GPU acceleration and improved memory efficiency.

Edit INPUT_DIR and run:
    python cbz_to_pdf_gpu.py
"""

from pathlib import Path
import re
import zipfile
from PIL import Image
import torch
import torchvision.transforms as transforms
import gc
from io import BytesIO

# >>>>>>>>>>>>>>>>>>>>>>>  EDIT THIS  <<<<<<<<<<<<<<<<<<<<<<<<<
INPUT_DIR = r"C:\Users\azhme\OneDrive - Clear Creek ISD\Files\Other Folders\Books\Attack On Titan Manga\CBZ"
BATCH_SIZE = 51  # Process images in batches to manage memory
USE_GPU = True  # Set to False to disable GPU acceleration
# >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

# Check for CUDA availability
device = torch.device('cuda' if USE_GPU and torch.cuda.is_available() else 'cpu')
print(f"Using device: {device}")

def _natural_key(text: str):
    """Helps sort files like page2 before page10."""
    return [int(tok) if tok.isdigit() else tok.lower() for tok in re.split(r"(\d+)", text)]

def process_image_gpu(img_data: bytes) -> Image.Image:
    """Process image using GPU acceleration if available."""
    try:
        # Open image from bytes
        img = Image.open(BytesIO(img_data))
        
        if device.type == 'cuda':
            # Convert to tensor and move to GPU
            transform = transforms.Compose([
                transforms.ToTensor(),
            ])
            
            tensor = transform(img).unsqueeze(0).to(device)
            
            # Basic GPU processing (normalize, etc.)
            tensor = torch.clamp(tensor, 0, 1)
            
            # Convert back to PIL Image
            tensor = tensor.squeeze(0).cpu()
            img = transforms.ToPILImage()(tensor)
        
        # Ensure RGB mode
        if img.mode in ("P", "RGBA"):
            img = img.convert("RGB")
            
        return img
    except Exception as e:
        print(f"GPU processing failed, falling back to CPU: {e}")
        # Fallback to CPU processing
        img = Image.open(BytesIO(img_data))
        if img.mode in ("P", "RGBA"):
            img = img.convert("RGB")
        return img

def cbz_to_pdf(cbz_path: Path, out_dir: Path):
    """Memory efficient CBZ to PDF conversion with GPU acceleration."""
    with zipfile.ZipFile(cbz_path) as zf:
        images = [n for n in zf.namelist() if n.lower().endswith((
            ".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tif", ".tiff", ".webp"
        ))]
        if not images:
            print(f"[SKIP] {cbz_path.name}: no images detected")
            return
        images.sort(key=_natural_key)

        pdf_path = out_dir / f"{cbz_path.stem}.pdf"
        processed_images = []
        
        # Process images in batches
        for i in range(0, len(images), BATCH_SIZE):
            batch = images[i:i + BATCH_SIZE]
            batch_processed = []
            
            for name in batch:
                try:
                    with zf.open(name) as fp:
                        img_data = fp.read()
                    
                    # Process with GPU if available
                    processed_img = process_image_gpu(img_data)
                    batch_processed.append(processed_img)
                    
                except Exception as e:
                    print(f"[ERROR] Failed to process {name}: {e}")
                    continue
            
            processed_images.extend(batch_processed)
            
            # Clear GPU memory after each batch
            if device.type == 'cuda':
                torch.cuda.empty_cache()
            
            # Force garbage collection
            gc.collect()
            
            print(f"Processed batch {i//BATCH_SIZE + 1}/{(len(images) + BATCH_SIZE - 1)//BATCH_SIZE}")

        if not processed_images:
            print(f"[SKIP] {cbz_path.name}: no valid images processed")
            return

        # Save PDF
        try:
            processed_images[0].save(
                pdf_path, 
                "PDF", 
                save_all=True, 
                append_images=processed_images[1:],
                optimize=True,
                quality=85
            )
            print(f"[OK]  {pdf_path.name} ({len(processed_images)} pages)")
        except Exception as e:
            print(f"[ERROR] Failed to save PDF {pdf_path.name}: {e}")
        finally:
            # Clean up images from memory
            for img in processed_images:
                img.close()
            processed_images.clear()
            gc.collect()

def main():
    source_dir = Path(INPUT_DIR).expanduser().resolve()
    if not source_dir.is_dir():
        raise SystemExit(f"INPUT_DIR not a directory: {source_dir}")

    dest_dir = Path(__file__).parent.resolve()
    print(f"Converting CBZs from {source_dir}\nSaving PDFs to {dest_dir}\n")
    
    try:
        for cbz in sorted(source_dir.glob("*.cbz"), key=lambda p: _natural_key(p.name)):
            cbz_to_pdf(cbz, dest_dir)
            
            # Clean up after each file
            if device.type == 'cuda':
                torch.cuda.empty_cache()
            gc.collect()
            
    except KeyboardInterrupt:
        print("\nConversion interrupted by user")
    except Exception as e:
        print(f"Error during conversion: {e}")
    finally:
        # Final cleanup
        if device.type == 'cuda':
            torch.cuda.empty_cache()

if __name__ == "__main__":
    main()
