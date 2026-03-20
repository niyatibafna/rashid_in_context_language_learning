'''
This file has BuildPrompt class that build the context for performing inference with ICL.
It takes in:
- task: task key
- language: language key
- cipher: Cipher object
- input: [{"input": str, "output": str, "metadata": dict}]
- prompt_key: str

It returns:
- prompt: str
'''

import asyncio
import os
import sqlite3
import torch
from typing import List, Dict, Any, Union, Tuple

from datasets.arrow_dataset import NonExistentDatasetError
from .ciphers import Cipher
from .task_data import TaskData
from .utils.lang_codes import LANGS, SYNTAX_DESCRIPTIONS, INFLECTION_PARADIGMS_DESCRIPTIONS
from .utils.tokenize_text import tokenize_text
from datasets import load_dataset
import random
from abc import abstractmethod
import stanza
from rapidfuzz import process
from rapidfuzz.distance import Levenshtein
from pathlib import Path
from rank_bm25 import BM25Okapi
from threading import Lock


class BuildPromptLexicon:
    '''
    This class is for building a prompt that contains the translation of all relevant words in the input along with word features and syntax description if requested.
    All language parameters are expected as NLLB style codes.
    '''
    def __init__(
        self, 
        task: str, 
        language: str, 
        cipher_obj: Cipher, 
        prompt_key: str = None, 
        direction: str = None,
        lexicon: str = None, # {panlex, gtrans}
        word_class: str = "all", # {content, function, all}
        nes_only: bool = False, # Whether to only translate NEs
        lemmas_only: bool = False,
        use_lemmatizer: bool = False,
        num_exemplars: int = 0,
        add_word_features: bool = False,
        add_syntax_description: bool = False,
        add_inflection_paradigms: bool = False,
        add_related_language_translation: bool = False,
        cascade_related_language: bool = False, # Whether to first translate to a related language, and then to the target language, only applicable for generation.
        **kwargs
    ):
        self.task = task
        self.language = language
        self.ciphered_name = LANGS[self.language]["ciphered_name"] if cipher_obj is not None else LANGS[self.language]["name"]
        self.ciphered_lang_info = LANGS[self.language]["ciphered_lang_info"]
        self.cipher_obj = cipher_obj
        self.prompt_key = prompt_key
        self.direction = direction
        self.lexicon = lexicon
        self.use_lemmatizer = use_lemmatizer or add_word_features # Whether to add lemmas to word list. Automatically set to True if add_word_features is True.
        self.nes_only = nes_only
        self.add_syntax_description = add_syntax_description
        self.add_inflection_paradigms = add_inflection_paradigms
        self.num_exemplars = num_exemplars
        self.add_related_language_translation = add_related_language_translation
        self.cascade_related_language = cascade_related_language


        print(f"cascade_related_language: {self.cascade_related_language}")

        # Pivot language is the language we're translating to or from, depending on the direction (not target language)
        # It's English unless we're cascading through a related language. We can only cascade through related languages for generation.
        if self.cascade_related_language:
            assert self.direction == "generation", "Cascade related language is only applicable for generation"
            print(f"Setting pivot language to {self.language}'s related language: {LANGS[self.language]['related_language_code']}")
            self.pivot_language = LANGS[self.language]["related_language_code"]
            self.pivot_language_name = LANGS[self.pivot_language]["name"]
        else:
            self.pivot_language = "eng_Latn"
            self.pivot_language_name = "English"
        print(f"Pivot language: {self.pivot_language}, Pivot language name: {self.pivot_language_name}")
        
        if lexicon == "panlex":
            self.lexicon_obj = LexiconBuilderPanlex(language, self.pivot_language, direction)
        elif lexicon == "gtrans":
            self.lexicon_obj = LexiconBuilderGTrans(language, self.pivot_language, direction)
        else:
            print(f"No lexicon provided.")
        self.google_translator = LexiconBuilderGTrans(language, self.pivot_language, direction) # Just for NEs.

        self.word_class = word_class
        self.lemmas_only = lemmas_only

        self.num_exemplars = num_exemplars
        if num_exemplars > 0:
            dev_dataset = TaskData(task, language).load_data_method(direction = direction, split = "dev-exemplars")            
            dev_sources = [item["input"] for item in dev_dataset]
            dev_sources_tokenized = [tokenize_text(item, language, fast=True) for item in dev_sources]
            dev_targets = [item["output"] for item in dev_dataset]
            self.bm25 = BM25Okapi(dev_sources_tokenized)
            self.dev_data = (dev_sources, dev_targets)

        self.add_word_features = add_word_features
        # Map NLLB language codes to Stanza language codes
        
        self._stanza_nlp = self._get_stanza_pipeline() # We always need Stanza for NE handling
        # if self.word_class != "all" or self.lemmas_only or self.add_word_features:
        #     self._stanza_nlp = self._get_stanza_pipeline()
        # else:
        #     self._stanza_nlp = None
        
        # Function word POS tags (closed class)
        self._function_pos_tags = {
            "DET", "PRON", "PREP", "ADP", "CONJ", "CCONJ", "SCONJ", 
            "AUX", "PART", "INTJ", "PUNCT", "NUM", "X"
        }

        if self.add_related_language_translation or self.cascade_related_language: # We need a translator from English to the related language
            from .utils.translate_wrapper import LLMTranslateWrapper, GoogleTranslateWrapper
            related_language_code = LANGS[self.language]["related_language_code"]
            if related_language_code in ["spa_Latn", "fra_Latn"]: # For these HRLs we can use Google Translate
            # if True:
                self.related_language_translator = GoogleTranslateWrapper("eng_Latn", related_language_code) # We're always translating from English to the related language
            else:
                self.related_language_translator = LLMTranslateWrapper("eng_Latn", related_language_code) # We're always translating from English to the related language
            self.related_language_name = LANGS[related_language_code]["name"]

        


    def _get_stanza_pipeline(self) -> stanza.Pipeline:
        """Initialize and return the Stanza pipeline."""
        # We are always parsing the test language, which may be the input or output language, depending on the direction.
        stanza_lang = LANGS[self.language]["stanza_code"] if self.direction == "comprehension" else LANGS[self.pivot_language]["stanza_code"]
        # stanza.download(stanza_lang)

        
        return stanza.Pipeline(
            lang=stanza_lang,
            use_gpu=True if torch.cuda.is_available() else False,
        )
    

    def _get_word_class(self, word: str, word_features: Dict[str, Any]) -> str:
        """
        Determine if a word is a content word or function word.
        Returns 'content' or 'function'.
        """
        # Try exact match first, then lowercase match
        features = word_features.get(word) or word_features.get(word.lower())
        if features is None:
            # Fallback: if word not found in features, assume content
            return "content"
        
        pos_tag = features.get('pos_tag')
        if pos_tag and pos_tag in self._function_pos_tags:
            return "function"
        return "content"

    def _is_word_lemma(self, word: str, word_features: Dict[str, Any]) -> bool:
        """
        Check if a word is already in its lemma (base) form.
        Returns True if the word is a lemma, False otherwise.
        """
        # Try exact match first, then lowercase match
        features = word_features.get(word) or word_features.get(word.lower())
        if features is None:
            # Fallback: if word not found, assume it's not a lemma
            return False
        
        lemma = features.get('lemma')
        if lemma is None:
            return False
        
        return word.lower() == lemma.lower()

    def _translate_this_word(self, word: str, word_features: Dict[str, Any]) -> bool:
        '''Should we translate this word?'''
        word_class_check = False
        lemma_check = False
        if self.word_class == "all":
            word_class_check = True
        elif self.word_class == "content":
            word_class_check = self._get_word_class(word, word_features) == "content"
        elif self.word_class == "function":
            word_class_check = self._get_word_class(word, word_features) == "function"
        
        if self.lemmas_only:
            lemma_check = self._is_word_lemma(word, word_features)
        else:
            lemma_check = True
        
        if self.nes_only:
            ne_check = word_features.get(word, {}).get('ne_label', None) is not None
            # We don't want to translate anything other than NEs
        else:
            ne_check = True
            
        return word_class_check and lemma_check and ne_check

    def _collect_word_features(self, input: str) -> Dict[str, Any]:
        '''
        Collect word features from Stanza for each word in the input.
        '''

        word_list = []
        word_features = {}
        if self._stanza_nlp is not None:
            doc = self._stanza_nlp(input)
            # Create a dictionary mapping word text to its features
            for sentence in doc.sentences:
                for word_obj in sentence.words:
                    # print(f"word_obj: {word_obj.text}")
                    word_text = word_obj.text
                    word_list.append(word_text)

                    ne_label = None
                    for token in sentence.tokens:
                        if word_obj in token.words:
                            if token.ner != "O":
                                ne_label = token.ner
                                break

                    features = {
                        'pos_tag': word_obj.upos,
                        'lemma': word_obj.lemma.lower() if word_obj.lemma else "-",
                        'word_features': word_obj.feats if word_obj.feats else "-",
                        'ne_label': ne_label
                    }

                    if self.use_lemmatizer and features['lemma'] != word_text.lower() and features['lemma'] != "-" and features['ne_label'] is None: # Also add the lemma to the word list
                        word_list.append(features['lemma'])

                    if word_text not in word_features:
                        word_features[word_text] = features

        
        if self._stanza_nlp is None: # Let's use space split tokenization if Stanza is not available
            word_list = tokenize_text(input, self.language, fast=True)

        return word_list, word_features


    def _cipher_word_features(self, word_list: List[str], word_features: Dict[str, Any], cipher = False) -> Dict[str, Any]:
        '''
        Cipher word features if cipher is True
        '''
        encode_source = cipher == True and self.direction == "comprehension" # Whether to encode the source word
        if encode_source:
            for word in word_list:
                features = word_features.get(word, None)
                if features is not None:
                    encoded_word = self.cipher_obj.encode(word)
                    word_features[encoded_word] = {
                        'pos_tag': features['pos_tag'],
                        'lemma': self.cipher_obj.encode(features['lemma']),
                        'word_features': features['word_features'],
                        'ne_label': features['ne_label']
                    }

            for word in word_list:
                if word in word_features:
                    del word_features[word]

        return word_features

    def _build_icl_word_maps(self, input, word_list: List[str], word_features: Dict[str, Any], cipher = False) -> List[Dict[str, Any]]:
        '''
        Build ICL word info dictionary. Each word may contain several related entries from dictionary.
        cipher: Whether to apply cipher
        '''
        icl_word_maps = []

        encode_source = cipher == True and self.direction == "comprehension" # Whether to encode the source word
        encode_target = cipher == True and self.direction == "generation" # Whether to encode the target word

        # We're having the issue that stanza tokenization splits up words (esp in Marathi)
        # making google translate not usable. While using Panlex we need the word feats since we need to know the NER tag.
        # Further, we need word feats when we have constraints of which words to translate.
        # But we don't need this in the following simple case, where we use a simpler word list.

        word_feats_check_not_required = self.lemmas_only == False and self.word_class == "all" and self.nes_only == False
        # This simulates the "ideal lexicon" case, where we can directly translate words in running text.
        if self.lexicon == "gtrans" and word_feats_check_not_required:
            word_list = tokenize_text(input, self.language, fast=True)
            for word in word_list:
                sources, translations = self.lexicon_obj.fuzzy_match_translations(word)
                for source, translation in zip(sources, translations):
                    if all(translation is None for translation in translations):
                        continue
                    source = self.cipher_obj.encode(source) if encode_source else source
                    translation = self.cipher_obj.encode(translation) if encode_target else translation                    
                    icl_word_maps.append((source, translation))
        
            return icl_word_maps


        for word in word_list:
            # print(f"word: {word}")
            # print(f"word_features: {word_features}")
            # print(f"self.word_class: {self.word_class}")
            # print(f"self.lemmas_only: {self.lemmas_only}")
            # print(f"self.nes_only: {self.nes_only}")
            if self._translate_this_word(word, word_features): # Should we translate this word (acc to lemma / pos checks)? And is it in our lexicon?
                # print(f"Translating word: {word}")
                # For NE's, we keep the original word as the translation
                if word in word_features and word_features[word].get('ne_label', None) is not None:
                    if not self.language.endswith("Latn"):
                        translation = self.google_translator.translate(word) # For NEs and languages not in Latin script, we use Google Translate, which just transliterates the word to the target language script
                    else:
                        translation = word # For Latin script languages, we use the original word as the translation
                    sources, translations = [word], [translation]
                else:
                    sources, translations = self.lexicon_obj.fuzzy_match_translations(word)

                for source, translation in zip(sources, translations):
                    if all(translation is None for translation in translations):
                        continue
                    source = self.cipher_obj.encode(source) if encode_source else source
                    translation = self.cipher_obj.encode(translation) if encode_target else translation                    
                    icl_word_maps.append((source, translation))

        return icl_word_maps

    def _get_exemplars(self, input: str, k = 3, cipher = False) -> List[Dict[str, Any]]:
        '''
        Get exemplars from the dev data for the given input using BM25 similarity with the input.
        '''
        if self.num_exemplars == 0:
            return None

        query_tokens = tokenize_text(input, self.language, fast=True)
        
        scores = self.bm25.get_scores(query_tokens)
        exemplars_i = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        exemplars = [(self.dev_data[0][i], self.dev_data[1][i]) for i in exemplars_i]

        encode_source = cipher == True and self.direction == "comprehension" # Whether to encode the source 
        encode_target = cipher == True and self.direction == "generation" # Whether to encode the target
        if encode_source:
            if self.task.startswith("xnli"):
                exemplars = [(self.cipher_obj.encode_segments(source, open_segment_token="<", close_segment_token=">"), target) for source, target in exemplars]
            else:    
                exemplars = [(self.cipher_obj.encode(source), target) for source, target in exemplars]
        if encode_target:
            exemplars = [(source, self.cipher_obj.encode(target)) for source, target in exemplars]

        if self.cascade_related_language:
            exemplars = [(self.related_language_translator.translate(source), target) for source, target in exemplars] # We're always doing generation

        return exemplars

    def _build_task_string(self, input, cipher = False):
        if self.task.startswith("mt"):
            if self.direction == "comprehension":
                if cipher == True:
                    assert self.cipher_obj.decode(self.cipher_obj.encode(input)) == input, "Cipher decode does not match input"
                    input = self.cipher_obj.encode(input)
                task_string = f"Translate the following text from {self.ciphered_name} to {self.pivot_language_name}. Respond only with the translation. \Input:\n{input}\n\n"
            else:
                task_string = f"Translate the following text from {self.pivot_language_name} to {self.ciphered_name}. Respond only with the translation. \nInput:\n{input}\n\n"
        elif self.task.startswith("mcq"):
            if self.direction == "comprehension":
                if cipher == True:
                    assert self.cipher_obj.decode(self.cipher_obj.encode(input)) == input, "Cipher decode does not match input"
                    input = self.cipher_obj.encode(input)
                task_string = f"Answer the following multiple-choice question in {self.ciphered_name}. Respond only with the numeric label of the correct option. \nInput:\n{input}\n\n"
        elif self.task.startswith("xnli"):
            if self.direction == "comprehension":
                if cipher == True:
                    assert self.cipher_obj.decode(self.cipher_obj.encode(input)) == input, "Cipher decode does not match input"
                    input = self.cipher_obj.encode_segments(input, open_segment_token="<", close_segment_token=">")
                task_string = f"You are given a premise and a hypothesis written in {self.ciphered_name}. Determine whether the hypothesis is entailed by, contradicted by, or neutral with respect to the premise. For entailment return '0'; for neutral return '1'; for contradiction return '2'. Respond only with the numeric label of the correct option.\nInput:\n{input}\n\n"
        elif self.task.startswith("xstorycloze"):
            if self.direction == "comprehension":
                if cipher == True:
                    assert self.cipher_obj.decode(self.cipher_obj.encode(input)) == input, "Cipher decode does not match input"
                    input = self.cipher_obj.encode(input)
                task_string = f"You are given a story, followed by two possible continuations, written in {self.ciphered_name}. Choose the continuation that best fits the prior context. Respond only with the numeric label of the correct option. \nInput:\n{input}\n\n"
        else:
            raise ValueError(f"Task {self.task} not supported")
        return task_string, input


    def _get_inflection_paradigms_description(self, cipher = False) -> str:
        '''
        Get inflection paradigms description for the language.
        '''
        inflection_paradigms_description = INFLECTION_PARADIGMS_DESCRIPTIONS[self.language]
        if cipher == True:
            inflection_paradigms_description = self.cipher_obj.encode_segments(inflection_paradigms_description, open_segment_token="<", close_segment_token=">")
        return inflection_paradigms_description

    def build_prompt(self, input, cipher = False) -> str:
        '''
        Build prompt. Format: 
        Language intro, task intro with input, exemplars, word meanings, word features, syntax description, repeat input.
        '''
        context_string = ""
        if cipher == True:
            context_string += f"{self.ciphered_lang_info} \n\n"

        og_input = input
        if self.cascade_related_language:    
            assert self.direction == "generation", "Cascade related language is only supported for generation tasks"
            input = self.related_language_translator.translate(input)

        # Task intro with input
        task_string, encoded_input = self._build_task_string(input, cipher) # input is encoded if cipher is True and direction is comprehension
        context_string += task_string

        # Exemplars
        if self.num_exemplars > 0:
            exemplars = self._get_exemplars(og_input, k=self.num_exemplars, cipher=cipher) # We use og input to find examples (in case of cascade related language, we use the og English, not the cascaded language input)
            formatted_exemplars = "\n".join([f"Input:\n{source}\nOutput:\n{target}\n\n" for source, target in exemplars])
            context_string += f"Here are some examples of inputs and outputs: \n{formatted_exemplars} \n\n"

        # Add lexicon information for each word
        if self.lexicon is not None or self.nes_only:
            word_list, word_features = self._collect_word_features(input)
            # Get lexicon entries for each word in the input
            icl_word_maps = self._build_icl_word_maps(input, word_list, word_features, cipher)
            formatted_word_meanings = "\n".join([f"{word} - {translation}" for word, translation in icl_word_maps])
            if len(icl_word_maps) > 0:
                context_string += f"Here are some word meanings for words in the input text. Note that these may not be correctly inflected. Also note that there may be multiple translations for a word, in which case you should choose the most relevant one.\n{formatted_word_meanings}\n\n"

        if self.add_word_features:
            assert self.lexicon is not None, "Word features are only available if lexicon is provided"
            word_features = self._cipher_word_features(word_list, word_features, cipher)
            formatted_info = "\n".join([f"{word}: POS: {wm['pos_tag']}, Lemma: {wm['lemma']}, Features: {wm['word_features']}" for word, wm in word_features.items()])
            if len(word_features) > 0:
                context_string += f"Here is POS, lemma, and grammatical feature information for words in the input text:\n{formatted_info} \n\n"

        if self.add_inflection_paradigms:
            inflection_paradigms_description = self._get_inflection_paradigms_description(cipher)
            context_string += f"Here is information on how to inflect verbs in {self.ciphered_name}:\n{inflection_paradigms_description} \n\n"

        if self.add_syntax_description:
            syntax_description = SYNTAX_DESCRIPTIONS[self.language]
            if not syntax_description:
                raise ValueError(f"Syntax description not found for language {self.language}")
            context_string += f"Here is a general description of the syntax of the language {self.ciphered_name}:\n{syntax_description} \n\n"

        if self.add_related_language_translation:
            related_language_translation = self.related_language_translator.translate(input)
            context_string += f"Here is the translation of the input text in {self.related_language_name}, which is a related language to {self.ciphered_name}, sharing syntax but not vocabulary. Use this translation to guide the word order of your output. \n{related_language_translation} \n\n"
        
        if cipher == False:
            context_string = context_string.replace(LANGS[self.language]["ciphered_name"], LANGS[self.language]["name"])

        
        if self.num_exemplars > 0 or self.lexicon is not None or self.nes_only or self.add_word_features or self.add_syntax_description or self.add_inflection_paradigms or self.add_related_language_translation: # Repeat input in case we have additional information to consider
            context_string += f"Consider all the information provided above. Respond with *only* the output. \nInput:\n{encoded_input}"
        

        context_string += f"\nOutput:\n"
        return context_string

    
    

