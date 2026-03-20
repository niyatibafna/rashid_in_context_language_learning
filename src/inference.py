from typing import Optional, Dict, Any, List
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
import os
from abc import abstractmethod
from tqdm import tqdm

model_key_to_model_map = {
        "llama": "meta-llama/Llama-3.1-8B-Instruct",
        "qwen7b": "Qwen/Qwen2.5-7B-Instruct",
        "gpt-5.1": "gpt-5.1",
    }

def Inference(model_key: str, 
              device: Optional[str] = None, 
              model_kwargs: Optional[Dict[str, Any]] = None, 
              tokenizer_kwargs: Optional[Dict[str, Any]] = None, 
              api_key: Optional[str] = None, 
              base_url: Optional[str] = None, 
              ):
    '''
    Initialize the inference model.
    model_key: str
    device: Optional[str] = None
    model_kwargs: Optional[Dict[str, Any]] = None
    tokenizer_kwargs: Optional[Dict[str, Any]] = None
    '''
    def _get_class_key(model_key: str) -> str:
        if model_key.startswith("gpt-"):
            return "openai"
        else:
            return "hf" 

    class_key = _get_class_key(model_key)
    
    model_name = model_key_to_model_map.get(model_key, model_key)
    
    if class_key == "openai":
        return InferenceOpenAI(model_key=model_name, api_key=api_key, base_url=base_url)
    elif class_key == "hf":
        return InferenceHF(model_key=model_name, device=device, model_kwargs=model_kwargs, tokenizer_kwargs=tokenizer_kwargs)
    else:
        raise ValueError(f"Invalid model key: {model_key}")

class InferenceHF:
    def __init__(
        self,
        model_key: str,
        device: Optional[str] = None,
        model_kwargs: Optional[Dict[str, Any]] = None,
        tokenizer_kwargs: Optional[Dict[str, Any]] = None,
    ):
        self.model_key = model_key
        self.model_kwargs = model_kwargs or {}
        self.device = device or ('cuda' if torch.cuda.is_available() else 'cpu')
        self.tokenizer_kwargs = tokenizer_kwargs or {}

        # ---- Load tokenizer ----
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_key,
            **self.tokenizer_kwargs,
        )

        # Llama-style: pad with EOS and use LEFT padding
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        self.tokenizer.padding_side = "left"

        # ---- Load model ----
        self.model = AutoModelForCausalLM.from_pretrained(
            self.model_key,
            torch_dtype=torch.float16,
            **self.model_kwargs,
        )
        self.model.to(self.device)
        self.model.eval()

    def _tokenize(self, texts: List[str]):
        """Tokenize and move to device."""
        encoded = self.tokenizer(
            texts,
            return_tensors="pt",
            padding=True,
            truncation=True,
        )
        encoded = {k: v.to(self.device) for k, v in encoded.items()}
        return encoded

    def _generate(
        self,
        texts: List[str],
        max_new_tokens: int = 128,
        temperature: float = 1.0,
        top_p: float = 1.0,
        top_k: int = 50,
        do_sample: bool = False,
    ) -> List[str]:
        """
        Basic text generation from raw prompts.
        `texts` should already be the full prompt strings (including chat templates if any).
        """
        inputs = self._tokenize(texts)

        # Length of the (padded) prompt in tokens
        prompt_lens = inputs["input_ids"].shape[1]

        gen_kwargs = dict(
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            do_sample=do_sample,
            pad_token_id=self.tokenizer.pad_token_id,
            eos_token_id=self.tokenizer.eos_token_id,
        )

        with torch.no_grad():
            output_ids = self.model.generate(
                **inputs,
                **gen_kwargs,
            )

        # Drop the prompt part for all batch items
        generated_ids = output_ids[:, prompt_lens:]

        # Decode only the new tokens
        outputs = self.tokenizer.batch_decode(
            generated_ids, skip_special_tokens=True
        )
        return [o.strip() for o in outputs]

    def generate(
        self,
        texts: List[str],
        batch_size: int = 1,
        max_new_tokens: int = 128,
        temperature: float = 1.0,
        **kwargs,
    ) -> List[str]:
        """
        Chat-style inference for chat models (e.g. Llama 3.1 Instruct).
        `texts` is a list of plain user messages.
        """
        if hasattr(self.tokenizer, "apply_chat_template"):
            prompts = [
                self.tokenizer.apply_chat_template(
                    [{"role": "user", "content": text}],
                    tokenize=False,
                    add_generation_prompt=True,
                )
                for text in texts
            ]
        else:
            # Simple fallback if no chat template is available
            prompts = [f"User: {text}\nAssistant:" for text in texts]

        generated_texts = []
        for i in tqdm(range(0, len(prompts), batch_size), desc="Generating texts"):
            generated_texts.extend(self._generate(
                prompts[i:i+batch_size],
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                **kwargs,
            ))
        return generated_texts
    


