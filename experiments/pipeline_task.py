import json
import os
import sys
from pathlib import Path

import fire

# Add parent directory to path to import from src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.build_prompt import get_prompt_builder
from src.ciphers import CVCipher, HanziCipher
from src.evaluation import EvaluationAccuracy
from src.inference import Inference
from src.task_data import TaskData


def _validate_task_direction(task_name: str, direction: str) -> None:
    if task_name == "xstorycloze" and direction != "comprehension":
        raise ValueError("XStoryCloze only supports comprehension direction.")


def _normalize_output(task_name: str, output_text: str) -> str:
    if task_name == "xstorycloze":
        return output_text.strip()
    return output_text


def main(
    language: str,
    task_name: str,
    direction: str,
    max_new_tokens: int,
    num_examples: int,
    batch_size: int,
    prompt_builder_config_file: str,
    prompt_builder_config_id: str,
    use_cipher: bool,
    model_key: str,
    output_file: str,
    results_dir: str,
    only_eval: bool = False,
):
    _validate_task_direction(task_name, direction)
    Path(results_dir).mkdir(parents=True, exist_ok=True)

    if not only_eval:
        print("Creating cipher...")
        if language == "cmn_hans":
            cipher_obj = HanziCipher(seed=42)
        else:
            cipher_obj = CVCipher(language=language, seed=42)
        print(f"  Cipher created successfully for {language}!\n")

        print(f"Loading {task_name} data...")
        task_data = TaskData(task_name=task_name, language=language)
        data_subset = task_data.load_data_method(
            direction=direction,
            split="dev",
            num_examples=num_examples,
        )
        print(f"  Loaded {len(data_subset)} examples\n")

        print("Round-trip checking cipher...")
        round_trip_checks = [
            cipher_obj.round_trip_check(example["input"]) for example in data_subset
        ]
        if not all(round_trip_checks):
            raise RuntimeError("Cipher round-trip check failed")
        print("  Round-trip check passed\n")

        print("Creating prompt builder...")
        with open(prompt_builder_config_file, "r", encoding="utf-8") as f:
            prompt_builder_configs = json.load(f)
        prompt_builder_config = prompt_builder_configs[prompt_builder_config_id]
        prompt_builder = get_prompt_builder(
            task=task_name,
            language=language,
            cipher_obj=cipher_obj,
            direction=direction,
            **prompt_builder_config,
        )
        print("  Prompt builder created successfully!\n")

        print("Initializing inference model...")
        inference = Inference(
            model_key=model_key,
            api_key=os.getenv("OPENAI_API_KEY"),
        )
        print("  Inference model initialized!\n")

        print(f"Building prompts (cipher={use_cipher})...")
        prompts = []
        prompts_raw = []
        for example in data_subset:
            input_text = example["input"]
            prompts.append(prompt_builder.build_prompt(input_text, cipher=use_cipher))
            prompts_raw.append(prompt_builder.build_prompt(input_text, cipher=False))
        print(f"  Example prompt:\n{prompts[0]}\n")
        print(f"  Built {len(prompts)} prompts\n")

        print(f"Running batched inference (cipher={use_cipher})...")
        responses = inference.generate(
            prompts,
            max_new_tokens=max_new_tokens,
            batch_size=batch_size,
        )
        print(f"  Generated {len(responses)} responses\n")

        if use_cipher and direction == "generation":
            responses_decoded = [cipher_obj.decode(r) for r in responses]
        else:
            responses_decoded = responses

        print("Preparing output data for evaluation...")
        eval_data = []
        for i, example in enumerate(data_subset):
            eval_data.append(
                {
                    "input": example["input"],
                    "output": _normalize_output(task_name, responses_decoded[i]),
                    "output_raw": responses[i],
                    "reference": example["output"],
                    "prompt": prompts[i],
                    "prompt_raw": prompts_raw[i],
                    "metadata": example.get("metadata", {}),
                }
            )
        print(f"  Prepared {len(eval_data)} examples\n")

        print("Saving outputs...")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(eval_data, f, ensure_ascii=False, indent=2)
        print(f"  Saved outputs to {output_file}\n")
    else:
        with open(output_file, "r", encoding="utf-8") as f:
            eval_data = json.load(f)

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
    print(f"Language: {language}")
    print(f"Examples: {overall['num_examples']}")
    print(f"Accuracy: {overall['accuracy']:.4f}")
    print(f"Outputs saved in: {output_file}")
    print(f"Results saved in: {results_dir}")
    print("=" * 80)


if __name__ == "__main__":
    fire.Fire(main)
