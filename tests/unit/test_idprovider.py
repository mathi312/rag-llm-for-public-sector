import pytest
import io
import numpy as np

from PIL import Image
from unittest.mock import patch, MagicMock

from extensions.idprovider import *
from extensions.idprovider import _get_reader, _preprocess_image_for_ocr, _run_ocr_easyocr


"""
Unit-Tests with pytest for the ID field mapping functionality.
"""

def test_map_id_fields_ocr_extraction_id_card():
    """Test mapping of ID fields from OCR lines for a German demo ID card."""
    lines = [
        "BUNDESREPUBLIK DEUTSCHLAND",
        "LZ6311T 4 7",
        "FEDERAL REPUBLIC OF GERMANY / REPUBLIQUE FEDERALE D'ALLEMAGNE",
        "DE",
        "PERSONALAUSWEIS",
        "IDENTITY CARD",
        "CARTE DIDENTITE",
        "[a] Name/Surname/Nom",
        "[bj Geburtsname/Name at birth/Nom de naissance",
        "[aJMUSTERMANN",
        "[bJGABLER",
        "Vornamen/Given names/Prenoms",
        "ERIKA",
        "Geburtstag /Date of birth/",
        "Staatsangehörigkeit / Nationality /",
        "Date de naissance",
        "Nationalite",
        "12",
        "08",
        "1972",
        "DEUTSCH",
        "Geburtsort/Place of birth/Lieu de naissance",
        "BERLIIN",
        "Gültig bis/Date of expiry/",
        "Date d expiration",
        "01",
        "05 .2034",
        "938568"
    ]
    result = map_id_fields(IdType.ID_CARD, lines)
    assert result["id_card_number"] == "LZ6311T47"
    assert result["id_card_name"] == "MUSTERMANN"
    assert result["id_card_birth_name"] == "GABLER"
    assert result["id_card_first_name"] == "ERIKA"
    assert result["id_card_date_of_birth"] == "12.08.1972"
    assert result["id_card_place_of_birth"] != "BERLIN"
    assert result["id_card_nationality"] == "DEUTSCH"
    assert result["id_card_date_of_expiry"] == "01.05.2034"


def test_map_id_fields_ocr_extraction_passport():
    """Test mapping of ID fields from OCR lines for a German demo passport."""
    lines = [
        "BUNDESREPUBLIK DEUTSCHLAND",
        "REISEPASS",
        "Federal republic oF Germany",
        "REPUBLIQUE FedeRaLE d'allemagne",
        "PASSPORT - PASSEPORT",
        "Typ",
        "Type",
        "Type",
        "Kode",
        "Code",
        "Code",
        "Pass-Nr.",
        "Passport No",
        "Passeport No",
        "Co1XWZCLV",
        "1 [aJName",
        "Surname",
        "Nom",
        "[b] Geburtsname",
        "Name at birth",
        "Nom de naissance",
        "MUSTERMANN",
        "GABLER",
        "Vornamen",
        "Given names",
        "Prenoms",
        "ERIKA",
        "Geburtstag",
        "Date of birh",
        "Geschlecht",
        "Sex {",
        "Staatsangehorigkeit",
        "Nationality /",
        "Date de naissance",
        "Sexe",
        "Nationalite",
        "12.08.4964",
        "DEUTSCH",
        "Geburtsort _",
        "Place ot birth / Lieu de nalssance",
        "D",
        "BERLIN",
        "Ausstellungsdatur / Date",
        "Gultig bis",
        "Date of expiry",
        "Unterschritt der Inhaberin ,",
        "olssue",
        "Date de delivrance",
        "Date",
        "'expiration",
        "des Inhabers",
        "Signature of bcarer",
        "01.03.2017",
        "28.02.2027",
        "Signature de la titulaire, du titulaire",
        "Bchorde",
        "Authonity",
        "Autorite",
        "STADT KÖLN",
        "Unb ndsm",
        "P <D < <MUSTERMANN<<ERIKA<<<<<<<< <<< < < < << < < < < < <",
        "tnt",
        "Dyrolai",
        "Co1XwZ CLV5D<<6408125F2702283<<<<<<<<<<<<<<<0"
    ]

    result = map_id_fields(IdType.PASSPORT, lines)
    assert result["passport_number"] == "C01XWZCLV"
    assert result["passport_last_name"] == "MUSTERMANN"
    assert result["passport_birth_name"] == "GABLER"
    assert result["passport_first_name"] == "ERIKA"
    assert result["passport_date_of_birth"] != "12.08.1964"
    assert result["passport_place_of_birth"] == "BERLIN"
    assert result["passport_nationality"] == "DEUTSCH"
    assert result["passport_date_of_issue"] == "01.03.2017"
    assert result["passport_date_of_expiry"] == "28.02.2027"
    assert result["passport_authority"] == "STADT KÖLN"


