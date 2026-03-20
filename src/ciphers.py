import random
import string
from abc import ABC, abstractmethod
from pypinyin import pinyin, Style
import re
from .utils import ara_constants as ara

class Cipher(ABC):
    def __init__(self, language, seed=42):
        self.language = language
        self.seed = seed

    @abstractmethod
    def encode(self, text):
        pass
    
    @abstractmethod
    def decode(self, text):
        pass

    def round_trip_check(self, text):
        encoded = self.encode(text)
        decoded = self.decode(encoded)
        if decoded != text:
            print(f"Round-trip check failed for {text}")
            print(f"Text: {text}")
            print(f"Encoded: {encoded}")
            print(f"Decoded: {decoded}")
            print()
            return False
        return True
    

class CVCipher(Cipher):
    def __init__(self, language, seed=42):
        super().__init__(language, seed)
        self.language = language
        self.classes = self.get_classes(language)
        self.encode_map, self.decode_map = self.create_cipher_maps()

    def get_classes(self, language):
        # Use Unicode ranges or predefined sets for different languages
        classes = []
        if language == 'eng_Latn':
            vowels = 'aeiou'
            consonants = 'bcdfghjklmnpqrstvwxyz'
            classes = [vowels, consonants]
        elif language in {'hin_Deva', 'mar_Deva'}:
            # vowels = 'अआइईउऊएऐओऔािीुूेैोौ'
            dependent_vowels = 'ािीुूेैोौ'
            independent_vowels = 'अआइईउऊएऐओऔ'
            consonants = 'कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसहळ'
            classes = [dependent_vowels, independent_vowels, consonants]
        elif language == "tam_Taml":
            independent_vowels = 'அஆஇஈஉஊஎஏஒஓஔ'
            dependent_vowels = 'ாிீுூெேொோௌ'
            consonants = 'கஙசஞடணதநபமயரலவழளறஹஜஷஸ'
            classes = [independent_vowels, dependent_vowels, consonants]
        elif language == "arb_Arab": 
            vowels = ara.VOWELS 
            consonants = ara.CONSONANTS
            classes = [vowels, consonants]
        elif language == 'spa_Latn':
            vowels = 'aeiouáéíóúü'
            consonants = 'bcdfghjklmnñpqrstvwxyz'
            classes = [vowels, consonants]

        elif language == "tur_Latn":
            vowels = "aeioöuü" # dotless i not included due to weird unicode capitalization issues
            consonants = "bcçdfgğhjklmnpqrsştvyz"
            classes = [vowels, consonants]


        elif language == 'fra_Latn':
            vowels = 'aeiouàâéèêîôù'
            consonants = 'bcdfghjklmnpqrstvwxyzç'
            classes = [vowels, consonants]

        elif language == 'deu_Latn':
            vowels = 'aeiouäöü'
            consonants = 'bcdfghjklmnpqrstvwxyz' # leaving out ß due to weird unicode capitalization issues
            classes = [vowels, consonants]

        elif language == "ind_Latn":  # Indonesian
            vowels = "aeiou"
            consonants = "".join(sorted(set(string.ascii_lowercase) - set(vowels)))
            classes = [vowels, consonants]

        elif language == "zsm_Latn":  # Malay
            vowels = "aeiou"
            consonants = "".join(sorted(set(string.ascii_lowercase) - set(vowels)))
            classes = [vowels, consonants]

        elif language == "swa_Latn":  # Swahili
            vowels = "aeiou"
            consonants = "".join(sorted(set(string.ascii_lowercase) - set(vowels)))
            classes = [vowels, consonants]

        elif language == "vie_Latn":
            vowels = "".join([
                "aăâeêioôơuưy",
                "áàảãạ",
                "ắằẳẵặ",
                "ấầẩẫậ",
                "éèẻẽẹ",
                "ếềểễệ",
                "íìỉĩị",
                "óòỏõọ",
                "ốồổỗộ",
                "ớờởỡợ",
                "úùủũụ",
                "ứừửữự",
                "ýỳỷỹỵ",
            ])
            consonants = "bcdfghjklmnpqrstvxzđ"
            classes = [vowels, consonants]


        # --- Telugu (already 3-category friendly) ---
        elif language == "tel_Telu":
            # Keeping it simple/consistent: independent vowels, dependent vowels, consonants
            independent_vowels = "అఆఇఈఉఊఎఏఐఒఓఔ"
            dependent_vowels = "ాిీుూెేైొోౌ"
            consonants = "కఖగఘఙచఛజఝఞటఠడఢణతథదధనపఫబభమయరలవశషసహళ"
            classes = [independent_vowels, dependent_vowels, consonants]

        elif language == "ces_Latn":  # Czech
            # Czech vowels (incl. long vowels and ů)
            vowels = "aeiouyáéíóúůýě"
            # Czech consonants (incl. diacritics)
            consonants = "bcčdďfghjklmnňpqrřsštťvwxzž"
            classes = [vowels, consonants]

        elif language == "pol_Latn":  # Polish
            # Polish vowels (incl. ą, ę, ó)
            vowels = "aeiouyąęó"
            # Polish consonants (incl. diacritics)
            consonants = "bcćdfghjklłmnńprsśtwzźżqvx"
            classes = [vowels, consonants]


        elif language == "kor_Hang":
            syllables = "".join(chr(c) for c in range(0xAC00, 0xD7A4))
            classes = [syllables]


        elif language == 'cmn_Hans':
            vowels = 'aeiou'
            consonants = 'bpmfdtnlgkhjqxzcsryw'
            classes = [vowels, consonants]
            # TODO: tones = '1234' 
        else:
            raise ValueError(f"Language {language} not supported")
        
        return classes

    def create_cipher_maps(self):
        rng = random.Random(self.seed)
        encode_map = {}
        decode_map = {}
        for class_ in self.classes:
            shuffled_class = list(class_)
            rng.shuffle(shuffled_class)
            for original, shuffled in zip(class_, shuffled_class):
                encode_map[original] = shuffled
                decode_map[shuffled] = original
        
        return encode_map, decode_map

    def encode(self, text):
        encoded_text = []
        if self.language == "cmn_Hans":
            text = self._preprocess_cmn_Hans(text)
        if self.language == "arb_Arab":
            text = self._preprocess_arb_Arab(text)
        # Encode while preserving case
        for char in text:
            if char.lower() in self.encode_map:
                encoded_text.append(self.encode_map[char.lower()] if char.islower() else self.encode_map[char.lower()].upper())
            else:
                encoded_text.append(char)
        
        if self.language == "arb_Arab":
            return self._postprocess_arb_Arab(''.join(encoded_text))
        
        return ''.join(encoded_text)

    def decode(self, text):
        decoded_text = []
        # Decode while preserving case
        # if self.language == "tam_Taml":
        #     text = self._preprocess_tam_Taml(text)
        if self.language == "arb_Arab":
            text = self._preprocess_arb_Arab(text)
        for char in text:
            if char.lower() in self.decode_map:
                decoded_text.append(self.decode_map[char.lower()] if char.islower() else self.decode_map[char.lower()].upper())
            else:
                decoded_text.append(char)
        # if self.language == "tam_Taml":
        #     return self._postprocess_tam_Taml(''.join(decoded_text))
        if self.language == "arb_Arab":
            return self._postprocess_arb_Arab(''.join(decoded_text))
        return ''.join(decoded_text)

    
    def _preprocess_cmn_Hans(self, text):
        text = pinyin(text, style=Style.TONE3)
        text = " ".join([pinyin_char for chinese_char in text for pinyin_char in chinese_char])
        return text

    def encode_segments(self, text, open_segment_token="<", close_segment_token=">"):
        
        encoded_text = ""
        encode_segment = False
        for char in text:
            if char == open_segment_token:
                encode_segment = True
            elif char == close_segment_token:
                encode_segment = False
            elif encode_segment:
                encoded_text += self.encode(char)
            else:
                encoded_text += char
        return encoded_text

    def decode_segments(self, text, open_segment_token="<", close_segment_token=">"):
        decoded_text = ""
        decode_segment = False
        for char in text:
            if char == open_segment_token:
                decode_segment = True
            elif char == close_segment_token:
                decode_segment = False
            elif decode_segment:
                decoded_text += self.decode(char)
            else:
                decoded_text += char
        return decoded_text
    
    # def _preprocess_tam_Taml(self, text):
    #     ## Convert dependent vowel signs to independent vowels
    #     dependent_to_independent = {
    #         'ா': 'ஆ',
    #         'ி': 'இ',
    #         'ீ': 'ஈ',
    #         'ு': 'உ',
    #         'ூ': 'ஊ',
    #         'ெ': 'எ',
    #         'ே': 'ஏ',
    #         'ொ': 'ஒ',
    #         'ோ': 'ஓ',
    #         'ௌ': 'ஔ',
    #         '்': 'ஃ'  # Virama, removes inherent vowel
    #     }

    #     for dep, indep in dependent_to_independent.items():
    #         text = text.replace(dep, indep)
       
    #     print("After dependent to independent conversion:", text)
    #     regex_pattern = f"([{self.consonants}])(?=[^{self.vowels + 'ஃ'}]|$)"
    #     text = re.sub(regex_pattern, r'\1அ', text)
    #     print("After adding implicit 'அ':", text)

    #     return text
    
    # def _postprocess_tam_Taml(self, text):
    #     ## Convert independent vowels back to dependent vowel signs
    #     independent_to_dependent = {
    #         'அ': '',
    #         'ஆ': 'ா',
    #         'இ': 'ி',
    #         'ஈ': 'ீ',
    #         'உ': 'ு',
    #         'ஊ': 'ூ',
    #         'எ': 'ெ',
    #         'ஏ': 'ே',
    #         'ஒ': 'ொ',
    #         'ஓ': 'ோ',
    #         'ஔ': 'ௌ',
    #         'ஃ': '்'  # Virama
    #     }
    #     for indep, dep in independent_to_dependent.items():
    #         text = " ".join([word[0] + word[1:].replace(indep, dep) for word in text.split(" ")])
        
    #     return text
    
    def _process_arb_Arab(self, text, map_):
        # See map in ara_constants.py
        for key, val in map_.items():
            text = text.replace(key, val)
        
        return text
    
    def _preprocess_arb_Arab(self, text):
        return self._process_arb_Arab(text=text, map_=ara.PREPROCESS_MAP)
    
    def _postprocess_arb_Arab(self, text):
        return self._process_arb_Arab(text=text, map_=ara.POSTPROCESS_MAP)

