"""
This module contains sample data for different types of identification documents.
Each document is represented as an object with relevant fields.
"""

# id_card
id_card = {
    "id_card_nr": "123456789",
    "id_card_first_name": "Max",
    "id_card_last_name": "Muster",
    "id_card_birthdate": "10.02.2005",
    "id_card_birth_place": "Musterstadt",
    "id_card_nationality": "Musterland",
    "id_card_address": "Musterstrasse 1, 12345 Musterstadt"
}

# passport
passport = {
    "passport_nr": "M987654321",
    "passport_first_name": "Max",
    "passport_last_name": "Muster",
    "passport_birthdate": "10.02.2005",
    "passport_birth_place": "Musterstadt",
    "passport_nationality": "Musterland",
    "passport_address": "Musterstrasse 1, 12345 Musterstadt"
}

# residence_permit
residence_permit = {
    "residence_permit_nr": "RP12345678",
    "residence_permit_first_name": "Max",
    "residence_permit_last_name": "Muster",
    "residence_permit_birthdate": "10.02.2005",
    "residence_permit_birth_place": "Musterstadt",
    "residence_permit_nationality": "Musterland",
    "residence_permit_address": "Musterstrasse 1, 12345 Musterstadt"
}


def process_id_document():
    return "ID Document Processed"