def test_map_id_fields_ocr_extraction_residence_permit():
    """Test mapping of ID fields from OCR lines for a German demo residence permit."""
    lines = [
        "AUFENTHALTSTITEL",
        "YZX211V11",
        "YZX211V11",
        "NAMEN VornamenISURNAMES Forenames",
        "MUSTERMANN",
        "Erika",
        "GESCHLECHTI",
        "STAATSANGEHÖRIGKEITI",
        "GEBURTSDATUMI",
        "SEX",
        "NATIONALITY",
        "DATE OF BIRTH",
        "F",
        "TUR",
        "12",
        "08",
        "1983",
        "ART DES TITELSITYPE OF PERMIT `",
        "KARTE GÜLTIG BISICARD EXPIRY",
        "AUFENTHALTSERLAUBNIS",
        "31",
        "10",
        "2026",
        "ANMERKUNGENREMARKS",
        "19C ABS,1 I.VM",
        "11",
        "ABS . 2",
        "BESCHV",
        "AUSWEISERSATZ /PERSONALIEN",
        "EIG",
        "ANGABEN",
        "3ryl/lew",
        "925732",
        "RESIDENCE PERMIT",
    ]

    result = map_id_fields(IdType.RESIDENCE_PERMIT, lines)
    assert result["residence_permit_number"] == "YZX211V11"
    assert result["residence_permit_last_name"] == "MUSTERMANN"
    assert result["residence_permit_first_name"] == "Erika"
    assert result["residence_permit_date_of_birth"] == "12.08.1983"
    assert result["residence_permit_nationality"] == "TUR"
    assert result["residence_permit_sex"] == "F"
    assert result["residence_permit_type_of_permit"] == "AUFENTHALTSERLAUBNIS"
    assert result["residence_permit_date_of_expiry"] == "31.10.2026"


def test_map_id_fields_not_enough_lines():
    """Test that an IndexError is raised when there are not enough lines."""
    with pytest.raises(IndexError):
        map_id_fields(IdType.ID_CARD, ["only", "two"])

@patch("extensions.idprovider.Reader", autospec=True)
def test_get_reader_is_cached(mock_reader):
    r1 = _get_reader(gpu=False)
    r2 = _get_reader(gpu=False)

    assert r1 is r2
    mock_reader.assert_called_once_with(["de", "en"], gpu=False)

def test_preprocess_image_no_resize():
    img = Image.new("RGB", (1000, 800))
    out = _preprocess_image_for_ocr(img, max_dim=2000)

    assert out.size == img.size

def test_preprocess_image_resizes_large_image():
    img = Image.new("RGB", (4000, 2000))
    out = _preprocess_image_for_ocr(img, max_dim=2000)

    assert out.size == (2000, 1000)

@patch("extensions.idprovider._get_reader")
@patch("extensions.idprovider._preprocess_image_for_ocr")
def test_run_ocr_easyocr(mock_preprocess_image, mock_get_reader):
    img = Image.new("RGB", (100, 100))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    image_bytes = buf.getvalue()

    mock_reader = MagicMock()
    mock_reader.readtext.return_value = ["LINE ONE", "LINE TWO"]

    mock_get_reader.return_value = mock_reader
    mock_preprocess_image.side_effect = lambda x: x

    result = _run_ocr_easyocr(image_bytes)

    assert result == "LINE ONE\nLINE TWO"
    mock_reader.readtext.assert_called_once()
    args, kwargs = mock_reader.readtext.call_args
    assert isinstance(args[0], np.ndarray)
    assert kwargs["detail"] == 0
    assert kwargs["paragraph"] is False

def test_detect_id_type_id_card():
    lines = ["Bundesrepublik Deutschland", "Personalausweis"]
    assert detect_id_type_from_text(lines) == IdType.ID_CARD

def test_detect_id_type_passport():
    lines = ["EUROPEAN UNION", "Passport"]
    assert detect_id_type_from_text(lines) == IdType.PASSPORT

def test_detect_id_type_residence_permit():
    lines = ["Aufenthaltstitel"]
    assert detect_id_type_from_text(lines) == IdType.RESIDENCE_PERMIT

def test_detect_id_type_raises():
    with pytest.raises(ValueError):
        detect_id_type_from_text(["Random text", "Nothing useful"])

def test_is_close_match_exact():
    assert is_close_match("PERSONALAUSWEIS", "PERSONALAUSWEIS")

def test_is_close_match_approximate():
    assert is_close_match("PERS0NALAUSWE1S", "PERSONALAUSWEIS", threshold=0.6)

def test_is_close_match_false():
    assert not is_close_match("HELLO WORLD", "PASSPORT")

@patch("extensions.idprovider._run_ocr_easyocr")
@patch("extensions.idprovider.map_id_fields")
def test_process_id_document_detects_type(mock_map_id_fields, mock_run_easyocr):
    mock_run_easyocr.return_value = "PERSONALAUSWEIS\nMUSTERMANN\nERIKA"
    mock_map_id_fields.return_value = {"first_name": "ERIKA", "last_name": "MUSTERMANN"}

    result = process_id_document(b"fake-bytes")

    assert result["id_type"] == IdType.ID_CARD
    assert result["first_name"] == "ERIKA"
    assert result["last_name"] == "MUSTERMANN"
    assert "PERSONALAUSWEIS" in result["raw_text"]

@patch("extensions.idprovider._run_ocr_easyocr")
@patch("extensions.idprovider.map_id_fields")
def test_process_id_document_with_explicit_id_type(mock_map_id_fields, mock_run_easyocr):
    mock_run_easyocr.return_value = "REISEPASS\nDOE\nJOHN"
    mock_map_id_fields.return_value = {"first_name": "JOHN", "last_name": "DOE"}

    result = process_id_document(
        b"fake-bytes",
        id_type=IdType.PASSPORT
    )

    assert result["id_type"] == IdType.PASSPORT
