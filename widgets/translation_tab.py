# widgets/translation_tab.py
import os
import re
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

from constants import (
    LANG_ROOT, GRAMMAR_TEXT, CONJ_FILE, CONJ_FIELDS,
    FONTS_DIRNAME, DICT_FILE, DICT_FIELDS
)
from utils.file_io import load_csv
from utils.conjugation_utils import analyze_verb_form


def build_translation_tab(app):
    tab = ttk.Frame(app.notebook)
    app.notebook.add(tab, text="Translation")

    ttk.Label(tab, text="Translation Tool",
              font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=10, pady=(8, 4))

    # English → Conlang
    ttk.Label(tab, text="English → Conlang").pack(anchor="w", padx=8)
    app.trans_input = tk.Text(tab, height=4, wrap="word",
                              bg="#1b1b1b", fg="#eaeaea", insertbackground="white")
    app.trans_input.pack(fill="x", padx=8, pady=4)
    ttk.Button(tab, text="Translate to Conlang",
               command=lambda: translate_to_conlang(app)).pack(anchor="w", padx=8, pady=(0, 6))

    # Conlang → English
    ttk.Label(tab, text="Conlang → English").pack(anchor="w", padx=8)
    app.trans_input_rev = tk.Text(tab, height=4, wrap="word",
                                  bg="#1b1b1b", fg="#eaeaea", insertbackground="white")
    app.trans_input_rev.pack(fill="x", padx=8, pady=4)
    ttk.Button(tab, text="Translate to English",
               command=lambda: translate_to_english(app)).pack(anchor="w", padx=8, pady=(0, 6))

    # Result
    ttk.Label(tab, text="Result:").pack(anchor="w", padx=8)
    app.trans_output = tk.Text(tab, height=4, wrap="word",
                               bg="#1b1b1b", fg="#eaeaea", insertbackground="white")
    app.trans_output.pack(fill="x", padx=8, pady=4)

    # Pronunciation
    ttk.Label(tab, text="Pronunciation:").pack(anchor="w", padx=8)
    app.trans_pron = ttk.Label(tab, text="", background="#2b2b2b", foreground="lightblue")
    app.trans_pron.pack(anchor="w", padx=8, pady=(0, 6))

    # Pronunciation playback
    play_frame = ttk.Frame(tab)
    play_frame.pack(anchor="w", padx=8, pady=(0, 6))
    ttk.Button(play_frame, text="Play Pronunciation",
               command=lambda: play_pronunciation(app)).pack(side="left")

    # Glyph preview canvas
    ttk.Label(tab, text="Glyph Preview:").pack(anchor="w", padx=8)
    app.trans_canvas = tk.Canvas(tab, bg="white", height=200)
    app.trans_canvas.pack(fill="both", expand=True, padx=8, pady=8)
    app.trans_canvas.image_refs = []


# -------------------------
# Translation functions
# -------------------------

def translate_to_conlang(app):
    text = app.trans_input.get("1.0", tk.END).strip()
    if not text:
        return
    if not app.current_language:
        messagebox.showwarning("No language", "Load a language first.")
        return
    if not app.dictionary:
        messagebox.showwarning("No dictionary", "Load a language first.")
        return

    # Parse grammar from the editor if present; else from grammar.txt
    grammar_text = ""
    if hasattr(app, "grammar_editor"):
        grammar_text = app.grammar_editor.get("1.0", tk.END)
        parsed = parse_grammar_text(grammar_text)
    else:
        parsed = parse_grammar_file(app)

    # Apply phrase-level transforms
    transformed_phrase = apply_phrase_transforms(text, parsed.get("transforms", []))

    out_words = []
    for tok in transformed_phrase.split():
        con = f"[{tok}]"
        pos = ""

        # Always lemmatize
        lemma, conj_type = analyze_verb_form(tok)

        # Try dictionary lookup on token, then lemma
        entry = app.dictionary.get(tok.lower()) or app.dictionary.get(lemma.lower())

        if entry:
            con = entry.get("conlang", "") or con
            pos = (entry.get("pos", "") or "").lower()

            # If it's a verb, apply conjugation
            if pos == "verb":
                con_base = entry.get("conlang", "")
                tense = app.tense_var.get() if hasattr(app, "tense_var") else "present"
                for row in app.conjugations:
                    if (row.get("english") or "").lower() == lemma.lower():
                        con = row.get(tense, con_base) or con_base
                        break

        # Apply prefixes/suffixes
        con = apply_prefix_suffix(con, pos, parsed)
        out_words.append(con)

    result = " ".join(out_words)

    # Output + pronunciation
    app.trans_output.delete("1.0", tk.END)
    app.trans_output.insert(tk.END, result)

    first_word = text.split()[0] if text.split() else ""
    pron = app.dictionary.get(first_word.lower(), {}).get("pronunciation", "") if first_word else ""
    app.trans_pron.configure(text=pron or "—")

    render_glyphs(app, result)

