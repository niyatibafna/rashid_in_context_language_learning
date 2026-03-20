# In-Context Language Learning

This repository contains the code for < ICLL paper link >.

## What this repository provides

- Task loading and normalization (`src/task_data.py`)
- Cipher utilities for artificial unseen language construction (`src/ciphers.py`)
- Prompt builders using configurable combinations of materials in the language like lexicons, morphological tool outputs, and syntax descriptions, as per various strategies described in the paper (`src/build_prompt.py`). Materials and inputs are ciphered appropriately if needed.
- Model inference for local HF models and API-backed models (`src/inference.py`)
- Task-appropriate evaluation (`src/evaluation.py`)

## Repository structure

- `src/`: core library code (data, prompts, ciphers, inference, evaluation)
- `experiments/`: runnable pipelines. Pipelines applying ciphering to inputs, materials, and deciphering to outputs when relevant.
  - `pipeline.py`: Running MT in both directions with evaluation options with BLEU, chrF, COMET, GEMBA_MQM, or LLM-as-judge
  - `pipeline_task.py`: task pipeline with accuracy evaluation (e.g., XNLI, MMLU-ProX, XStoryCloze)
  - `pipeline_cascade_task.py`: two-stage cascade using MT (source -> English (using MT pipeline with specified ICL strategy) -> task inference)
  - `pipeline_word_for_word.py`: (non-LLM baseline) word-for-word translation by string concatenation of lexical equivalents.
- `experiments/configs_exps/`: experiment configs (e.g., prompt settings by config ID)
- `experiments/exps/`: shell/Slurm launch example scripts


## Setup

```bash
pip install -r requirements.txt
```

Set API credentials when using OpenAI-backed inference/evaluation:

```bash
export OPENAI_API_KEY="<your_key>"
```

## Typical usage

Run an MT experiment:

```bash
python experiments/pipeline.py \
  --language="spa_Latn" \
  --task_name="mtfloresplus" \
  --direction="generation" \
  --max_new_tokens=256 \
  --num_examples=16 \
  --batch_size=8 \
  --prompt_builder_config_file="experiments/configs_exps/lang_info.json" \
  --prompt_builder_config_id="E4" \
  --use_cipher=True \
  --model_key="llama" \
  --output_file="outputs/example/output.json" \
  --results_dir="outputs/example/results"
```

## Configuring inference strategies (`src/build_prompt.py`)

Inference strategy is controlled through prompt construction, implemented in `src/build_prompt.py` (via `get_prompt_builder(...)` and `BuildPromptLexicon`). Strategies are created as  experiment configs (as in `experiments/configs_exps/lang_info.json`) and selected at runtime.

### In-context language learning strategies available (from `src.build_prompt.py`)

`get_prompt_builder(task, language, cipher_obj, direction, **kwargs)` uses:
- `task`: task identifier (e.g., `mtfloresplus`, `xnli`, `mcqmmluprox`, `xstorycloze`)
- `language`: NLLB-style language code for the experiment language
- `cipher_obj`: cipher instance used by the prompt builder
- `direction`: `generation` or `comprehension`

Configurable `kwargs` for `BuildPromptLexicon`:
- `prompt_key`: prompt-builder type (currently must be `lexicon`)
- `lexicon`: lexicon source (`panlex` or `gtrans`)
- `word_class`: which words to translate (`content`, `function`, `all`)
- `nes_only`: if `True`, translate only named entities
- `lemmas_only`: if `True`, translate only lemma-form words
- `use_lemmatizer`: enable lemmatization during word selection
- `num_exemplars`: number of retrieved in-context exemplars
- `add_word_features`: include POS/lemma/NE-style features in prompt text
- `add_syntax_description`: include language syntax guidance
- `add_inflection_paradigms`: include inflection/paradigm information
- `add_related_language_translation`: add related-language translation support text
- `cascade_related_language`: cascade through a related language (generation setting)

### How to use configs

1. Create config entries in a JSON file (e.g., `experiments/configs_exps/lang_info.json`) with your strategy settings keyed by ID (e.g., `B0`, `E1`).
2. Pass that file and key into the pipeline:
   - `--prompt_builder_config_file="experiments/configs_exps/lang_info.json"`
   - `--prompt_builder_config_id="E1"`
3. `pipeline.py` loads the selected config and forwards it to `get_prompt_builder(...)`.

Run an accuracy-based task:

```bash
python experiments/pipeline_task.py \
  --language="hin_Deva" \
  --task_name="xnli" \
  --direction="comprehension" \
  --max_new_tokens=256 \
  --num_examples=16 \
  --batch_size=8 \
  --prompt_builder_config_file="experiments/configs_exps/lang_info.json" \
  --prompt_builder_config_id="E1" \
  --use_cipher=True \
  --model_key="gpt-5.1" \
  --output_file="task_outputs/xnli/output.json" \
  --results_dir="outputs/xnli/results"
```

## Misc

- MT outputs and associated automatic evaluations for all strategies described in the paper for both directions and 3 models are in `outputs_and_results/mt_outputs.zip`. 
- Task results for all strategies are in `outputs_and_results/task_results.json`.
- Configs for all strategies described in the paper are in `experiments/configs_exps/lang_info.json`.
- Run the `topline` experiments on original language inputs without ciphering by using config `B0` and setting `use_cipher=False`. 
- We also provide a word-for-word baseline in `src/word_for_word_baseline.py`.


## Extending the project

- **New language:** add metadata and language codes in `src/utils/lang_codes.py`, then add cipher support in `src/ciphers.py`.
- **New task:** implement loading/formatting in `src/task_data.py` to return consistent `input`/`output` fields.
- **New prompting strategy:** extend `src/build_prompt.py` and add new corresponding experiment configs.
- **New model backend:** add support in `src/inference.py`.
- **New metric/evaluator:** implement in `src/evaluation.py` and wire into the relevant pipeline(s).


