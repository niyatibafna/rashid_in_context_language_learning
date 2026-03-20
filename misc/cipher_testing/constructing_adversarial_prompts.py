from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Sequence, Tuple, Union

import json
import os
import sys

import sacrebleu

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))
from misc.results_collection.utils_results_extraction import load_ouputs_grid
from misc.results_collection.utils_string_analysis import parse_translation_prompt
from src.ciphers import CVCipher as Cipher
from src.inference import Inference

DECIPHER_ANALYSIS_ROOT = "misc/cipher_testing/decipher_analysis_output/no_lexicon"
KEY_DECIPHERED_INPUT = "deciphered input text"
KEY_ENGLISH_TRANSLATION = "english translation"



def build_prompt(input_text: str, lexicon_entries: List[str], icl_examples: Sequence[Tuple[str, str]]) -> str:
    """
    Build a prompt from exemplars plus the given input.

    Args:
        input_text: The final input string we want a model to translate/answer.
        icl_examples: Sequence of (input, output) example pairs.

    Returns:
        A single concatenated string containing all examples and the final input.
    """
    
    examples: List[str] = []

    for src, tgt in icl_examples:
        examples.append(f"Ciphered text: {src}\nTranslation: {tgt}")

    task_string = f"First decipher the input text, and then translate it to English: {input_text}. Here are some examples of the ciphered text and their translations:"
    
    task_string += "\n\n".join(examples)


    # task_string += f"Here are also the word meanings for each word in the input text: \n{lexicon_entries}"

    task_string += f'Using this information, first decipher the input text, and then translate it to English. Provide your guess for i. the underlying language, ii. the cipher method used, iii. the deciphered input text iv. English translation. \n\nUse the following JSON output format and make sure your output is a valid JSON object: {{"language": "<language>", "cipher method": "<cipher method>", "deciphered input text": "<deciphered input text>", "english translation": "<english translation>"}} \n\nInput text: {input_text}'

    return task_string.strip()


def load_language_outputs(
    language: str,
    exp_id: str,
    num_samples: int = 100,
    direction: str = "comprehension",
    *,
    base_path: Union[str, Path] | None = None,
    model_name: str = "gpt-5.1",
    prompt_set: str = "lang_info",
) -> List[dict]:
    """
    Load all comprehension outputs for a single language/exp_id using ``load_ouputs_grid``.

    Returns:
        A list of segment dicts (possibly empty if not found).
    """
    if base_path is None:
        homedir = os.environ.get("HOMEDIR", os.path.expanduser("~"))
        base_path = f"{homedir}/projects/llm_language_learning/outputs/lang_info_mtwmtpp"

    outputs_grid = load_ouputs_grid(
        languages=[language],
        num_samples=num_samples,
        exp_ids=[exp_id],
        direction=direction,
        base_path=base_path,
        model_name=model_name,
        prompt_set=prompt_set,
    )

    lang_grid = outputs_grid.get(language, {})
    segments = lang_grid.get(exp_id)
    return segments if isinstance(segments, list) else []


def build_concatenated_prompts_for_language(
    language: str,
    exp_id: str,
    num_samples: int = 100,
    direction: str = "comprehension",
    cipher_obj: Cipher = None,
    *,
    base_path: Union[str, Path] | None = None,
    model_name: str = "gpt-5.1",
    prompt_set: str = "lang_info",
) -> str:
    """
    For all comprehension segments for a given language/exp_id, parse exemplars from the
    original prompt and build new prompts that combine those exemplars with each segment's
    ``input``.

    This:
      1. Loads outputs via ``load_ouputs_grid``.
      2. For each segment, uses ``parse_translation_prompt(prompt_raw)`` to get exemplars.
      3. Sends the segment ``input`` and the exemplars to ``build_prompt``.
      4. Returns a single concatenated string over all segments.
    """
    segments = load_language_outputs(
        language=language,
        exp_id=exp_id,
        num_samples=100,
        direction=direction,
        base_path=base_path,
        model_name=model_name,
        prompt_set=prompt_set,
    )

    all_prompts: List[str] = []

    for seg in segments[:num_samples]:
        if not isinstance(seg, dict):
            continue

        input_text = seg.get("input")
        if cipher_obj is not None:
            input_text = cipher_obj.encode(input_text)
        prompt = seg.get("prompt")


        lexicon_entries, icl_examples, _ = parse_translation_prompt(prompt)
        icl_examples = icl_examples or []

        prompt_str = build_prompt(input_text, lexicon_entries, icl_examples)
        all_prompts.append(prompt_str)

        print(f"Prompt for input text: {input_text}")
        print(prompt_str)
        print(f"Reference: {seg.get('reference')}")

    return all_prompts

