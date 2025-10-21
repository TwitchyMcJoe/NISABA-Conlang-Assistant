# widgets/dictionary_tab.py
import os
from tkinter import ttk, simpledialog, messagebox
import tkinter as tk

from utils.file_io import load_csv, save_csv, ensure_language_dir
from utils.audio_utils import play_audio_file
from constants import DICT_FILE, DICT_FIELDS, CONJ_FILE, CONJ_FIELDS, GRAMMAR_TEXT


def build_dictionary_tab(app):
    """Attach the Dictionary tab to the main notebook."""
    tab = ttk.Frame(app.notebook)
    app.notebook.add(tab, text="Dictionary")

    ctrl = ttk.Frame(tab)
    ctrl.pack(fill="x", padx=6, pady=6)
    ttk.Button(ctrl, text="Reload From Language", command=lambda: reload_dictionary_from_lang(app)).pack(side="left", padx=4)
#    ttk.Button(ctrl, text="Add", command=lambda: add_word_button(app)).pack(side="left", padx=4)
    ttk.Button(ctrl, text="Add", command=lambda: add_word(app)).pack(side="left", padx=4)
    ttk.Button(ctrl, text="Edit", command=lambda: edit_word_button(app)).pack(side="left", padx=4)
    ttk.Button(ctrl, text="Delete", command=lambda: delete_word_button(app)).pack(side="left", padx=4)
    ttk.Button(ctrl, text="Recheck Consistency", command=lambda: recheck_consistency(app)).pack(side="left", padx=4)
    ttk.Button(ctrl, text="Auto-sync Conjugations", command=lambda: sync_conjugations_with_dictionary(app)).pack(side="left", padx=4)
    ttk.Button(ctrl, text="Play Pronunciation (selected)", command=lambda: play_selected_pronunciation(app)).pack(side="left", padx=6)

    
    cols = ("english","conlang","pos","gender","definition","pronunciation","loanword","cons_phon","cons_spell")
    app.dict_tree = ttk.Treeview(tab, columns=cols, show="headings", height=20)

    headers = [
        ("english","English"),("conlang","Conlang"),("pos","Part of Speech"),
        ("gender","Gender"),("definition","Definition"),("pronunciation","Pronunciation"),
        ("loanword","Loanword?"),("cons_phon","Consistent (Phon)"),("cons_spell","Consistent (Spell)")
    ]
    widths = [140,140,120,100,260,160,100,140,140]

    app.dict_tree.bind("<Double-1>", lambda e: on_dict_double_click(app, e))

    for (col,txt),w in zip(headers,widths):
        app.dict_tree.heading(col, text=txt)
        app.dict_tree.column(col, width=w)
    app.dict_tree.pack(fill="both", expand=True, padx=6, pady=6)
    from utils.table_edit import enable_treeview_editing
    enable_treeview_editing(app.dict_tree, save_callback=save_dictionary, app=app)

# -------------------------
# Helper functions
# -------------------------

def reload_dictionary_from_lang(app):
    if not app.current_language:
        messagebox.showwarning("No language", "Select a language first.")
        return
    load_dictionary(app, app.current_language)

def load_dictionary(app, lang):
    app.current_language = lang
    app.title(f"Conlang Assistant - {lang}")
    langdir = ensure_language_dir(lang)
    rows = load_csv(os.path.join(langdir, DICT_FILE), DICT_FIELDS)
    app.dictionary = {}
    for r in rows:
        eng = (r.get("english") or "").strip()
        if not eng:
            continue
        app.dictionary[eng.lower()] = {
            "conlang": r.get("conlang",""),
            "pos": r.get("pos",""),
            "gender": r.get("gender",""),
            "definition": r.get("definition",""),
            "pronunciation": r.get("pronunciation",""),
            "loanword": r.get("loanword","NO"),   # default NO
            "consistent_phon": r.get("consistent_phon",""),
            "consistent_spell": r.get("consistent_spell","")
        }

    # load conjugations too
    conj_path = os.path.join(langdir, CONJ_FILE)
    app.conjugations = load_csv(conj_path, CONJ_FIELDS) if os.path.exists(conj_path) else []

    # load grammar text if present
    gf = os.path.join(langdir, GRAMMAR_TEXT)
    if os.path.exists(gf) and hasattr(app, "grammar_editor"):
        with open(gf, "r", encoding="utf-8") as f:
            app.grammar_editor.delete("1.0", tk.END)
            app.grammar_editor.insert(tk.END, f.read())

    update_dict_table(app)

def update_dict_table(app):
    app.dict_tree.delete(*app.dict_tree.get_children())
    for eng, data in app.dictionary.items():
        pron = data["pronunciation"]
        conlang = data["conlang"]
        loan = data.get("loanword","NO")

        # recompute consistency
        phon_cons = "PASS" if check_phonology_consistency(app, pron) else "FAIL"
        spell_cons = "PASS" if check_spelling_consistency(app, conlang, pron) else "FAIL"

        app.dict_tree.insert("", "end", values=(
            eng, conlang, data["pos"], data["gender"],
            data["definition"], pron, loan,
            phon_cons, spell_cons
        ))


