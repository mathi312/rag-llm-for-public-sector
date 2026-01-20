import pytest
from extensions.idprovider import map_id_fields

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
    result = map_id_fields("ID Card", lines)
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

    result = map_id_fields("Passport", lines)
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

    result = map_id_fields("Residence permit", lines)
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
        map_id_fields("ID Card", ["only", "two"])