from nltk.stem import WordNetLemmatizer
from mlconjug3 import Conjugator

lemmatizer = WordNetLemmatizer()
conj = Conjugator(language='en')

def analyze_verb_form(word):
    """
    #Return lemma and conjugation type for an English verb form.
    """
    lemma = lemmatizer.lemmatize(word.lower(), pos="v")
    verb = conj.conjugate(lemma)

    for mood, tenses in verb.conjug_info.items():
        for tense, forms in tenses.items():
            if isinstance(forms, list) and word in [f.lower() for f in forms]:
                return lemma, f"{mood}:{tense}"
            elif isinstance(forms, dict):
                for person, form in forms.items():
                    if word == form.lower():
                        return lemma, f"{mood}:{tense}:{person}"
    return lemma, "unknown"
