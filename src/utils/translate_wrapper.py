from .lang_codes import LANGS
import asyncio
import os

class GoogleTranslateWrapper:
    def __init__(self, src_language: str, dest_language: str):
        from googletrans import Translator
        self.src_language = LANGS[src_language]["gtrans_code"]
        self.dest_language = LANGS[dest_language]["gtrans_code"]
        self.translator = Translator()
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

    async def _translate_async(self, text: str) -> str:
        result = await self.translator.translate(text, src=self.src_language, dest=self.dest_language)
        return result

    def translate(self, text: str) -> str:
        result = self._loop.run_until_complete(self._translate_async(text))
        return result.text

class LLMTranslateWrapper:

    def __init__(self, src_language: str, dest_language: str):
        from src.inference import Inference
        self.inference = Inference(
            model_key="gpt-5.1",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        self.src_language = LANGS[src_language]["name"]
        self.dest_language = LANGS[dest_language]["name"]

    def translate(self, text: str) -> str:
        prompt = f"Translate the following text from {self.src_language} to {self.dest_language}. Respond with *only* the output. \nInput:\n{text}\nOutput:\n"
        response = self.inference.generate([prompt], max_new_tokens=512)
        return response[0]