class LexiconBuilder:
    def __init__(self, language: str, pivot_language: str, direction: str):
        self.language = language
        self.pivot_language = pivot_language
        self.direction = direction
        self.lexicon = self._get_lexicon()
        self.lexicon_source_words = self.lexicon.keys()
    
    def _get_lexicon(self):
        pass
    
    def translate(self, word):
        pass

class LexiconBuilderPanlex(LexiconBuilder):

    def __init__(self, language: str, pivot_language: str, direction: str):
        super().__init__(language, pivot_language, direction)
        if pivot_language != "eng_Latn":
            raise ValueError(f"Pivot language for Panlex lexicon builder must be English")

    def _get_lexicon(self):
        lang_key = LANGS[self.language]["iso3_code"]
        if self.direction == "comprehension":
            code = f"{lang_key}_eng"
        else:
            code = f"eng_{lang_key}"
        
        print(f"Loading lexicon for {code}...")
        lexicon = load_dataset("ec5ug/chikhapo", code)["train"]
        lexicon = {entry["source_word"]: entry["target_translations"][:5] for entry in lexicon}
        
        return lexicon

    def translate(self, word):
        translations = self.lexicon.get(word, None)
        # Return at most 5 translations
        translations = translations[:2]
        return ",".join(translations) if translations is not None else None

    def fuzzy_match(self, word, k=2):
        '''For a word, find k most similar translations in the lexicon'''
        matches = process.extract(word, self.lexicon_source_words, scorer=Levenshtein.distance, limit=k) # returns (match, score, index)
        return [match[0] for match in matches]

    def fuzzy_match_translations(self, word, k=2) -> Tuple[List[str], List[str]]:
        '''For a word, find k most similar translations in the lexicon'''
        word = word.lower()
        if word in self.lexicon_source_words: # If the word is in the lexicon, we can use the exact translation, else we need to fuzzy match
            sources = [word]
        else:
            sources = self.fuzzy_match(word, k)
        translations = [self.translate(source) for source in sources]
        return sources, translations

