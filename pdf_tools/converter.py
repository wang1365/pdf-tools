from pathlib import Path
from typing import Optional
from pdf2docx import Converter

def convert_pdf_to_docx(pdf_path: str, docx_path: str, start: Optional[int] = None, end: Optional[int] = None) -> None:
    pdf = Path(pdf_path)
    if not pdf.is_file():
        raise FileNotFoundError(str(pdf))
    out = Path(docx_path)
    if out.parent and not out.parent.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
    cv = Converter(str(pdf))
    try:
        if start is None and end is None:
            cv.convert(str(out))
        else:
            cv.convert(str(out), start=start or 0, end=end)
    finally:
        cv.close()