class HanziCipher(Cipher):
    def __init__(self, seed=42, k=4):
        super().__init__("cmn_Hans", seed)
        self.k = k
        self.hanzi_range = self._generate_hanzi_range()
        self.combinations = self._generate_combinations(k)
        self.encode_map, self.decode_map = self._create_maps()

    def _generate_hanzi_range(self):
        start = 0x4E00
        end = 0x9FFF
        return [chr(code) for code in range(start, end + 1)]

    def _generate_combinations(self, k):
        letters = string.ascii_lowercase
        tones = "1234"

        random.seed(self.seed)

        combos = set()
        total_needed = len(self.hanzi_range)

        while len(combos) < total_needed:
            prefix = ''.join(random.choice(letters) for _ in range(k - 1))
            tone = random.choice(tones)
            combos.add(prefix + tone)

        return list(combos)


    def _create_maps(self):
        random.seed(self.seed)
        hanzi = list(self.hanzi_range)
        combos = self.combinations.copy()

        random.shuffle(hanzi)
        random.shuffle(combos)

        size = min(len(hanzi), len(combos))
        hanzi = hanzi[:size]
        combos = combos[:size]

        encode_map = {h: c for h, c in zip(hanzi, combos)}
        decode_map = {c: h for h, c in zip(hanzi, combos)}

        return encode_map, decode_map

    def encode(self, text):
        encoded = []
        for ch in text:
            if ch in self.encode_map:
                encoded.append(self.encode_map[ch])
            else:
                encoded.append(ch)
        return " ".join(encoded)

    def decode(self, text):
        parts = text.split()
        decoded = []
        for token in parts:
            if token in self.decode_map:
                decoded.append(self.decode_map[token])
            else:
                decoded.append(token)
        return ''.join(decoded)


