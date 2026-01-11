import pytest
from extensions.idprovider import map_id_fields

def test_map_id_fields_happy_path():
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
    assert result["id_card_place_of_birth"] == "BERLIN"
    assert result["id_card_nationality"] == "DEUTSCH"
    assert result["id_card_date_of_expiry"] == "01.05.2034"

def test_map_id_fields_not_enough_lines():
    with pytest.raises(IndexError):
        map_id_fields("ID Card", ["only", "two"])