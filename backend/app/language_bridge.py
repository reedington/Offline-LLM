"""Experimental African-language bridge (Phase 6D).

Disabled by default (FEATURE_AFRICAN_LANG=false). When enabled, questions in
Yoruba, Hausa, or Swahili are detected heuristically, translated to English
by a *local* NLLB model (CTranslate2 int8 — never a cloud API), answered by
the stable English RAG path, and optionally translated back.

Design rules:
- The English path is never touched when the flag is off or the text is English.
- Heavy imports (ctranslate2, transformers) are lazy so the default product
  never pays their memory cost.
- If translation models are absent, the bridge reports itself unavailable and
  the caller falls back to the standard English path.
"""

from __future__ import annotations

import re
import unicodedata
from functools import lru_cache

from app.config import NLLB_CT2_DIR, NLLB_TOKENIZER_DIR

SUPPORTED_LANGUAGES = {"yo", "ha", "sw"}

NLLB_CODES = {
    "en": "eng_Latn",
    "yo": "yor_Latn",
    "ha": "hau_Latn",
    "sw": "swh_Latn",
}

# Distinctive orthography: Yoruba uses dot-below vowels/consonants and tone
# marks; Hausa uses hooked consonants.
_YORUBA_CHARS = set("ẹọṣẸỌṢ")
_HAUSA_CHARS = set("ɓɗƙƴƁƊƘƳ")

# Common high-frequency words per language, matched on whole words.
_MARKERS = {
    "yo": {
        "báwo", "bawo", "elo", "eelo", "kini", "kíni", "ni", "jẹ́", "jẹ", "ṣe",
        "owó", "owo", "melo", "mélòó", "àti", "ati", "fún", "fun", "ìwé", "iwe",
        "ọjọ́", "ojo", "sanwó", "sanwo", "ta", "wo", "inú", "inu",
    },
    "ha": {
        "menene", "mene", "nawa", "yaya", "ina", "wane", "wace", "kudin", "kudi",
        "biyan", "kwanaki", "kwana", "cikin", "za", "ne", "ce", "don", "mai",
        "ranar", "lokacin", "nan", "shi", "ita", "sune", "kuma", "amma", "da",
    },
    "sw": {
        "nini", "ngapi", "je", "gani", "kiasi", "bei", "malipo", "siku", "lipa",
        "kulipa", "ni", "ya", "wa", "za", "cha", "kwa", "katika", "ankara",
        "mkataba", "hati", "biashara", "pesa", "shilingi", "muda", "tarehe",
    },
    "en": {
        "the", "is", "are", "what", "when", "how", "much", "many", "do", "does",
        "payment", "invoice", "due", "total", "cost", "price", "days", "return",
        "a", "an", "of", "for", "in", "on", "to", "and",
    },
}


def _words(text: str) -> list[str]:
    return re.findall(r"[\w'’áàéèíìóòúùẹọṣɓɗƙƴâêîôû]+", text.lower(), re.UNICODE)


def detect_language(text: str) -> str:
    """Best-effort detection among en/yo/ha/sw. Defaults to English."""
    text = unicodedata.normalize("NFC", text or "")
    if any(char in _YORUBA_CHARS for char in text):
        return "yo"
    if any(char in _HAUSA_CHARS for char in text):
        return "ha"
    # Yoruba is written with dense tone diacritics; Hausa and Swahili are
    # essentially unaccented Latin. Three or more tone-marked vowels is a
    # strong Yoruba signal even without dot-below characters.
    tone_marked = sum(1 for char in text.lower() if char in "àáèéìíòóùú")
    if tone_marked >= 3:
        return "yo"

    words = _words(text)
    if not words:
        return "en"
    scores = {
        lang: sum(1 for word in words if word in markers)
        for lang, markers in _MARKERS.items()
    }
    best = max(scores, key=lambda lang: scores[lang])
    # Require a clear signal before claiming a non-English language: at least
    # two marker hits and strictly more than the English score.
    if best != "en" and (scores[best] < 2 or scores[best] <= scores["en"]):
        return "en"
    return best


class NLLBTranslator:
    """Local NLLB via CTranslate2 int8. Loads lazily; never touches the network."""

    def __init__(self, model_dir=NLLB_CT2_DIR, tokenizer_dir=NLLB_TOKENIZER_DIR):
        self.model_dir = model_dir
        self.tokenizer_dir = tokenizer_dir
        self._translator = None
        self._tokenizers: dict[str, object] = {}

    def available(self) -> bool:
        if not (self.model_dir.exists() and self.tokenizer_dir.exists()):
            return False
        try:
            import ctranslate2  # noqa: F401
            import transformers  # noqa: F401
        except ImportError:
            return False
        return True

    def _load(self):
        if self._translator is None:
            import ctranslate2

            self._translator = ctranslate2.Translator(str(self.model_dir), device="cpu", compute_type="int8")
        return self._translator

    def _tokenizer(self, source_language: str):
        if source_language not in self._tokenizers:
            from transformers import AutoTokenizer

            self._tokenizers[source_language] = AutoTokenizer.from_pretrained(
                str(self.tokenizer_dir),
                src_lang=NLLB_CODES[source_language],
                local_files_only=True,
            )
        return self._tokenizers[source_language]

    def translate(self, text: str, source_language: str, target_language: str) -> str:
        translator = self._load()
        tokenizer = self._tokenizer(source_language)
        tokens = tokenizer.convert_ids_to_tokens(tokenizer.encode(text))
        results = translator.translate_batch(
            [tokens],
            target_prefix=[[NLLB_CODES[target_language]]],
        )
        output_tokens = results[0].hypotheses[0][1:]
        return tokenizer.decode(tokenizer.convert_tokens_to_ids(output_tokens))


class LanguageBridge:
    """Detect -> translate to English -> English RAG -> optional back-translation."""

    def __init__(self, translator=None):
        self.translator = translator if translator is not None else NLLBTranslator()

    def available(self) -> bool:
        return self.translator.available()

    def process(self, question: str, answer_fn) -> dict | None:
        """Answer a non-English question through the English pipeline.

        Returns None when the question is English or the bridge is not
        available — the caller must then use the standard English path.
        `answer_fn(english_question)` runs the normal calculator/RAG path.
        """
        language = detect_language(question)
        if language == "en" or language not in SUPPORTED_LANGUAGES:
            return None
        if not self.available():
            return None

        english_question = self.translator.translate(question, language, "en")
        result = answer_fn(english_question)

        translated_answer = None
        try:
            translated_answer = self.translator.translate(result["answer"], "en", language)
        except Exception:
            translated_answer = None

        bridged = dict(result)
        bridged["bridge"] = {
            "detected_language": language,
            "english_question": english_question,
            "english_answer": result["answer"],
            "experimental": True,
        }
        if translated_answer:
            bridged["answer"] = translated_answer
        return bridged


@lru_cache(maxsize=1)
def get_bridge() -> LanguageBridge:
    return LanguageBridge()