def add_word(app):
    # 8 columns: english, conlang, pos, gender, definition, pronunciation, consistent_phon, consistent_spell
    empty = ("NEW", "", "", "", "", "", "NO", "", "")
    app.dict_tree.insert("", "end", values=empty)
    

def add_word_button(app):
    eng = simpledialog.askstring("English", "English word:")
    if not eng:
        return
    con = simpledialog.askstring("Conlang", "Conlang word:")
    pos = simpledialog.askstring("POS", "Part of speech:")
    gen = simpledialog.askstring("Gender", "Gender:")
    defi = simpledialog.askstring("Definition", "Definition:")
    pron = simpledialog.askstring("Pronunciation", "Pronunciation:")
    app.dictionary[eng.lower()] = {
        "conlang": con or "", "pos": pos or "", "gender": gen or "",
        "definition": defi or "", "pronunciation": pron or "",
        "consistent_phon": "", "consistent_spell": ""
    }
    save_dictionary(app)
    update_dict_table(app)

def edit_word_button(app):
    sel = app.dict_tree.selection()
    if not sel:
        messagebox.showwarning("Select", "Select a word to edit")
        return
    item = sel[0]
    vals = app.dict_tree.item(item, "values")
    eng = vals[0]
    data = app.dictionary.get(eng.lower(), {})
    con = simpledialog.askstring("Conlang", "Conlang word:", initialvalue=data.get("conlang",""))
    if con is None: return
    data["conlang"] = con
    data["pos"] = simpledialog.askstring("POS", "Part of speech:", initialvalue=data.get("pos","")) or ""
    data["gender"] = simpledialog.askstring("Gender", "Gender:", initialvalue=data.get("gender","")) or ""
    data["definition"] = simpledialog.askstring("Definition", "Definition:", initialvalue=data.get("definition","")) or ""
    data["pronunciation"] = simpledialog.askstring("Pronunciation", "Pronunciation:", initialvalue=data.get("pronunciation","")) or ""
    app.dictionary[eng.lower()] = data
    save_dictionary(app)
    update_dict_table(app)

def delete_word_button(app):
    sel = app.dict_tree.selection()
    if not sel:
        messagebox.showwarning("Select", "Select a word to delete")
        return
    item = sel[0]
    eng = app.dict_tree.item(item, "values")[0]
    if messagebox.askyesno("Delete", f"Delete word '{eng}'?"):
        app.dictionary.pop(eng.lower(), None)
        save_dictionary(app)
        update_dict_table(app)

def save_dictionary(app):
    if not app.current_language:
        return
    rows = []
    for iid in app.dict_tree.get_children():
        eng, con, pos, gen, defi, pron, loan, _, _ = app.dict_tree.item(iid, "values")
        phon_cons = "PASS" if check_phonology_consistency(app, pron) else "FAIL"
        spell_cons = "PASS" if check_spelling_consistency(app, con, pron) else "FAIL"
        rows.append({
            "english": eng, "conlang": con, "pos": pos, "gender": gen,
            "definition": defi, "pronunciation": pron,
            "loanword": loan,
            "consistent_phon": phon_cons, "consistent_spell": spell_cons
        })
    langdir = ensure_language_dir(app.current_language)
    save_csv(os.path.join(langdir, DICT_FILE), DICT_FIELDS, rows)


def sync_conjugations_with_dictionary(app):
    if not app.current_language:
        messagebox.showwarning("No language", "Select a language first.")
        return

    # Collect all verbs from dictionary
    verbs = [(eng, data["conlang"]) for eng, data in app.dictionary.items()
             if data.get("pos", "").lower() == "verb"]

    # Track existing English lemmas already in conjugations
    existing = {row.get("english", "").lower() for row in app.conjugations}

    new_rows = []
    for eng, con in verbs:
        if eng.lower() not in existing:
            row = {"english": eng, "base": con, "past": "", "present": "", "future": ""}
            new_rows.append(row)
            app.conjugations.append(row)

            # Also insert into the Conjugations tree if it exists
            if hasattr(app, "conj_tree"):
                app.conj_tree.insert("", "end", values=(eng, con, "", "", ""))

    # Save to CSV
    from utils.file_io import ensure_language_dir, save_csv
    from constants import CONJ_FILE, CONJ_FIELDS
    langdir = ensure_language_dir(app.current_language)
    save_csv(os.path.join(langdir, CONJ_FILE), CONJ_FIELDS, app.conjugations)

    messagebox.showinfo("Sync", f"Added {len(new_rows)} new verbs to conjugations. (Make sure to 'Reload from language' first.)")

