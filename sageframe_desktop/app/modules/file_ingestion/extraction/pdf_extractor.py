"""PDF text extraction utilities using PyPDF2 and pdf2image."""

import os
import tempfile
from typing import Optional

from PyPDF2 import PdfReader
from pdf2image import convert_from_path
from PIL import Image


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a text-based PDF.

    If the PDF pages have text, concatenates content; otherwise returns empty string.
    """
    try:
        reader = PdfReader(file_path)
        contents = []
        
        for page_num, page in enumerate(reader.pages, 1):
            try:
                text = page.extract_text() or ""
                if text.strip():
                    # Clean up the text
                    text = text.strip()
                    # Remove excessive whitespace
                    text = " ".join(text.split())
                    contents.append(text)
            except Exception as e:
                print(f"Warning: Could not extract text from page {page_num}: {e}")
                continue
        
        return "\n\n".join(contents)
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return ""


def has_selectable_text(file_path: str, min_chars: int = 50) -> bool:
    """Check if PDF has selectable text (more than min_chars)."""
    text = extract_text_from_pdf(file_path)
    return len(text.strip()) >= min_chars


def rasterize_pdf_first_page(file_path: str, dpi: int = 300) -> str:
    """Convert first page of PDF to PNG image and return the image path.
    
    Args:
        file_path: Path to the PDF file
        dpi: DPI for rasterization (higher = better quality, default 300)
    
    Returns:
        Path to temporary PNG file.
    
    Raises:
        ValueError: If PDF rasterization fails
    """
    try:
        # Convert first page to image with higher DPI for better OCR
        images = convert_from_path(file_path, first_page=1, last_page=1, dpi=dpi)
        if not images:
            raise ValueError("Failed to rasterize PDF page - no images returned")
        
        # Save to temp file
        fd, temp_path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        
        # Save with good quality for OCR
        images[0].save(temp_path, "PNG", optimize=False)
        
        print(f"Rasterized PDF to {temp_path} at {dpi} DPI")
        return temp_path
        
    except Exception as e:
        raise ValueError(f"PDF rasterization failed: {e}")
