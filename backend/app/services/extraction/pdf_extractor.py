import os
from typing import List, Tuple
import fitz  # PyMuPDF


class PDFExtractor:
    @staticmethod
    def extract_text_from_pdf(file_path: str) -> Tuple[str, bool, float]:
        """
        Extracts text from a PDF file.
        Returns:
            - text: concatenated text string
            - is_digital: True if selectable digital text exists, False if scanned
            - confidence: confidence score (1.0 for digital PDF)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        doc = fitz.open(file_path)
        extracted_text = []
        total_pages = len(doc)
        total_chars = 0

        for page_num in range(total_pages):
            page = doc[page_num]
            text = page.get_text()
            if text and text.strip():
                extracted_text.append(text)
                total_chars += len(text.strip())

        doc.close()

        combined_text = "\n".join(extracted_text)

        # If average characters per page > 30, it's a digital PDF
        if total_chars > (30 * max(1, total_pages)):
            return combined_text, True, 0.98

        return combined_text, False, 0.50

    @staticmethod
    def render_pages_to_images(file_path: str) -> List[bytes]:
        """Renders PDF pages as PNG image byte streams for OCR processing."""
        doc = fitz.open(file_path)
        images = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            # 2x zoom for sharp OCR recognition
            pix = page.get_pixmap(dpi=200)
            img_bytes = pix.tobytes("png")
            images.append(img_bytes)
        doc.close()
        return images
