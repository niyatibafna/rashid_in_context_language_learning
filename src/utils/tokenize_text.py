from typing import List
import stanza
import re

def tokenize_text(text: str, lang: str, fast=False) -> List[str]:
    '''
    Tokenize text using space-splitting for most languages.
    For Korean, use a regex to tokenize on spaces.
    For Chinese and Japanese, use a list of characters.
    '''
    def _tokenize_ko_space(text): 
        return re.findall(r'[가-힣]+|[a-zA-Z0-9]+', text)

    if fast:        
        if lang == "kor_Hang":
            return _tokenize_ko_space(text)
        elif lang in ["cmn_Hans", "jpn_Jpan"]:
            return [char for char in text]
        else:
            return text.split()
    else:
        return stanza.Pipeline(lang, processors='tokenize').process(text).sentences[0].words