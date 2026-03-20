# Consonants: traditional consonants + seats of hamza 
CONSONANTS = "بتثجحخدذرزسشصضطظعغفقكلمنهويء" + "أإؤئ"

# Vowels: short vowels + dagger alif + alif maqsuura
VOWELS = "َُِ" + "ٰ" + "ى"

# NOTE: We are leaving alif, wasla, and taa marbuuta untouched

PREPROCESS_MAP = {
    # tanwiin diacritics
    "ً": "َ" + "n", # tanwiin fat7a to fat7a + n  
    "ٌ": "ُ" + "n", # tanwiin damma to damma + n 
    "ٍ": "ِ" + "n", # tanwiin kasra to kasra + n  
    # combination letters
    "آ": "أ" + "ا", # alif madda to hamza + alif
}

POSTPROCESS_MAP = {
    # reconvert the tanwiin vowels (get rid of the 'n')
    "َ" + "n": "ً", # fat7a + n to tanwiin fat7a
    "ُ" + "n": "ٌ", # damma + n to tanwiin damma
    "ِ" + "n": "ٍ", # kasra + n to tanwiin kasra
    # reconvert combination letters 
    "أ" + "ا": "آ",
}

# NOTE: made a much more intricate version of this, but it was not 
#       invertible
