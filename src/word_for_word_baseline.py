"""
Word-for-word baseline: tokenize input, replace each token with its top lexicon
translation, return space-concatenated string.
"""

from typing import Optional, Union

from .utils.tokenize_text import tokenize_text
from .build_prompt import LexiconBuilder, LexiconBuilderPanlex, LexiconBuilderGTrans
from .utils.lang_codes import LANGS


class WordForWordBaseline:
    def __init__(self, input_lang: str, output_lang: str, lexicon: str = "gtrans"):
        self.input_lang = input_lang
        self.output_lang = output_lang
        self.lexicon = lexicon
        self.lexicon_builder = self._get_lexicon_builder()



    def _get_lexicon_builder(self):
        """Build a LexiconBuilder for input_lang -> output_lang. One language must be English."""
        if self.input_lang not in LANGS or self.output_lang not in LANGS:
            raise ValueError(f"Unsupported language code(s). input_lang={self.input_lang!r}, output_lang={self.output_lang!r}")
        eng = "eng_Latn"
        if self.input_lang == eng and self.output_lang == eng:
            raise ValueError("input_lang and output_lang cannot both be English.")
        if self.input_lang == eng:
            language = self.output_lang
            pivot_language = eng
            direction = "generation"
        elif self.output_lang == eng:
            language = self.input_lang
            pivot_language = eng
            direction = "comprehension"
        else:
            raise ValueError(
                "Word-for-word baseline requires one of input_lang or output_lang to be eng_Latn."
            )
        if self.lexicon == "panlex":
            return LexiconBuilderPanlex(language, pivot_language, direction)
        if self.lexicon == "gtrans":
            return LexiconBuilderGTrans(language, pivot_language, direction)
        raise ValueError(f"Unknown lexicon {self.lexicon}. Use 'panlex' or 'gtrans'.")


    def word_for_word_translate(self, input_str: str) -> str:
        """
        Return a word-for-word translation of the input using fast tokenization and
        lexicon lookups (top match per word).

        Args:
            input_str: Source text.
            input_lang: NLLB-style language code for the input (e.g. "fra_Latn", "eng_Latn").
            output_lang: NLLB-style language code for the output.
            lexicon_builder: If provided, use this builder and ignore `lexicon`. Otherwise
                a builder is created for input_lang -> output_lang (one must be eng_Latn).
            lexicon: Which lexicon to use when creating a builder: "gtrans" or "panlex".

        Returns:
            Space-concatenated string of lexicon equivalents (one per token); if no
            translation is found for a token, the original token is kept.
        """
        tokens = tokenize_text(input_str, self.input_lang, fast=True)
        parts = []

        for word in tokens:
            try:
                _, translations = self.lexicon_builder.fuzzy_match_translations(word, k=1)
            except Exception:
                translations = []
            if translations and translations[0]:
                parts.append(translations[0].strip().split(",")[0])
            else:
                parts.append(word)

        return " ".join(parts)