def get_llm_response(prompt: str) -> str:
    """
    Get a response from the LLM for a given prompt.
    """
    inference = Inference(model_key="gpt-5.1", api_key=os.getenv("OPENAI_API_KEY"))
    response = inference.generate([prompt], max_new_tokens=1024, batch_size=1)
    return response[0]


def _parse_llm_response(response: str) -> Dict[str, Any]:
    """Parse LLM JSON response; return dict of keys/values or {'raw_response': response} on failure."""
    try:
        parsed = json.loads(response)
        return dict(parsed) if isinstance(parsed, dict) else {"raw_response": response}
    except (json.JSONDecodeError, TypeError):
        return {"raw_response": response}


def eval_llm_responses(
    llm_responses: List[str],
    input_texts: List[str],
    reference_texts: List[str],
    language: str,
    prompts: List[str],
    *,
    output_dir: Union[str, Path] | None = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Evaluate LLM responses: dump per-item JSON (input, ref, all LLM keys), compute
    corpus-level chrf++ and BLEU for (i) deciphered vs original input and (ii) translation vs reference,
    and save both dumps under decipher_analysis_output/<lang>/.

    Args:
        llm_responses: List of raw LLM response strings (expected JSON with keys like
            'deciphered input text', 'english translation').
        input_texts: List of original (ground-truth) input text per segment (for decipher metric).
        reference_texts: List of reference English translations per segment.
        language: Language code (e.g. 'hin_Deva') used for the output subfolder.
        output_dir: Optional root directory; defaults to DECIPHER_ANALYSIS_ROOT in cwd.

    Returns:
        (output_records, eval_metrics) where output_records is the list of dicts with input, ref,
        and all keys from each LLM response, and eval_metrics is the dict of corpus scores and paths.
    """
    if output_dir is None:
        output_dir = Path(DECIPHER_ANALYSIS_ROOT)
    else:
        output_dir = Path(output_dir)
    lang_dir = output_dir / language
    lang_dir.mkdir(parents=True, exist_ok=True)

    n = min(len(llm_responses), len(input_texts), len(reference_texts))
    output_records: List[Dict[str, Any]] = []

    hypotheses_decipher: List[str] = []
    references_decipher: List[str] = []
    hypotheses_translation: List[str] = []
    references_translation: List[str] = []

    for i in range(n):
        inp = input_texts[i]
        ref = reference_texts[i]
        resp = llm_responses[i]
        parsed = _parse_llm_response(resp)

        record: Dict[str, Any] = {"input": inp, "ref": ref, "prompt": prompts[i], **parsed}
        output_records.append(record)

        deciphered = parsed.get(KEY_DECIPHERED_INPUT) or parsed.get("deciphered_input_text", "")
        translation = parsed.get(KEY_ENGLISH_TRANSLATION) or parsed.get("english_translation", "")

        if isinstance(deciphered, str) and isinstance(inp, str):
            hypotheses_decipher.append(deciphered)
            references_decipher.append(inp)
        if isinstance(translation, str) and isinstance(ref, str):
            hypotheses_translation.append(translation)
            references_translation.append(ref)

    # Corpus-level BLEU and chrF++ (decipher: LLM deciphered vs original input)
    if hypotheses_decipher and references_decipher:
        bleu_decipher = sacrebleu.corpus_bleu(hypotheses_decipher, [references_decipher])
        chrf_decipher = sacrebleu.corpus_chrf(hypotheses_decipher, [references_decipher])
    else:
        bleu_decipher = chrf_decipher = None

    # Corpus-level BLEU and chrF++ (translation: LLM translation vs reference)
    if hypotheses_translation and references_translation:
        bleu_translation = sacrebleu.corpus_bleu(hypotheses_translation, [references_translation])
        chrf_translation = sacrebleu.corpus_chrf(hypotheses_translation, [references_translation])
    else:
        bleu_translation = chrf_translation = None

    eval_metrics: Dict[str, Any] = {
        "decipher": {
            "bleu": bleu_decipher.score if bleu_decipher is not None else None,
            "chrf": chrf_decipher.score if chrf_decipher is not None else None,
        },
        "translation": {
            "bleu": bleu_translation.score if bleu_translation is not None else None,
            "chrf": chrf_translation.score if chrf_translation is not None else None,
        },
        "num_segments": n,
    }

    # Save output dump (list of dicts: input, ref, and all LLM keys)
    outputs_path = lang_dir / "outputs.json"
    with open(outputs_path, "w", encoding="utf-8") as f:
        json.dump(output_records, f, ensure_ascii=False, indent=2)

    # Save eval dump (corpus scores)
    eval_path = lang_dir / "eval.json"
    with open(eval_path, "w", encoding="utf-8") as f:
        json.dump(eval_metrics, f, ensure_ascii=False, indent=2)

    eval_metrics["outputs_path"] = str(outputs_path)
    eval_metrics["eval_path"] = str(eval_path)
    return output_records, eval_metrics


def run_pipeline(
    language: str,
    num_samples: int,
    *,
    exp_id: str = "E4",
    direction: str = "comprehension",
    use_cipher: bool = True,
    base_path: Union[str, Path] | None = None,
    model_name: str = "gpt-5.1",
    prompt_set: str = "lang_info",
    output_dir: Union[str, Path] | None = None,
) -> Dict[str, Any]:
    """
    Run the full pipeline for a given language and number of samples:
    load segments → build prompts (optionally ciphered) → get LLM responses → evaluate and save.

    Args:
        language: Language code (e.g. 'hin_Deva').
        num_samples: Number of segments to process.
        exp_id: Experiment ID to load (default 'E4').
        direction: 'comprehension' or 'generation'.
        use_cipher: If True, encode segment input with CVCipher before building the prompt.
        base_path: Optional base path for outputs grid.
        model_name: Model key for loading segments and for inference.
        prompt_set: Prompt set for loading segments.
        output_dir: Root dir for decipher_analysis_output; default DECIPHER_ANALYSIS_ROOT.

    Returns:
        Eval metrics dict (including outputs_path, eval_path, decipher/translation scores).
    """
    cipher_obj = Cipher(language=language) if use_cipher else None
    segments = load_language_outputs(
        language=language,
        exp_id=exp_id,
        num_samples=100,
        direction=direction,
        base_path=base_path,
        model_name=model_name,
        prompt_set=prompt_set,
    )

    # print(f"Number of segments: {len(segments)}")
    # print(f"Segments: {segments[0]}")

    prompts: List[str] = []
    input_texts: List[str] = []   # original (unciphered) for decipher metric
    reference_texts: List[str] = []

    for seg in segments:
        if not isinstance(seg, dict):
            continue
        original_input = seg.get("input")
        ref = seg.get("reference")
        prompt_raw = seg.get("prompt") or seg.get("prompt_raw")
        if not isinstance(original_input, str) or not isinstance(ref, str):
            continue
        if not isinstance(prompt_raw, str):
            continue

        lexicon_entries, icl_examples, _ = parse_translation_prompt(prompt_raw)
        icl_examples = icl_examples or []
        input_for_prompt = cipher_obj.encode(original_input) if cipher_obj else original_input
        prompt_str = build_prompt(input_for_prompt, lexicon_entries, icl_examples)

        prompts.append(prompt_str)
        input_texts.append(original_input)
        reference_texts.append(ref)

    if not prompts:
        return {"error": "no valid segments", "num_segments": 0}

    prompts = prompts[:num_samples]
    input_texts = input_texts[:num_samples]
    reference_texts = reference_texts[:num_samples]
    inference = Inference(model_key=model_name, api_key=os.getenv("OPENAI_API_KEY"))
    llm_responses = inference.generate(prompts, max_new_tokens=1024, batch_size=1)
    # llm_responses = [json.dumps({'language': 'Hindi', 'cipher method': 'CVCipher', 'deciphered input text': 'हिन्दी भाषा के लिए एक उदाहरण है', 'english translation': 'An example for the Hindi language'}) for _ in range(len(prompts))]

    _, eval_metrics = eval_llm_responses(
        llm_responses=llm_responses,
        input_texts=input_texts,
        reference_texts=reference_texts,
        prompts=prompts,
        language=language,
        output_dir=output_dir,
    )
    return eval_metrics


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run cipher decipher pipeline for a language.")
    parser.add_argument("--language", type=str, default="hin_Deva", help="Language code (e.g. hin_Deva)")
    parser.add_argument("--num_samples", type=int, default=5, help="Number of segments to run")
    parser.add_argument("--exp_id", type=str, default="E4", help="Experiment ID to load")
    parser.add_argument("--no_cipher", action="store_true", help="Do not apply cipher to input")
    parser.add_argument("--output_dir", type=str, default=None, help="Output root (default: decipher_analysis_output)")
    args = parser.parse_args()

    metrics = run_pipeline(
        language=args.language,
        num_samples=args.num_samples,
        exp_id=args.exp_id,
        use_cipher=not args.no_cipher,
        output_dir=args.output_dir,
    )
    print(json.dumps(metrics, indent=2))



