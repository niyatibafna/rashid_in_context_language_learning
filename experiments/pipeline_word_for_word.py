'''
Word-for-word baseline pipeline: same structure as pipeline.py but uses
word_for_word_translate for inference. Input/output languages are set from direction.

Example run:
python experiments/pipeline_word_for_word.py \
  --language="spa_Latn" \
  --task_name="mtfloresplus" \
  --direction="generation" \
  --num_examples=16 \
  --lexicon="gtrans" \
  --output_file="outputs/wfw/lang_info/spa_Latn_gen_16.json" \
  --results_dir="outputs/wfw/lang_info/spa_Latn_gen_16" \
  --evaluate_comet=False --evaluate_gemba=False --evaluate_llm_judge=None
'''

import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.word_for_word_baseline import WordForWordBaseline
from src.task_data import TaskData
from src.evaluation import EvaluationStringBased, EvaluationComet, EvaluationLLMasJudge, EvaluationGEMBA


def main(
    language: str,
    task_name: str,
    direction: str,
    num_examples: int,
    lexicon: str = "panlex",
    output_file: str = None,
    results_dir: str = None,
    only_eval: bool = False,
    evaluate_comet: bool = False,
    evaluate_gemba: bool = False,
    evaluate_llm_judge: str = None,
):
    if direction == "comprehension":
        input_lang = language
        output_lang = "eng_Latn"
    else:
        input_lang = "eng_Latn"
        output_lang = language

    if not only_eval:
        print("Loading task data...")
        task_data = TaskData(task_name=task_name, language=language)
        data_subset = task_data.load_data_method(direction=direction, split="dev", num_examples=num_examples)
        print(f"  Loaded {len(data_subset)} examples from task dataset")
        print()

        print("Creating word-for-word baseline...")
        baseline = WordForWordBaseline(input_lang=input_lang, output_lang=output_lang, lexicon=lexicon)
        print("  Baseline created successfully!")
        print()

        print("Running word-for-word inference...")
        responses = [baseline.word_for_word_translate(example["input"]) for example in data_subset]
        print(f"  Generated {len(responses)} responses")
        print()

        print("Preparing output data for evaluation...")
        eval_data = []
        for i, example in enumerate(data_subset):
            eval_item = {
                "input": example["input"],
                "output": responses[i],
                "output_raw": responses[i],
                "reference": example["output"],
                "prompt": "",
                "prompt_raw": "",
                "metadata": example.get("metadata", {}),
            }
            eval_data.append(eval_item)
        print(f"  Prepared {len(eval_data)} examples for evaluation")
        print()

        print("Saving outputs to JSON...")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(eval_data, f, ensure_ascii=False, indent=2)
        print(f"  Saved: {output_file}")
        print()

    # Evaluation (identical to pipeline.py)
    print("Running evaluation (BLEU and chrF)...")
    results_file = f"{results_dir}/outputs_segment_scores.json"
    overall_file = f"{results_dir}/overall_scores.json"

    if os.path.exists(results_file) and os.path.exists(overall_file):
        with open(results_file, "r", encoding="utf-8") as f:
            results = json.load(f)
        with open(overall_file, "r", encoding="utf-8") as f:
            overall = json.load(f)
        print(f"  Loaded results from {results_file}")
        print(f"  Loaded overall scores from {overall_file}")
    else:
        with open(output_file, "r", encoding="utf-8") as f:
            results = json.load(f)
        overall = {}

    evaluator_string = EvaluationStringBased()
    print("  Evaluating outputs...")
    results, string_overall = evaluator_string.evaluate(results)
    overall.update(string_overall)
    print(f"    Overall BLEU: {overall['bleu']:.4f}")
    print(f"    Overall chrF: {overall['chrf']:.4f}")
    print()

    if evaluate_comet:
        print("Running COMET evaluation")
        evaluator_comet = EvaluationComet("Unbabel/XCOMET-XL")
        print("  Evaluating outputs with COMET...")
        results, comet_overall = evaluator_comet.evaluate(results)
        overall.update(comet_overall)

    if evaluate_llm_judge:
        from src.inference import Inference
        function = evaluate_llm_judge.split(":")[0]
        gpt_object = Inference(model_key="gpt-5.1", api_key=os.getenv("OPENAI_API_KEY"))
        llm_judge = EvaluationLLMasJudge(llm_object=gpt_object, language=language, eval_key=function)
        if function == "md_win_rate":
            assert len(evaluate_llm_judge.split(":")) == 2, "md_win_rate requires a base_data_name"
            base_config_id = evaluate_llm_judge.split(":")[1]
            base_filepath = os.path.join(os.path.dirname(output_file), base_config_id + ".json")
            print(f"Running LLM-Judge evaluation for multidimensional win rate with base data from file: {base_filepath}")
            results, overall_llm_judge = llm_judge.evaluate(base_filepath=base_filepath, eval_filepath=results, base_data_name=base_config_id)
        else:
            print(f"Running LLM-Judge evaluation for {function}")
            results, overall_llm_judge = llm_judge.evaluate(results)
        overall.update(overall_llm_judge)

    if evaluate_gemba:
        print("Running GEMBA evaluation")
        if direction == "generation":
            source_lang = "eng_Latn"
            target_lang = language
        else:
            source_lang = language
            target_lang = "eng_Latn"
        gemba = EvaluationGEMBA(method="GEMBA-MQM", model="gpt-4.1", source_lang=source_lang, target_lang=target_lang)
        results, overall_gemba = gemba.evaluate(results)
        overall.update(overall_gemba)

    with open(results_file, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    with open(overall_file, "w", encoding="utf-8") as f:
        json.dump(overall, f, ensure_ascii=False, indent=2)

    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Processed {num_examples} translation examples for {language} (direction={direction})")
    print(f"Output files saved in: {output_file}")
    print(f"Evaluation results saved in: {results_dir}")
    print(f"Evaluation Scores: BLEU: {overall['bleu']:.4f}, chrF: {overall['chrf']:.4f}")
    print("=" * 80)


if __name__ == "__main__":
    import fire
    fire.Fire(main)