##def translate_to_conlang(app):
##    text = app.trans_input.get("1.0", tk.END).strip()
##    if not text:
##        return
##    if not app.current_language:
##        messagebox.showwarning("No language", "Load a language first.")
##        return
##    if not app.dictionary:
##        messagebox.showwarning("No dictionary", "Load a language first.")
##        return
##
##    # Parse grammar from the editor if present; else from grammar.txt
##    grammar_text = ""
##    if hasattr(app, "grammar_editor"):
##        grammar_text = app.grammar_editor.get("1.0", tk.END)
##        parsed = parse_grammar_text(grammar_text)
##    else:
##        parsed = parse_grammar_file(app)
##
##    # Apply phrase-level transforms (supports {placeholders} and "=>")
##    transformed_phrase = apply_phrase_transforms(text, parsed.get("transforms", []))
##
##    # Tokenize after transforms, then dictionary + word-level rules
##    out_words = []
####    for tok in transformed_phrase.split():
##        entry = app.dictionary.get(tok.lower())
##        if entry:
##            con = entry.get("conlang", "") or ""
##            pos = (entry.get("pos", "") or "").lower()
##        else:
##            con = f"[{tok}]"
##            pos = ""
##
##        # Prefixes/Suffixes from parsed grammar
##        con = apply_prefix_suffix(con, pos, parsed)
##
##        # Conjugations by selected tense (only for verbs)
##        if pos == "verb" and getattr(app, "conjugations", None):
##            tense = app.tense_var.get() if hasattr(app, "tense_var") else "present"
##            con = apply_conjugation_for_token(con, tok, app.conjugations, tense)
##
##        out_words.append(con)
##
##
##
##    for tok in transformed_phrase.split():
##        entry = app.dictionary.get(tok.lower())
##        if entry:
##            con = entry.get("conlang", "") or ""
##            pos = (entry.get("pos", "") or "").lower()
##        else:
##            con = f"[{tok}]"
##            pos = ""
##
##        # Prefixes/Suffixes
##        con = apply_prefix_suffix(con, pos, parsed)
##
##        #New verb handling
##        if pos == "verb":
##            lemma, conj_type = analyze_verb_form(tok)
##
##            # Look up lemma in dictionary
##            base_entry = app.dictionary.get(lemma.lower())
##            if base_entry:
##                con_base = base_entry.get("conlang", "")
##                tense = app.tense_var.get() if hasattr(app, "tense_var") else "present"
##
##                # Match against conjugations.csv
##                for row in app.conjugations:
##                    if row.get("english") == lemma:
##                        con = row.get(tense, con_base) or con_base
##                        break
##                else:
##                    con = con_base
##            else:
##                con = f"[{tok}]"
##
##        out_words.append(con)
##
##    result = " ".join(out_words)
##
##    # Output + pronunciation (first input word)
##    app.trans_output.delete("1.0", tk.END)
##    app.trans_output.insert(tk.END, result)
##
##    first_word = text.split()[0] if text.split() else ""
##    pron = app.dictionary.get(first_word.lower(), {}).get("pronunciation", "") if first_word else ""
##    app.trans_pron.configure(text=pron or "—")
##
##    # Render glyphs
##    render_glyphs(app, result)


def translate_to_english(app):
    text = app.trans_input_rev.get("1.0", tk.END).strip().lower()
    if not text:
        return
    if not app.dictionary:
        messagebox.showwarning("No dictionary", "Load a language first.")
        return

    words = text.split()
    out = []

    for w in words:
        eng = None

        # 1) Direct reverse dictionary lookup
        for k, v in app.dictionary.items():
            if v.get("conlang", "").lower() == w:
                eng = k
                break

        # 2) If not found, check conjugations.csv
        if not eng and getattr(app, "conjugations", None):
            for row in app.conjugations:
                for tense in ("past", "present", "future"):
                    if (row.get(tense) or "").lower() == w:
                        eng = row.get("english", "")
                        break
                if eng:
                    break

        # 3) Fallback
        if not eng:
            eng = f"[{w}]"

        out.append(eng)

    result = " ".join(out)
    app.trans_output.delete("1.0", tk.END)
    app.trans_output.insert(tk.END, result)
    app.trans_pron.configure(text="—")

    render_glyphs(app, text)

# -------------------------
# Grammar parsing
# -------------------------

