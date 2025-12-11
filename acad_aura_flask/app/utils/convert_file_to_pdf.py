# app/utils/convert_file_to_pdf.py
import os
import shutil
from pathlib import Path
from PIL import Image  # Pillow
from datetime import datetime

# Optional imports (may be None if not installed)
try:
    from docx2pdf import convert as docx2pdf_convert
except Exception:
    docx2pdf_convert = None

try:
    from reportlab.pdfgen import canvas
except Exception:
    canvas = None

try:
    import win32com.client as win32com
except Exception:
    win32com = None

ALLOWED_EXT = {
    "doc", "docx", "ppt", "pptx", "xls", "xlsx",
    "txt", "csv", "pdf", "png", "jpg", "jpeg", "bmp", "gif"
}


def txt_to_pdf(txt_path, pdf_path):
    if canvas is None:
        raise RuntimeError("reportlab not installed. Install with: pip install reportlab")
    c = canvas.Canvas(pdf_path)
    with open(txt_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
    y = 800
    left = 40
    line_height = 12
    for line in lines:
        text = line.rstrip("\n")
        if y < 40:
            c.showPage()
            y = 800
        c.drawString(left, y, text)
        y -= line_height
    c.save()


def image_to_pdf(image_path, pdf_path):
    # Pillow handles multi-frame GIFs as multiple pages; for others we convert single image to single page PDF
    try:
        with Image.open(image_path) as im:
            # Convert RGBA -> RGB (PDF doesn't accept alpha)
            if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
                alpha = im.convert("RGBA")
                bg = Image.new("RGB", alpha.size, (255, 255, 255))
                bg.paste(alpha, mask=alpha.split()[3])  # 3 is alpha channel
                rgb = bg
            else:
                rgb = im.convert("RGB")

            # For multi-frame (animated GIF), save all frames into a multi-page PDF
            frames = []
            try:
                # attempt to iterate frames
                for frame in ImageSequence(rgb if hasattr(Image, "ImageSequence") else im):
                    frame_rgb = frame.convert("RGB")
                    frames.append(frame_rgb)
            except Exception:
                # fallback - single frame
                frames = [rgb]

            if len(frames) == 1:
                frames[0].save(pdf_path, "PDF", resolution=100.0)
            else:
                frames[0].save(pdf_path, "PDF", save_all=True, append_images=frames[1:])
            return pdf_path
    except Exception as e:
        # fallback simple save
        try:
            with Image.open(image_path) as im:
                rgb = im.convert("RGB")
                rgb.save(pdf_path, "PDF")
                return pdf_path
        except Exception as e2:
            raise RuntimeError(f"Image->PDF conversion failed: {e2}")


def convert_to_pdf(original_path: str, pdf_path: str):
    """
    Convert original_path to pdf_path.
    Raises RuntimeError with a helpful message on failure.
    """
    original_path = str(original_path)
    pdf_path = str(pdf_path)
    ext = Path(original_path).suffix.lower().lstrip(".")
    ext = ext or ""

    # Already a PDF: copy
    if ext == "pdf":
        shutil.copyfile(original_path, pdf_path)
        return pdf_path

    # Word documents
    if ext in ("docx", "doc"):
        if docx2pdf_convert:
            try:
                # docx2pdf will create a pdf next to source; use temp file then move
                tmp = Path(pdf_path).with_suffix(".tmp.pdf")
                docx2pdf_convert(original_path, str(tmp))
                if tmp.exists():
                    tmp.replace(pdf_path)
                    return pdf_path
                # fallback: docx2pdf might write to same dir as original
                alt = Path(original_path).with_suffix(".pdf")
                if alt.exists():
                    shutil.move(str(alt), pdf_path)
                    return pdf_path
                raise RuntimeError("docx2pdf did not produce expected PDF.")
            except Exception as e:
                raise RuntimeError(f"Word->PDF conversion failed: {e}")
        else:
            raise RuntimeError("docx2pdf not installed. Install with: pip install docx2pdf (requires MS Word on Windows).")

    # Images (use Pillow)
    if ext in ("png", "jpg", "jpeg", "bmp", "gif"):
        return image_to_pdf(original_path, pdf_path)

    # Text / CSV
    if ext in ("txt", "csv"):
        return txt_to_pdf(original_path, pdf_path)

    # PowerPoint
    if ext in ("ppt", "pptx"):
        if win32com:
            try:
                powerpoint = win32com.Dispatch("PowerPoint.Application")
                powerpoint.Visible = 1
                pres = powerpoint.Presentations.Open(original_path, WithWindow=False)
                pres.SaveAs(pdf_path, 32)  # 32 = ppSaveAsPDF
                pres.Close()
                powerpoint.Quit()
                if os.path.exists(pdf_path):
                    return pdf_path
                raise RuntimeError("PowerPoint conversion did not create a PDF.")
            except Exception as e:
                raise RuntimeError(f"PPT->PDF conversion failed (COM): {e}")
        else:
            raise RuntimeError("pywin32 not installed. Install with: pip install pywin32 to enable PPT conversions on Windows.")

    # Excel
    if ext in ("xls", "xlsx"):
        if win32com:
            try:
                excel = win32com.Dispatch("Excel.Application")
                excel.Visible = False
                wb = excel.Workbooks.Open(original_path)
                wb.ExportAsFixedFormat(0, pdf_path)  # 0 = xlTypePDF
                wb.Close(False)
                excel.Quit()
                if os.path.exists(pdf_path):
                    return pdf_path
                raise RuntimeError("Excel conversion did not create a PDF.")
            except Exception as e:
                raise RuntimeError(f"Excel->PDF conversion failed (COM): {e}")
        else:
            raise RuntimeError("pywin32 not installed. Install with: pip install pywin32 to enable Excel conversions on Windows.")

    raise RuntimeError(f"Unsupported file extension: '{ext}'. Allowed: {', '.join(sorted(ALLOWED_EXT))}")