class LexiconBuilderGTrans(LexiconBuilder):
    '''
    This class is for building a prompt that contains the translation of all relevant words in the input.
    All language parameters are expected as NLLB style codes.
    '''
    def __init__(self, language: str, pivot_language: str, direction: str):
        self.gtrans_code = LANGS[language]["gtrans_code"]
        self.pivot_gtrans_code = LANGS[pivot_language]["gtrans_code"]

        if direction == "comprehension":
            self.src = self.gtrans_code     # from foreign language
            self.dest = self.pivot_gtrans_code # to English / other pivot language
        else:
            self.src = self.pivot_gtrans_code # from English
            self.dest = self.gtrans_code    # to target language / other pivot language

        datadir = os.environ.get("DATADIR")
        if not datadir:
            raise EnvironmentError("DATADIR environment variable is required for LexiconBuilderGTrans cache.")
        self.cache_dir = Path(datadir) / "gtrans_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.cache_dir / "gtrans_cache.sqlite3"
        self._db_lock = Lock()
        self._translate_lock = Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._initialize_db()

        super().__init__(language, pivot_language, direction)
        from googletrans import Translator
        
        self.translator = Translator()

        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

    def _get_lexicon(self):
        with self._db_lock:
            cursor = self._conn.execute(
                """
                SELECT word, translation 
                FROM translations
                WHERE language = ? AND pivot_language = ? AND direction = ? AND src = ? AND dest = ?
                """,
                (self.language, self.pivot_language, self.direction, self.src, self.dest),
            )
            rows = cursor.fetchall()
        return {word: translation for word, translation in rows}

    def _initialize_db(self):
        with self._db_lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS translations (
                    language TEXT NOT NULL,
                    pivot_language TEXT NOT NULL,
                    direction TEXT NOT NULL,
                    src TEXT NOT NULL,
                    dest TEXT NOT NULL,
                    word TEXT NOT NULL,
                    translation TEXT NOT NULL,
                    PRIMARY KEY (language, pivot_language, direction, src, dest, word)
                )
                """
            )
            self._conn.commit()

    def _persist_translation(self, word: str, translation: str):
        if translation is None:
            return
        with self._db_lock:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO translations (
                    language, pivot_language, direction, src, dest, word, translation
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (self.language, self.pivot_language, self.direction, self.src, self.dest, word, translation),
            )
            self._conn.commit()

    async def _translate_async(self, word: str) -> str:
        # IMPORTANT: await first, then access .text
        result = await self.translator.translate(word, src=self.src, dest=self.dest)
        return result.text

    def translate(self, word: str) -> str:
        # Public, synchronous method
        if word in self.lexicon:
            return self.lexicon[word]

        with self._translate_lock:
            if word in self.lexicon:
                return self.lexicon[word]

            try:
                translation = self._loop.run_until_complete(self._translate_async(word))
                if word.islower() and isinstance(translation, str):
                    translation = translation.lower()
                self.lexicon[word] = translation
                self._persist_translation(word, translation)
            except Exception as e:
                print(f"Error translating {word}: {e}")
                return None
            return translation

    def close(self):
        with self._db_lock:
            if getattr(self, "_conn", None):
                self._conn.close()
                self._conn = None

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass


    def fuzzy_match_translations(self, word: str, k: int = 2) -> Tuple[List[str], List[str]]:
        # Same as translate, but we return the source words and translations
        word = word.lower()
        sources = [word]
        translations = [self.translate(source) for source in sources]
        return sources, translations




factory_map = {
        "lexicon": BuildPromptLexicon,
    }


def get_prompt_builder(
    task: str,
    language: str,
    cipher_obj: Cipher,
    direction: str,
    **kwargs):
    '''
    It should return a BuildPrompt object.
    '''
    
    prompt_key = kwargs.get("prompt_key", None)
    if prompt_key not in factory_map:
        raise ValueError(f"Invalid prompt builder key: {prompt_key}")
    return factory_map[prompt_key](task=task, language=language, cipher_obj=cipher_obj, direction=direction, **kwargs)