def parse_grammar_text(text):
    """
    Parse grammar rules from freeform editor text (old style):
    - prefix(pos): a-, b-
    - suffix(pos): -x, -y
    - transforms: left => right
    """
    prefixes = {}
    suffixes = {}
    transforms = []
    notes = []
    for ln in text.splitlines():
        L = ln.strip()
        if not L or L.startswith("#"):
            continue

        if L.lower().startswith("prefix(") and ":" in L:
            try:
                inside = L[L.index("(") + 1:L.index(")")]
                pos = inside.strip().lower()
                val = L.split(":", 1)[1].strip()
                prefixes[pos] = [v.strip() for v in val.split(",") if v.strip()]
            except Exception:
                notes.append(L)
            continue

        if L.lower().startswith("suffix(") and ":" in L:
            try:
                inside = L[L.index("(") + 1:L.index(")")]
                pos = inside.strip().lower()
                val = L.split(":", 1)[1].strip()
                suffixes[pos] = [v.strip() for v in val.split(",") if v.strip()]
            except Exception:
                notes.append(L)
            continue

        if "=>" in L:
            left, right = L.split("=>", 1)
            # Trim stray quotes on right side if present
            transforms.append((left.strip(), right.strip().strip('"').strip("'")))
            continue

        notes.append(L)

    return {"prefixes": prefixes, "suffixes": suffixes, "transforms": transforms, "notes": notes}


def parse_grammar_file(app):
    """
    Parse grammar.txt (sectioned format saved by grammar_tab):
    - [PREFIXES] table with header "POS,Prefixes"
    - [SUFFIXES] table with header "POS,Suffixes"
    - [TRANSFORMS] lines like "{owner}'s {object} => the {object} of {owner}"
    Returns same structure as parse_grammar_text.
    """
    prefixes = {}
    suffixes = {}
    transforms = []

    if not app.current_language:
        return {"prefixes": prefixes, "suffixes": suffixes, "transforms": transforms}

    path = os.path.join(LANG_ROOT, app.current_language, GRAMMAR_TEXT)
    if not os.path.exists(path):
        return {"prefixes": prefixes, "suffixes": suffixes, "transforms": transforms}

    section = None
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            ln = raw.strip()
            if not ln:
                continue
            if ln.startswith("[") and ln.endswith("]"):
                section = ln.strip("[]").upper()
                continue

            # Tables
            if section == "PREFIXES":
                # Skip header line like "POS,Prefixes"
                if ln.lower().startswith("pos,"):
                    continue
                if "," in ln:
                    pos, pfxs = ln.split(",", 1)
                    pos = pos.strip().lower()
                    # split by commas, allow multiple prefixes; skip empties
                    values = [v.strip() for v in pfxs.split(",") if v.strip()]
                    if values:
                        prefixes[pos] = values

            elif section == "SUFFIXES":
                if ln.lower().startswith("pos,"):
                    continue
                if "," in ln:
                    pos, sfxs = ln.split(",", 1)
                    pos = pos.strip().lower()
                    values = [v.strip() for v in sfxs.split(",") if v.strip()]
                    if values:
                        suffixes[pos] = values

            elif section == "TRANSFORMS":
                # Lines like: pattern => replacement
                if "=>" in ln:
                    left, right = ln.split("=>", 1)
                    transforms.append((left.strip(), right.strip().strip('"').strip("'")))

    return {"prefixes": prefixes, "suffixes": suffixes, "transforms": transforms}


# -------------------------
# Transform and word rules
# -------------------------

def apply_phrase_transforms(sentence, transforms):
    """
    Apply transforms to the sentence.
    Supports placeholder templates like:
      "{owner}'s {object} => the {object} of {owner}"
    Captures apostrophes inside words via [\\w']+.
    """
    s = sentence
    for pattern, replacement in transforms:
        # Normalize quotes
        pattern = pattern.strip().strip('"').strip("'")
        replacement = replacement.strip().strip('"').strip("'")

        # Find placeholders {name}
        names = re.findall(r"\{(\w+)\}", pattern)
        if not names:
            # Simple literal replacement
            s = s.replace(pattern, replacement)
            continue

        # Build regex: replace each {name} with a named group
        regex = re.escape(pattern)
        for name in names:
            # Replace the escaped "{name}" with a named capture allowing apostrophes
            regex = regex.replace(r"\{" + name + r"\}", fr"(?P<{name}>[\w']+)")
        # Allow flexible spacing
        regex = regex.replace(r"\ ", r"\s+")

        try:
            s = re.sub(regex, lambda m: replacement.format(**{n: m.group(n) for n in names}), s)
        except Exception:
            # Fallback: raw replacement if format fails
            try:
                s = re.sub(regex, replacement, s)
            except Exception:
                pass

    return s


