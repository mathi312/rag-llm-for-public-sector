"""
This module contains sample data for different types of identification documents.
Each document is represented as an object with relevant fields.
It includes functions to map OCR-extracted text lines to structured ID fields.
"""

import io
import re
from functools import lru_cache
from typing import Dict, List, Optional
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
import numpy as np
from easyocr import Reader


# Define field patterns for different ID types
FIELD_PATTERNS: Dict[str, Dict[str, str]] = {
    "ID Card": {
        "id_card_number": "",
        "id_card_name": "",
        "id_card_birth_name": "",
        "id_card_first_name": "",
        "id_card_date_of_birth": "",
        "id_card_place_of_birth": "",
        "id_card_nationality": "",
        "id_card_date_of_expiry": "",
    },
    "Passport": {
        "passport_number": "",
        "passport_name": "",
        "passport_birth_name": "",
        "passport_first_name": "",
        "passport_date_of_birth": "",
        "passport_place_of_birth": "",
        "passport_nationality": "",
        "passport_date_of_expiry": "",
    },
    "Residence permit": {
        "residence_permit_number": "",
        "residence_permit_name": "",
        "residence_permit_birth_name": "",
        "residence_permit_first_name": "",
        "residence_permit_date_of_birth": "",
        "residence_permit_place_of_birth": "",
        "residence_permit_nationality": "",
        "residence_permit_date_of_expiry": "",
    },
}


def map_id_fields(id_type: str, lines: List[str]) -> Dict[str, str]:
    """Maps OCR lines to ID fields based on the ID type."""
    patterns = FIELD_PATTERNS.get(id_type, {})
    mapped: Dict[str, str] = {k: "" for k in patterns.keys()}

    mapped["id_card_number"] = mapped.get("id_card_number", "") or lines[1].strip().replace(" ", "")
    mapped["id_card_name"] = mapped.get("id_card_name", "") or lines[9].strip()[3:]
    mapped["id_card_birth_name"] = mapped.get("id_card_birth_name", "") or lines[10].strip()[3:]
    mapped["id_card_first_name"] = mapped.get("id_card_first_name", "") or lines[12].strip()
    mapped["id_card_date_of_birth"] = mapped.get("id_card_date_of_birth", "") or lines[17].strip() + "." + lines[18].strip() + "." + lines[19].strip()
    mapped["id_card_place_of_birth"] = mapped.get("id_card_place_of_birth", "") or lines[22].strip()
    mapped["id_card_nationality"] = mapped.get("id_card_nationality", "") or lines[20].strip()
    mapped["id_card_date_of_expiry"] = mapped.get("id_card_date_of_expiry", "") or lines[25].strip() + "." + lines[26].strip().replace(" ", "")

    return mapped
    

# EasyOCR Reader initialization with caching
@lru_cache(maxsize=1)
def _get_reader(gpu: bool = False) -> Reader:
    """Initializes and returns an EasyOCR Reader instance."""
    return Reader(['de', 'en'], gpu=gpu)


def _preprocess_image_for_ocr(image: Image.Image, max_dim: int = 2000) -> Image.Image:
    """
    Preprocesses the image for better OCR results.

    :param image: PIL Image to preprocess.
    :param max_dim: Maximum dimension (width or height) for resizing.
    """
    w, h = image.size # Get original dimensions
    scale = min(1.0, max_dim / max(w, h)) # Calculate scaling factor
    if scale < 1.0:
        image = image.resize((int(w * scale), int(h * scale)), Image.LANCZOS) # Resize image if needed
    return image


def _run_ocr_easyocr(image_bytes: bytes) -> str:
    """Runs OCR on the given image bytes using EasyOCR."""
    img = Image.open(io.BytesIO(image_bytes))
    img = _preprocess_image_for_ocr(img)
    reader = _get_reader(gpu=False)
    lines = reader.readtext(np.array(img), detail=0, paragraph=False) # Get only text lines
    return "\n".join(lines) # Join lines into a single string


def process_id_document(file_bytes: bytes, id_type: str) -> Dict[str, str]:
    """Processes an ID document image and extracts relevant fields using OCR."""
    raw_text = _run_ocr_easyocr(file_bytes)
    lines = [ln for ln in raw_text.splitlines() if ln.strip()] # Filter out empty lines
    result = map_id_fields(id_type, lines)
    return {
        **result,
        "raw_text": raw_text.strip(),
    }