def play_selected_pronunciation(app):
    sel = app.dict_tree.selection()
    if not sel:
        return
    item = sel[0]
    vals = app.dict_tree.item(item, "values")
    pron = vals[5]  # pronunciation column (IPA string)

    if not pron:
        messagebox.showinfo("Pronunciation", f"No pronunciation set for {vals[0]}")
        return

    # Root-level ipa_audio folder
    from utils.file_io import get_ipa_audio_dir
    audio_dir = get_ipa_audio_dir()


    # Iterate through each IPA character
    for ch in pron:
        if ch.isspace():
            continue
        filename = f"{ch}.mp3"  # assumes files like "a.mp3", "ʃ.mp3"
        path = os.path.join(audio_dir, filename)
        if os.path.exists(path):
            play_audio_file(path)
        else:
            messagebox.showwarning("Missing", f"No audio file for IPA symbol '{ch}' in {audio_dir}")

def check_phonology_consistency(app, ipa_string):
    """Return True if all IPA symbols in the pronunciation are in the phoneme inventory."""
    langdir = ensure_language_dir(app.current_language)
    rows = load_csv(os.path.join(langdir, "phonology.csv"), ["ipa","example","type","notes"])
    phonemes = {r["ipa"] for r in rows if r.get("ipa")}
    # simple check: every character in ipa_string must be in phonemes
    for ch in ipa_string:
        if ch.isspace():
            continue
        if ch not in phonemes:
            return False
    return True

##def check_spelling_consistency(app, conlang_word, ipa_string):
##    """Return True if applying spelling rules to IPA yields the conlang word."""
##    langdir = ensure_language_dir(app.current_language)
##    rules_path = os.path.join(langdir, "spelling_rules.txt")
##    if not os.path.exists(rules_path):
##        return True  # no rules defined, assume consistent
##    with open(rules_path, "r", encoding="utf-8") as f:
##        rules = [line.strip() for line in f if "->" in line]
##    # apply rules sequentially
##    spelling = ipa_string
##    for rule in rules:
##        src, tgt = rule.split("->", 1)
##        spelling = spelling.replace(src.strip(), tgt.strip())
##    return spelling == conlang_word

def check_spelling_consistency(app, conlang_word, ipa_string):
    """Return True if applying spelling rules to IPA yields the conlang word."""
    langdir = ensure_language_dir(app.current_language)
    rules_path = os.path.join(langdir, "spelling_rules.csv")
    if not os.path.exists(rules_path):
        return True  # no rules defined, assume consistent

    rows = load_csv(rules_path, ["ipa", "romanization"])
    rules = [(r["ipa"], r["romanization"]) for r in rows if r.get("ipa")]

    spelling = ipa_string
    for ipa, roman in rules:
        if ipa and roman:
            spelling = spelling.replace(ipa, roman)

    return spelling == conlang_word


def recheck_consistency(app):
    if not app.current_language:
        messagebox.showwarning("No language", "Select a language first.")
        return

    for iid in app.dict_tree.get_children():
        vals = app.dict_tree.item(iid, "values")
        # Now 9 columns: english, conlang, pos, gender, definition, pronunciation, loanword, cons_phon, cons_spell
        eng, con, pos, gen, defi, pron, loan, _, _ = vals

        phon_cons = "PASS" if check_phonology_consistency(app, pron) else "FAIL"
        spell_cons = "PASS" if check_spelling_consistency(app, con, pron) else "FAIL"

        app.dict_tree.item(iid, values=(
            eng, con, pos, gen, defi, pron, loan, phon_cons, spell_cons
        ))

    messagebox.showinfo("Consistency", "Rechecked dictionary consistency against phonology and spelling rules.")

def on_dict_double_click(app, event):
    """If user double-clicks a FAIL in Consistent (Spell), jump to Spelling Rules tab."""
    region = app.dict_tree.identify("region", event.x, event.y)
    if region != "cell":
        return

    rowid = app.dict_tree.identify_row(event.y)
    colid = app.dict_tree.identify_column(event.x)
    if not rowid or not colid:
        return

    col_index = int(colid.replace("#", "")) - 1
    columns = app.dict_tree["columns"]
    if col_index < 0 or col_index >= len(columns):
        return
    col_name = columns[col_index]

    # Only trigger on the Consistent (Spell) column
    if col_name != "cons_spell":
        return

    vals = app.dict_tree.item(rowid, "values")
    cell_val = vals[col_index]
    if cell_val != "FAIL":
        return

    # Jump to Phonology & Spelling → Spelling Rules
    for i in range(app.notebook.index("end")):
        if app.notebook.tab(i, "text") == "Phonology & Spelling":
            app.notebook.select(i)
            try:
                phonology_tab = app.notebook.nametowidget(app.notebook.tabs()[i])
                # Find the inner Notebook (sub_nb)
                for child in phonology_tab.winfo_children():
                    if isinstance(child, ttk.Notebook):
                        sub_nb = child
                        for j in range(sub_nb.index("end")):
                            if sub_nb.tab(j, "text") == "Spelling Rules":
                                sub_nb.select(j)
                                break
                        break
            except Exception as e:
                print("Could not switch to Spelling Rules:", e)
            break