class InferenceOpenAI:
    def __init__(
        self,
        model_key: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Initialize OpenAI API client for inference.
        
        Args:
            model_key: OpenAI model name (e.g., "gpt-4", "gpt-3.5-turbo", "gpt-4o")
            api_key: OpenAI API key. If None, will try to use OPENAI_API_KEY env var.
            base_url: Optional base URL for API (useful for OpenAI-compatible APIs)
        """
        
        self.model_key = model_key
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("No API key provided and OPENAI_API_KEY env var is not set.")

        client_kwargs = {"api_key": self.api_key}
        if base_url:
            client_kwargs["base_url"] = base_url

        self.client = OpenAI(**client_kwargs)

        # We are only using chat models for now
        self.is_chat_model = True

    def _generate_one(
        self,
        text: str,
        max_new_tokens: int,
        temperature: float,
        top_p: float,
        do_sample: bool,
        **kwargs,
    ) -> str:
        """Generate text for a single prompt."""
        temp = temperature if do_sample else 0.0
        top_p_val = top_p if do_sample else 1.0

        if self.is_chat_model:
            resp = self.client.chat.completions.create(
                model=self.model_key,
                messages=[{"role": "user", "content": text}],
                max_completion_tokens=max_new_tokens,
                temperature=temp,
                top_p=top_p_val,
                **kwargs,
            )
            out = resp.choices[0].message.content
        else:
            resp = self.client.completions.create(
                model=self.model_key,
                prompt=text,
                max_completion_tokens=max_new_tokens,
                temperature=temp,
                top_p=top_p_val,
                **kwargs,
            )
            out = resp.choices[0].text

        return out.strip() if out else ""

    def generate(
        self,
        texts: List[str],
        max_new_tokens: int = 512,
        temperature: float = 1.0,
        top_p: float = 1.0,
        do_sample: bool = True,
        batch_size: Optional[int] = None,
        **kwargs,
    ) -> List[str]:
        """
        Generate outputs for a list of input strings.

        Args:
            texts: List of plain user messages or prompts.
            max_new_tokens: Maximum number of tokens to generate.
            temperature: Sampling temperature.
            top_p: Nucleus sampling parameter.
            do_sample: If False, use greedy / deterministic decoding (temperature=0, top_p=1).
            batch_size: Number of parallel requests (None or 1 = sequential).
            **kwargs: Extra args passed to OpenAI API.

        Returns:
            List of generated strings, same order as inputs.
        """
        if batch_size is None or batch_size <= 1 or len(texts) <= 1:
            # Simple sequential mode
            return [
                self._generate_one(
                    text,
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_p=top_p,
                    do_sample=do_sample,
                    **kwargs,
                )
                for text in texts
            ]

        # Batched / parallel mode
        results: List[Optional[str]] = [None] * len(texts)
        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            future_to_idx = {
                executor.submit(
                    self._generate_one,
                    text,
                    max_new_tokens,
                    temperature,
                    top_p,
                    do_sample,
                    **kwargs,
                ): idx
                for idx, text in enumerate(texts)
            }

            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    results[idx] = future.result()
                except Exception:
                    # If a request fails, return empty string for that item
                    results[idx] = ""

        # type: ignore is just to satisfy type checkers; logically everything is str now.
        return [r or "" for r in results]
