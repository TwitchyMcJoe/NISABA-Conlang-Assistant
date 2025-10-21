# file_io.py
import os
import csv
import sys
from constants import LANG_ROOT

def load_csv(path, fieldnames):
    rows = []
    if os.path.exists(path):
        with open(path, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                rows.append({k: r.get(k, "") for k in fieldnames})
    return rows

def save_csv(path, fieldnames, rows):
    d = os.path.dirname(path)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in fieldnames})

def ensure_language_dir(lang):
    if not lang:
        raise ValueError("Language name required")
    p = os.path.join(LANG_ROOT, lang)
    os.makedirs(p, exist_ok=True)
    os.makedirs(os.path.join(p, "fonts"), exist_ok=True)
    return p

def get_languages():
    os.makedirs(LANG_ROOT, exist_ok=True)
    return sorted([
        d for d in os.listdir(LANG_ROOT)
        if os.path.isdir(os.path.join(LANG_ROOT, d))
    ])


def get_app_root():
    """Return the correct application root whether running from source or frozen .exe."""
    if getattr(sys, 'frozen', False):  # running as a bundled exe
        return os.path.dirname(sys.executable)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def get_ipa_audio_dir():
    """Always return the root-level ipa_audio folder."""
    return os.path.join(get_app_root(), "ipa_audio")
