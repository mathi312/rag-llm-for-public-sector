"""
This module contains sample data for different types of identification documents.
Each document is represented as an object with relevant fields.
It includes functions to map OCR-extracted text lines to structured ID fields.
"""

import io
import re
import numpy as np
import difflib

from functools import lru_cache
from typing import Dict, List, Optional
from PIL import Image, ImageOps, ImageEnhance, ImageFilter
from enum import Enum, auto
from easyocr import Reader

class IdType(Enum):
    ID_CARD = "ID Card"
    PASSPORT = "Passport"
    RESIDENCE_PERMIT = "Residence Permit"

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
        "passport_last_name": "",
        "passport_birth_name": "",
        "passport_first_name": "",
        "passport_date_of_birth": "",
        "passport_place_of_birth": "",
        "passport_nationality": "",
        "passport_date_of_issue": "",
        "passport_date_of_expiry": "",
        "passport_authority": "",
    },
    "Residence permit": {
        "residence_permit_number": "",
        "residence_permit_last_name": "",
        "residence_permit_first_name": "",
        "residence_permit_date_of_birth": "",
        "residence_permit_nationality": "",
        "residence_permit_sex": "",
        "residence_permit_type_of_permit": "",
        "residence_permit_date_of_expiry": "",
    },
}

def map_id_fields(id_type: IdType, lines: List[str]) -> Dict[str, str]:
    """Maps OCR lines to ID fields based on the ID type."""
    patterns = FIELD_PATTERNS.get(id_type, {})
    mapped: Dict[str, str] = {k: "" for k in patterns.keys()}

    if id_type == IdType.ID_CARD:
        mapped["id_card_number"] = mapped.get("id_card_number", "") or lines[1].strip().replace(" ", "")
        mapped["id_card_name"] = mapped.get("id_card_name", "") or lines[9].strip()[3:]
        mapped["id_card_birth_name"] = mapped.get("id_card_birth_name", "") or lines[10].strip()[3:]
        mapped["id_card_first_name"] = mapped.get("id_card_first_name", "") or lines[12].strip()
        mapped["id_card_date_of_birth"] = mapped.get("id_card_date_of_birth", "") or lines[17].strip() + "." + lines[18].strip() + "." + lines[19].strip()
        mapped["id_card_place_of_birth"] = mapped.get("id_card_place_of_birth", "") or lines[22].strip()
        mapped["id_card_nationality"] = mapped.get("id_card_nationality", "") or lines[20].strip()
        mapped["id_card_date_of_expiry"] = mapped.get("id_card_date_of_expiry", "") or lines[25].strip() + "." + lines[26].strip().replace(" ", "")

    if id_type == IdType.PASSPORT:
        mapped["passport_number"] = mapped.get("passport_number", "") or lines[14].upper().strip().replace(" ", "").replace("O", "0")
        mapped["passport_last_name"] = mapped.get("passport_last_name", "") or lines[21].strip()
        mapped["passport_birth_name"] = mapped.get("passport_birth_name", "") or lines[22].strip()
        mapped["passport_first_name"] = mapped.get("passport_first_name", "") or lines[26].strip()
        mapped["passport_date_of_birth"] = mapped.get("passport_date_of_birth", "") or lines[36].strip()
        mapped["passport_place_of_birth"] = mapped.get("passport_place_of_birth", "") or lines[41].strip()
        mapped["passport_nationality"] = mapped.get("passport_nationality", "") or lines[37].strip()
        mapped["passport_date_of_issue"] = mapped.get("passport_date_of_issue", "") or lines[52].strip()
        mapped["passport_date_of_expiry"] = mapped.get("passport_date_of_expiry", "") or lines[53].strip()
        mapped["passport_authority"] = mapped.get("passport_authority", "") or lines[58].strip()

    if id_type == IdType.RESIDENCE_PERMIT:
        mapped["residence_permit_number"] = mapped.get("residence_permit_number", "") or lines[1].strip().replace(" ", "")
        mapped["residence_permit_last_name"] = mapped.get("residence_permit_name", "") or lines[4].strip()
        mapped["residence_permit_first_name"] = mapped.get("residence_permit_birth_name", "") or lines[5].strip()
        mapped["residence_permit_date_of_birth"] = mapped.get("residence_permit_date_of_birth", "") or lines[14].strip() + "." + lines[15].strip() + "." + lines[16].strip()
        mapped["residence_permit_nationality"] = mapped.get("residence_permit_nationality", "") or lines[13].strip()
        mapped["residence_permit_sex"] = mapped.get("residence_permit_sex", "") or lines[12].strip()
        mapped["residence_permit_type_of_permit"] = mapped.get("residence_permit_type_of_permit", "") or lines[19].strip()
        mapped["residence_permit_date_of_expiry"] = mapped.get("residence_permit_date_of_expiry", "") or lines[20].strip() + "." + lines[21].strip() + "." + lines[22].strip()

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


def process_id_document(file_bytes: bytes, id_type: IdType | None = None) -> Dict[str, str]:
    """Processes an ID document image and extracts relevant fields using OCR."""
    raw_text = _run_ocr_easyocr(file_bytes)
    lines = [ln for ln in raw_text.splitlines() if ln.strip()] # Filter out empty lines

    if id_type is None:
        id_type = detect_id_type_from_text(lines)

    result = map_id_fields(id_type, lines)

    return {
        **result,
        "id_type": id_type,
        "raw_text": raw_text.strip(),
    }

def detect_id_type_from_text(lines: list[str]) -> IdType:
    """Detects the ID type from OCR-extracted text."""
    for line in lines:
        line = line.upper()

        if is_close_match(line, "PERSONALAUSWEIS"):
            return IdType.ID_CARD
        elif is_close_match(line, "REISEPASS") or is_close_match(line, "PASSPORT"):
            return IdType.PASSPORT
        elif is_close_match(line, "AUFENTHALTSTITEL"):
            return IdType.RESIDENCE_PERMIT
    
    raise ValueError("Unable to detect ID type from Provided ID Document")

def is_close_match(text: str, keyword: str, threshold: float = 0.75) -> bool:
    """Returns True if the keyword approximately appears in the text,
    tolerating OCR errors based on the given similarity threshold."""
    matches = difflib.get_close_matches(keyword, [text], cutoff=threshold)
    return bool(matches)
