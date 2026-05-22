__version__ = "0.1.0"
__all__ = ["convert_pdf_to_docx"]


def convert_pdf_to_docx(*args, **kwargs):
    from .converter import convert_pdf_to_docx as _convert_pdf_to_docx

    return _convert_pdf_to_docx(*args, **kwargs)
