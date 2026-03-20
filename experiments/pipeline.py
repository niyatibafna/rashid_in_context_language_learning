'''
Example run:
python experiments/pipeline.py 
--language="spa_Latn" 
--task_name="mtfloresplus" 
--direction="generation" 
--max_new_tokens=256 
--num_examples=16 
--batch_size=8 
--prompt_builder_config_file="experiments/configs_exps/lang_info.json"
--prompt_builder_config_id="1"
--evaluate_comet=False --evaluate_llm_judge=False --evaluate_gemba=False --use_cipher=True --model_key="llama" --output_dir="outputs/lang_info/llama_samples-16"

Check out inference.py for model_key options.
Check out build_prompt.get_prompt_builder for prompt_key options.
'''


import sys
import os
import json
from pathlib import Path
import fire
import re

# Add parent directory to path to import from src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.inference import Inference
from src.ciphers import CVCipher, HanziCipher
from src.task_data import TaskData
from src.build_prompt import get_prompt_builder
from src.evaluation import EvaluationStringBased, EvaluationComet, EvaluationLLMasJudge, EvaluationGEMBA

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
    output_file: str = None,
    results_dir: str = None,
    only_eval: bool = False,
    evaluate_comet: bool = False, 
    evaluate_gemba: bool = False,
    evaluate_llm_judge: str = None, # expected to have value of EvaluationLLMasJudge.eval_key, with additional semicolon-separated options
):
    if not only_eval:
        print("Creating cipher...")
        if language == "cmn_hans":
            cipher_obj = HanziCipher(seed=42)
        else:    
            cipher_obj = CVCipher(language=language, seed=42)
        print(f"  Cipher created successfully for {language}!")
        print()
        
        # Step 3: Load task data
        print("Loading task data...")
        task_data = TaskData(task_name=task_name, language=language)
        data_subset = task_data.load_data_method(direction=direction, split="dev", num_examples=num_examples)
        print(f"  Loaded {len(data_subset)} examples from task dataset")

        # Round-trip check for cipher
        print("Round-trip checking cipher...")
        round_trip_checks = [cipher_obj.round_trip_check(example['input']) for example in data_subset]
        if not all(round_trip_checks):
            print(f"Round-trip check failed for {len(round_trip_checks)} examples")
            print()
        else:
            print(f"Round-trip check passed for all {len(round_trip_checks)} examples")
            print()

        
        print("Creating prompt builder...")
        with open(prompt_builder_config_file, 'r') as f:
            prompt_builder_configs = json.load(f)

        prompt_builder_config = prompt_builder_configs[prompt_builder_config_id]
        prompt_builder = get_prompt_builder(task=task_name, language=language, cipher_obj=cipher_obj, direction=direction, **prompt_builder_config)
        print("  Prompt builder created successfully!")
        print()
        
        print("Initializing inference model...")
        inference = Inference(
            model_key=model_key,
            api_key=os.getenv("OPENAI_API_KEY")
        )
        
        print("  Inference model initialized!")
        print()
        
        # Step 6: Build prompts for all examples
        print(f"Building prompts (cipher={use_cipher})...")
        prompts = []
        prompts_raw = []
        for i, example in enumerate(data_subset):
            input_text = example['input']
            prompt = prompt_builder.build_prompt(input_text, cipher=use_cipher)
            prompts.append(prompt)
            # Build clean prompt for sake of evaluation
            prompts_raw.append(prompt_builder.build_prompt(input_text, cipher=False))


        print(f"  Example prompt: {prompts[0]}")
        print(f"  Built {len(prompts)} prompts")
        print()
        
        # Step 7: Run batched inference
        print(f"Running batched inference (cipher={use_cipher})...")
        print(f"  Processing {len(prompts)} prompts in batches of {batch_size}...")
        responses = inference.generate(
            prompts, 
            max_new_tokens=max_new_tokens,
            batch_size=batch_size
        )
        print(f"  Generated {len(responses)} responses")
        print()
        
        # If model is generating ciphered text, decode it
        if use_cipher and direction == "generation":
            responses_decoded = [cipher_obj.decode(response) for response in responses]
        else:
            responses_decoded = responses
        
        # Step 9: Prepare output data for evaluation
        print("Preparing output data for evaluation...")
        
        eval_data = []
        for i, example in enumerate(data_subset):
            eval_item = {
                "input": example['input'],
                "output": responses_decoded[i],
                "output_raw": responses[i],
                "reference": example['output'],
                "prompt": prompts[i],
                "prompt_raw": prompts_raw[i],
                "metadata": example.get('metadata', {})
            }
            eval_data.append(eval_item)
        
        print(f"  Prepared {len(eval_data)} examples for evaluation")
        print()
        
        # Step 10: Save outputs to JSON files
        print("Saving outputs to JSON files...")
    
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(eval_data, f, ensure_ascii=False, indent=2)
        print(f"  Saved: {output_file}")
        print()
        
    # Step 11: Run evaluation (BLEU and chrF)
    print(f"Running evaluation (BLEU and chrF) (cipher={use_cipher})...")
    
    # We start with contents of output_file, and add per sample keys to the JSON. We save it to results_file.
    # If we have previously done some evaluation, we do not overwrite the results file, but rather add keys to it.

    results_file = f"{results_dir}/outputs_segment_scores.json"
    overall_file = f"{results_dir}/overall_scores.json"

    # If exist, load results and overall scores
    if os.path.exists(results_file) and os.path.exists(overall_file):
        with open(results_file, 'r', encoding='utf-8') as f:
            results = json.load(f)
        with open(overall_file, 'r', encoding='utf-8') as f:
            overall = json.load(f)
        print(f"  Loaded results from {results_file}")
        print(f"  Loaded overall scores from {overall_file}")
    else:
        with open(output_file, 'r', encoding='utf-8') as f: # 
            results = json.load(f)
        overall = {}

    evaluator_string = EvaluationStringBased()
    
    print(f"  Evaluating outputs...")
    results, string_overall = evaluator_string.evaluate(results)

    overall.update(string_overall)
    
    print(f"    Overall BLEU: {overall['bleu']:.4f}")
    print(f"    Overall chrF: {overall['chrf']:.4f}")
    print()
    
    # Step 12: Run COMET evaluation 
    if evaluate_comet:
        print("Running COMET evaluation ")
        evaluator_comet = EvaluationComet("Unbabel/XCOMET-XL")
        
        print(f"  Evaluating outputs with COMET...")
        results, comet_overall = evaluator_comet.evaluate(
            results
        )
        overall.update(comet_overall)
    
    # Step 13: Run LLM-Judge evaluation for fluency score
    if evaluate_llm_judge: # of type "<function>:<options>"
        function = evaluate_llm_judge.split(":")[0]
        gpt_object = Inference(
            model_key="gpt-5.1",
            api_key=os.getenv("OPENAI_API_KEY")
        )
        llm_judge = EvaluationLLMasJudge(llm_object=gpt_object, language=language, eval_key=function)
        if function == "md_win_rate":
            assert len(evaluate_llm_judge.split(":")) == 2, "md_win_rate requires a base_data_name"
            base_config_id = evaluate_llm_judge.split(":")[1]
            # Replace the prompt_builder_config_id with the base_config_id in the output_file
            base_filepath = re.sub(prompt_builder_config_id, base_config_id, output_file)
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

    
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    with open(overall_file, 'w', encoding='utf-8') as f:
        json.dump(overall, f, ensure_ascii=False, indent=2)

    
    # Step 12: Summary
    print("=" * 80)
    print("Summary")
    print("=" * 80)
    print(f"Processed {num_examples} translation examples for {language}")
    print(f"\nOutput files saved in: {output_file}")
    print(f"\nEvaluation results saved in: {results_dir}")
    print(f"\nEvaluation Scores:")
    print(f"  BLEU: {overall['bleu']:.4f}, chrF: {overall['chrf']:.4f}")
    print("=" * 80)

if __name__ == "__main__":
    fire.Fire(main)

