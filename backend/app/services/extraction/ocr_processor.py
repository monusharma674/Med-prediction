import os
import io
from typing import Tuple
from PIL import Image
from app.core.config import settings

# Optional pytesseract import
try:
    import pytesseract
    if os.path.exists(settings.TESSERACT_CMD):
        pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
    TESSERACT_AVAILABLE = True
except Exception:
    TESSERACT_AVAILABLE = False


class OCRProcessor:
    @staticmethod
    def process_image(image_bytes: bytes) -> Tuple[str, float]:
        """
        Runs Tesseract OCR on raw image bytes.
        Returns:
            - text: extracted text
            - confidence: average confidence score between 0.0 and 1.0
        """
        image = Image.open(io.BytesIO(image_bytes))

        if not TESSERACT_AVAILABLE:
            return "", 0.0

        try:
            # Check if tesseract binary exists
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            confidences = [int(c) for c in data['conf'] if c != '-1' and int(c) >= 0]
            avg_conf = (sum(confidences) / len(confidences) / 100.0) if confidences else 0.75
            text = pytesseract.image_to_string(image)
            return text, avg_conf
        except Exception:
            # Fallback if tesseract engine isn't reachable
            return "", 0.0
