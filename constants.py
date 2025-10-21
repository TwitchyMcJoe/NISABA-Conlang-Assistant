# constants.py
import os

APP_ROOT = os.path.abspath(".")
LANG_ROOT = os.path.join(APP_ROOT, "Languages")
os.makedirs(LANG_ROOT, exist_ok=True)

# Filenames
DICT_FILE = "dictionary.csv"
PHONO_FILE = "phonology.csv"
PHONOTEXT = "phonotactics.txt"
GRAMMAR_TEXT = "grammar.txt"
CONJ_FILE = "conjugations.csv"
FONTS_DIRNAME = "fonts"
NUMBERS_FILE = "numbers.csv"

# CSV field definitions
DICT_FIELDS = [
    "english", "conlang", "pos", "gender",
    "definition", "pronunciation",
    "loanword", "consistent_phon", "consistent_spell"
]
PHONO_FIELDS = ["ipa", "example", "type", "notes"]
CONJ_FIELDS = ["english", "base", "past", "present", "future"]
