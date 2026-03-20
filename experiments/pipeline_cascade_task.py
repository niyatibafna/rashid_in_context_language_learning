import json
import os
import sys
from pathlib import Path

import fire

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.build_prompt import get_prompt_builder
from src.ciphers import CVCipher, HanziCipher
from src.evaluation import EvaluationAccuracy
from src.inference import Inference
from src.task_data import TaskData


SUPPORTED_TASKS = {"mcqmmluprox", "xnli", "xstorycloze"}


def _build_cipher(language: str):
    if language == "cmn_hans":
        return HanziCipher(seed=42)
    return CVCipher(language=language, seed=42)


def _load_prompt_builder_config(config_file: str, config_id: str):
    with open(config_file, "r", encoding="utf-8") as f:
        cfgs = json.load(f)
    return cfgs[config_id]


def _task_inputs(task_name: str, examples):
    if task_name in {"mcqmmluprox", "xstorycloze"}:
        return [ex["input"] for ex in examples]
    if task_name == "xnli":
        return [
            f"Premise: {ex['metadata']['premise']}\nHypothesis: {ex['metadata']['hypothesis']}"
            for ex in examples
        ]
    raise ValueError(f"Unsupported task: {task_name}")


def _build_second_stage_prompts(task_name: str, prompt_builder, task_use_cipher: bool, english_inputs):
    prompts = []
    for inp in english_inputs:
        base_prompt = prompt_builder.build_prompt(inp, cipher=task_use_cipher)
        if task_name == "xnli":
            base_prompt = base_prompt.replace("\nOutput:\n", "") + f"\nInput:\n{inp}\nOutput:\n"
        elif "Input:" not in base_prompt:
            base_prompt = base_prompt.replace("\nOutput:\n", "") + f"\nInput:\n{inp}\n\nOutput:\n"
        prompts.append(base_prompt)
    return prompts


def main(
    src_language: str,
    task_name: str,
    num_examples: int,
    batch_size: int,
    model_key: str,
    mt_prompt_builder_config_file: str,
    mt_prompt_builder_config_id: str,
    mt_use_cipher: bool,
    mt_max_new_tokens: int,
    task_prompt_builder_config_file: str,
    task_prompt_builder_config_id: str,
    task_use_cipher: bool,
    task_max_new_tokens: int,
    output_file: str,
    results_dir: str,
):
    if task_name not in SUPPORTED_TASKS:
        raise ValueError(f"Unsupported task_name: {task_name}. Expected one of {sorted(SUPPORTED_TASKS)}")

    Path(results_dir).mkdir(parents=True, exist_ok=True)

    print(f"Loading {task_name} data...")
    task_data = TaskData(task_name=task_name, language=src_language)
    examples = task_data.load_data_method(
        direction="comprehension",
        split="dev",
        num_examples=num_examples,
    )

    print("Initializing inference model...")
    inference = Inference(
        model_key=model_key,
        api_key=os.getenv("OPENAI_API_KEY"),
    )

    print("Creating MT prompt builder...")
    mt_cipher = _build_cipher(src_language)
    mt_cfg = _load_prompt_builder_config(mt_prompt_builder_config_file, mt_prompt_builder_config_id)
    mt_prompt_builder = get_prompt_builder(
        task="mtfloresplus",
        language=src_language,
        cipher_obj=mt_cipher,
        direction="comprehension",
        **mt_cfg,
    )

    input_src = _task_inputs(task_name, examples)

    print("Building MT prompts...")
    mt_prompts = [mt_prompt_builder.build_prompt(inp, cipher=mt_use_cipher) for inp in input_src]

    print("Running MT inference...")
    mt_outputs_raw = inference.generate(
        mt_prompts,
        max_new_tokens=mt_max_new_tokens,
        batch_size=batch_size,
    )
    mt_outputs = mt_outputs_raw
    english_inputs = [x.strip() for x in mt_outputs]

    print(f"Creating English {task_name} prompt builder...")
    eng_cipher = _build_cipher("eng_Latn")
    task_cfg = _load_prompt_builder_config(task_prompt_builder_config_file, task_prompt_builder_config_id)
    task_prompt_builder = get_prompt_builder(
        task=task_name,
        language="eng_Latn",
        cipher_obj=eng_cipher,
        direction="comprehension",
        **task_cfg,
    )

    print(f"Building English {task_name} prompts...")
    task_prompts = _build_second_stage_prompts(
        task_name=task_name,
        prompt_builder=task_prompt_builder,
        task_use_cipher=task_use_cipher,
        english_inputs=english_inputs,
    )

    print(f"Running English {task_name} inference...")
    task_outputs_raw = inference.generate(
        task_prompts,
        max_new_tokens=task_max_new_tokens,
        batch_size=batch_size,
    )
    if task_use_cipher:
        task_outputs = [eng_cipher.decode(x) for x in task_outputs_raw]
    else:
        task_outputs = task_outputs_raw
    if task_name == "xstorycloze":
        task_outputs = [x.strip() for x in task_outputs]

    eval_data = []
    for i, ex in enumerate(examples):
        eval_data.append(
            {
                "input_src": input_src[i],
                "mt_prompt": mt_prompts[i],
                "mt_output_raw": mt_outputs_raw[i],
                "mt_output": mt_outputs[i],
                "input_en": english_inputs[i],
                "task_prompt": task_prompts[i],
                "task_output_raw": task_outputs_raw[i],
                "output": task_outputs[i],
                "reference": ex["output"],
                "metadata": ex.get("metadata", {}),
            }
        )

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(eval_data, f, ensure_ascii=False, indent=2)

    print("Running evaluation (accuracy)...")
    evaluator = EvaluationAccuracy()
    results, overall = evaluator.evaluate(eval_data)

    with open(f"{results_dir}/outputs_segment_scores.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    with open(f"{results_dir}/overall_scores.json", "w", encoding="utf-8") as f:
        json.dump(overall, f, ensure_ascii=False, indent=2)

    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Task: {task_name}")
    print(f"Source language: {src_language}")
    print(f"Examples: {overall['num_examples']}")
    print(f"Accuracy: {overall['accuracy']:.4f}")
    print("=" * 80)


if __name__ == "__main__":
    fire.Fire(main)