def apply_prefix_suffix(con_word, pos, parsed):
    if not con_word:
        return con_word
    pfx_list = parsed.get("prefixes", {}).get(pos, [])
    sfx_list = parsed.get("suffixes", {}).get(pos, [])
    if pfx_list:
        con_word = pfx_list[0] + con_word
    if sfx_list:
        con_word = con_word + sfx_list[0]
    return con_word


def apply_conjugation_for_token(con_word, english_token, conjugations, tense):
    """
    Apply conjugation using the selected tense.
    Prefers matching by the English token (row['english'] == english_token).
    If not found, attempts matching by base == conlang base.
    """
    # 1) Try English match
    for row in conjugations:
        if (row.get("english") or "").lower() == (english_token or "").lower():
            val = row.get(tense, "") or ""
            return val if val else con_word

    # 2) Fallback: match by conlang base
    for row in conjugations:
        if (row.get("base") or "").lower() == (con_word or "").lower():
            val = row.get(tense, "") or ""
            return val if val else con_word

    return con_word


# -------------------------
# Glyph rendering
# -------------------------

def render_glyphs(app, text):
    canvas = app.trans_canvas
    canvas.delete("all")
    canvas.image_refs = []

    if not app.current_language:
        return

    fontpath = os.path.join(LANG_ROOT, app.current_language, FONTS_DIRNAME)
    if not os.path.exists(fontpath):
        return
    fonts = [d for d in os.listdir(fontpath) if os.path.isdir(os.path.join(fontpath, d))]
    if not fonts:
        return
    mapping = load_csv(os.path.join(fontpath, fonts[0], "mapping.csv"), ["symbol", "filename"])
    sym_map = {m["symbol"]: m["filename"] for m in mapping if m.get("symbol")}

    sorted_syms = sorted(sym_map.keys(), key=len, reverse=True)
    x, y, line_h = 10, 10, 60
    maxw = int(canvas.winfo_width() or 1000)
    i = 0
    L = len(text)
    while i < L:
        matched = False
        for sym in sorted_syms:
            if text[i:i+len(sym)] == sym:
                fn = sym_map[sym]
                path = os.path.join(fontpath, fonts[0], fn)
                if os.path.exists(path):
                    try:
                        im = Image.open(path)
                        desired_h = 50
                        w, h = im.size
                        scale = desired_h / h if h else 1.0
                        im2 = im.resize((int(w * scale), desired_h), Image.Resampling.LANCZOS)
                        photo = ImageTk.PhotoImage(im2)
                        canvas.create_image(x, y, anchor="nw", image=photo)
                        canvas.image_refs.append(photo)
                        x += im2.width + 4
                        line_h = max(line_h, im2.height + 5)
                    except Exception:
                        canvas.create_text(x, y, anchor="nw", text=sym, font=("Arial", 18))
                        x += 12 * len(sym)
                else:
                    canvas.create_text(x, y, anchor="nw", text=sym, font=("Arial", 18))
                    x += 12 * len(sym)
                i += len(sym)
                matched = True
                break
        if not matched:
            ch = text[i]
            canvas.create_text(x, y, anchor="nw", text=ch, font=("Arial", 18))
            x += 12
            i += 1
        if x > maxw - 60:
            x = 10
            y += line_h
            line_h = 60


# -------------------------
# Pronunciation playback
# -------------------------

def play_pronunciation(app):
    ipa = app.trans_pron.cget("text").strip()
    if not ipa or ipa == "—":
        messagebox.showinfo("No pronunciation", "No pronunciation available to play.")
        return
    if not app.current_language:
        messagebox.showwarning("No language", "Load a language first.")
        return

    from utils.file_io import get_ipa_audio_dir
    ipa_folder = get_ipa_audio_dir()
    if not os.path.exists(ipa_folder):
        messagebox.showinfo("No audio", f"No ipa_audio folder for {app.current_language}.")
        return

    played_any = False
    for ch in ipa:
        if ch in (" ", "/", "|"):
            continue
        found = False
        for ext in (".wav", ".mp3"):
            path = os.path.join(ipa_folder, f"{ch}{ext}")
            if os.path.exists(path):
                found = True
                played_any = True
                try:
                    # Prefer pydub if available, else playsound
                    try:
                        from pydub import AudioSegment
                        from pydub.playback import play as pydub_play
                        seg = AudioSegment.from_file(path)
                        pydub_play(seg)
                    except ImportError:
                        from playsound import playsound
                        playsound(path)
                except Exception as e:
                    print("Audio play error:", e)
                break
        if not found:
            print("No audio file for symbol:", ch)

    if not played_any:
        messagebox.showinfo("No audio", f"No audio files found for pronunciation: {ipa}")
