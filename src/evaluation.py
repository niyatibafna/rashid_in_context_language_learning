from typing import Dict, Any, List, Tuple, Union
import re
import json
import sacrebleu
from comet import download_model, load_from_checkpoint
from src.utils.lang_codes import LANGS
from gemba.utils import get_gemba_scores
import random

class EvaluationAccuracy:
    """
    Evaluation class for numeric (1–10) tasks.
    Computes exact-match accuracy.
    """
    def __init__(self, normalize: bool = True):
        self.normalize = normalize

    def _normalize(self, x: str):
        if not self.normalize:
            return x

        x = x.strip()

        # extract first integer in the string
        match = re.search(r"\d+", x)
        if match is None:
            return None

        value = int(match.group())
        if 0 <= value <= 10: # covers xnli, xstorycloze, and mmlu ranges
            return value

        return None


    def evaluate(
        self,
        filepath: Union[str, List[Dict[str, Any]]]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, float]]:

        if not isinstance(filepath, str):
            data = filepath
        else:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

        correct = 0
        total = len(data)
        results = data.copy()

        for i, item in enumerate(data):
            pred = item["output"]
            ref = item["reference"]

            pred_n = self._normalize(pred)
            ref_n = self._normalize(ref)

            is_correct = pred_n == ref_n
            correct += int(is_correct)

            results[i]["accuracy_correct"] = is_correct

        accuracy = correct / total if total > 0 else 0.0

        overall_scores = {
            "accuracy": accuracy,
            "num_examples": total,
            "num_correct": correct,
        }
        return results, overall_scores

class EvaluationStringBased:
    '''
    Evaluation class that computes BLEU and chrF scores using sacrebleu.
    '''
    
    def __init__(self):
        '''
        Initialize the EvaluationStringBased class.
        '''
        pass
    
    def evaluate(self, filepath: Union[str, List[Dict[str, Any]]]) -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
        '''
        Evaluate translations using BLEU and chrF metrics.
        
        Args:
            filepath: Path to JSON file or list of dictionaries with:
                - "input": Input text
                - "output": Generated output text
                - "reference": Reference text
                - any other keys        
        Returns:
            Tuple of:
            - List of dictionaries with original keys plus "eval_scores" containing BLEU and chrF scores
            - Dictionary with overall scores (averaged across all examples)
        '''
        if not isinstance(filepath, str):
            data = filepath
        else:
        # Load data from JSON file
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
        # Extract references and hypotheses
        references = []
        hypotheses = []
        results = data.copy() # Deep copy of the data
        
        for item in data:
            reference = item["reference"]
            output = item["output"]
            
            references.append(reference)
            hypotheses.append(output)
        
        # Compute corpus-level BLEU and chrF scores
        # SacreBLEU expects references as a list of lists (for multiple references)
        # For single reference, wrap in list
        bleu = sacrebleu.corpus_bleu(hypotheses, [references])
        chrf = sacrebleu.corpus_chrf(hypotheses, [references])
        
        # Compute sentence-level scores for each example
        for i, item in enumerate(data):
            reference = item["reference"]
            output = item["output"]
            
            # Compute sentence-level BLEU (using corpus_bleu with single sentence)
            sent_bleu = sacrebleu.corpus_bleu([output], [[reference]])
            
            # Compute sentence-level chrF (using corpus_chrf with single sentence)
            sent_chrf = sacrebleu.corpus_chrf([output], [[reference]])
            
            # Add eval_scores to result
            results[i]["bleu_score"] = sent_bleu.score
            results[i]["chrf_score"] = sent_chrf.score
        
        # Overall scores (corpus-level)
        overall_scores = {
            "bleu": bleu.score,
            "chrf": chrf.score
        }
        
        return results, overall_scores


class EvaluationComet:
    '''
    Evaluation class that computes COMET scores for translation quality.
    '''
    
    def __init__(self, model_name: str = "Unbabel/wmt22-comet-da"):
        '''
        Initialize the EvaluationComet class.
        
        Args:
            model_name: Name of the COMET model to use. Default is "Unbabel/wmt22-comet-da". For xCOMET-XXL: "Unbabel/XCOMET-XXL"
                        
        '''
        self.model_name = model_name
        self.model = None
        self._load_model()
    
    def _load_model(self):
        '''
        Load the COMET model. Downloads if not already cached.
        '''
        try:
            model_path = download_model(self.model_name)
            self.model = load_from_checkpoint(model_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load COMET model {self.model_name}: {e}")
    
    def evaluate(self, filepath: Union[str, List[Dict[str, Any]]], batch_size: int = 8, gpus: int = 1) -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
        '''
        Evaluate translations using COMET metric.
        
        Args:
            filepath: Path to JSON file containing list of dictionaries with:
                - "input": Source text (input)
                - "output": Generated translation (hypothesis)
                - "reference": Reference translation
                - any other keys
            batch_size: Batch size for COMET evaluation (default: 8)
            gpus: Number of GPUs to use (default: 1)
        
        Returns:
            Tuple of:
            - List of dictionaries with original keys plus "eval_scores" containing COMET score
            - Dictionary with overall scores (averaged across all examples)
        '''
        # Load data from JSON file
        if not isinstance(filepath, str):
            data = filepath
        else:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        
        # Prepare data for COMET
        comet_data = []
        
        for item in data:
            source = item["input"]
            translation = item["output"]
            reference = item["reference"]
            
            comet_data.append({
                "src": source,
                "mt": translation,
                "ref": reference
            })
            
        # Compute COMET scores
        try:
            scores = self.model.predict(comet_data, batch_size=batch_size, gpus=gpus)
        except Exception as e:
            raise RuntimeError(f"Failed to compute COMET scores: {e}")
        
        # Extract scores (COMET returns a list of scores)
        comet_scores = scores.scores 
        comet_spans = scores.metadata.error_spans if hasattr(scores, 'metadata') and hasattr(scores.metadata, 'error_spans') else None
        # Add scores to results
        results = data.copy() # Deep copy of the data
        assert len(results) == len(comet_scores), "Number of results and comet scores do not match"
        for i, score in enumerate(comet_scores):
            results[i]["comet_score"] = float(score)
            results[i]["comet_spans"] = comet_spans[i] if comet_spans else None

        overall_score = scores.system_score
        overall_scores = {
            "comet": overall_score,
        }
        return results, overall_scores


class EvaluationGEMBA:
    """
    Evaluation class that computes GEMBA scores (GEMBA-DA or GEMBA-MQM)
    using the official Microsoft GEMBA repo.
    """

    def __init__(
        self,
        method: str = "GEMBA-MQM",
        model: str = "gpt-4", 
        source_lang: str = "eng_Latn",
        target_lang: str = "eng_Latn",
    ):
        """
        Args:
            method: "GEMBA-MQM" (error-based QE) or "GEMBA-DA" (DA-style score)
            model:  OpenAI model name passed to GEMBA (e.g. "gpt-4", "gpt-4o")
            source_lang: source language code as GEMBA expects
            target_lang: target language code as GEMBA expects
        """
        self.method = method
        self.model = model
        self.source_lang = LANGS[source_lang]["name"]
        self.target_lang = LANGS[target_lang]["name"]

    
    def _parse_gemba_output_into_mqm_score(self, gemba_output: str) -> List[Dict[str, Any]]:
        '''
        Parse the GEMBA output into MQM errors.
        '''
        mqm_score = 0
        for error_level in gemba_output:
            if error_level not in ["critical", "major", "minor"]:
                continue
            for _ in gemba_output[error_level]:
                mqm_score += 25 if error_level == "critical" else 10 if error_level == "major" else 5 if error_level == "minor" else 0

        mqm_score = min(mqm_score, 25)
        return -mqm_score

    def evaluate(
        self,
        filepath: Union[str, List[Dict[str, Any]]],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
        """
        Evaluate translations using GEMBA.

        For GEMBA-DA:
          - returns a scalar score per segment (0–100 style).
        For GEMBA-MQM:
          - GEMBA repo currently returns a scalar MQM-like score per segment
            (one number per line); you can store that as `gemba_score`.
        """
        # load data like your other evaluators
        if not isinstance(filepath, str):
            data = filepath
        else:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

        # GEMBA only uses src + mt (ref is ignored for MQM; DA mode can include ref
        # via its own scripts, but the public `main.py` and `get_gemba_scores`
        # use (source, hypothesis) lists)
        sources = [item["input"] for item in data]
        hypotheses = [item["output"] for item in data]

        # call GEMBA
        # get_gemba_scores(source: List[str], hyp: List[str], src_lang, tgt_lang, method, model, list_mqm_errors=False)
        gemba_outputs = get_gemba_scores(
            sources,
            hypotheses,
            self.source_lang,
            self.target_lang,
            self.method,
            self.model,
            list_mqm_errors=True,
        )

        results = data.copy()
        for i, output in enumerate(gemba_outputs):
            results[i]["gemba_output"] = dict(output)
            results[i]["gemba_mqm_score"] = self._parse_gemba_output_into_mqm_score(dict(output))

        overall_score = sum(results["gemba_mqm_score"] for results in results) / len(results)
        overall_scores = {
            "gemba_mqm": overall_score,
        }
        return results, overall_scores

        



class EvaluationLLMasJudge:
    '''
    Evaluation class that computes LLM-Judge scores for fluency.
    '''
    def __init__(self, llm_object, language: str, eval_key: str):
        '''
        Initialize the EvaluationLLMasJudge class.
        Args:
            llm_object: Inference* object, has generate method
            language: Language code
            eval_key: Key to use for evaluation
        '''
        self.llm_object = llm_object
        self.language = language
        self.eval_key = eval_key
        self.eval_key_map = {
            "fluency_score": self._evaluate_fluency_score,
            "error_and_fluency_score": self._evaluate_errors_and_fluency_score,
            "md_win_rate": self._evaluate_md_win_rate_separate,
        }
        if eval_key not in self.eval_key_map:
            raise ValueError(f"Evaluation key {eval_key} not supported")
        self.evaluate = self.eval_key_map[eval_key]
    

    def _validate_and_parse_response_fluency_score(self, response: str) -> Tuple[List[str], int]:
        '''
        Validate and parse the response for fluency score. It should only contain the fluency score and no other text.
        '''
        no_valid_score = False
        # Check if the response contains only a single number
        if not re.match(r'^\d+$', response):
            no_valid_score = True
            return no_valid_score, -1
        return no_valid_score, int(response)
        
    def _evaluate_fluency_score(self, filepath: Union[str, List[Dict[str, Any]]]) -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
        '''
        Evaluate fluency score *independent of source or reference* using LLM-Judge.
        '''
        if not isinstance(filepath, str):
            data = filepath
        else:
        # Load data from JSON file
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
        # Prepare data for evaluation
        evaluation_data = data.copy() # Deep copy of the data
        
        # Evaluate fluency score
        eval_fluency_prompt = '''Evaluate the fluency of the following text in {language}. Output a fluency score between 1-5 according to the following criteria: 
        1 = completely incomprehensible, 
        2 = Several major grammatical errors 
        3 = At least one major error
        4 = No major errors, but some minor grammatical errors,
        5 = No errors.

        The output should only be a single number and should contain no other text.
        Text: {text}
        Fluency score (1-5):
        '''
        
        prompts = [eval_fluency_prompt.format(language=self.language, text=item["output"]) for item in evaluation_data]
        responses = self.llm_object.generate(prompts)
        for idx, response in enumerate(responses):
            no_valid_score, fluency_score = self._validate_and_parse_response_fluency_score(response)
            if no_valid_score:
                evaluation_data[idx]["llmasjudge_response"] = response
                evaluation_data[idx]["fluency_score"] = -1
            else:
                evaluation_data[idx]["llmasjudge_response"] = response
                evaluation_data[idx]["fluency_score"] = int(fluency_score)

        num_valid_scores = len([item for item in evaluation_data if item["fluency_score"] != -1])
        overall_score = sum(item["fluency_score"] for item in evaluation_data if item["fluency_score"] != -1) / num_valid_scores
        overall_scores = {
            "fluency_score": overall_score,
            "percentage_valid_scores": num_valid_scores / len(evaluation_data) * 100 if len(evaluation_data) > 0 else 0,
            "num_valid_scores": num_valid_scores,
        }
        return evaluation_data, overall_scores
    
    def _validate_and_parse_response_errors_and_fluency_score(self, response: str) -> Tuple[List[str], int]:
        '''
        Validate and parse the response for fluency score.
        '''
        no_valid_score = False
        if "Grammatical errors:" not in response:
            no_valid_score = True
            return no_valid_score, [], -1
        if "Fluency score (1-5):" not in response:
            no_valid_score = True
            return no_valid_score, [], -1
        grammatical_errors = response.split("Grammatical errors:")[1].split("Fluency score (1-5):")[0].strip()
        fluency_score = response.split("Fluency score (1-5):")[1].strip()

        if not grammatical_errors.strip():
            no_valid_score = True
        if not fluency_score.strip():
            no_valid_score = True
        
        if type(fluency_score) != int:
            no_valid_score = True
        if fluency_score < 1 or fluency_score > 5:
            no_valid_score = True

        return no_valid_score, grammatical_errors, fluency_score

    def _evaluate_errors_and_fluency_score(self, filepath: Union[str, List[Dict[str, Any]]]) -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
        '''
        Evaluate fluency score *independent of source or reference* using LLM-Judge.
        '''
        if not isinstance(filepath, str):
            data = filepath
        else:
        # Load data from JSON file
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
        # Prepare data for evaluation
        evaluation_data = data.copy() # Deep copy of the data
        
        # Evaluate fluency score
        eval_fluency_prompt = '''Evaluate the fluency of the following text in {language}. Output the following things:
        1. A list of the grammatical errors in the text. Grammatical errors include errors such as incorrect inflection, missing or extra function words. 
        2. A fluency score between 1-5 according to the following criteria: 
        1 = completely incomprehensible, 
        2 = Several major grammatical errors 
        3 = At least one major error
        4 = No major errors, but some minor grammatical errors,
        5 = No errors.

        The output should be in the following format:
        Output:
        Grammatical errors:
        - <error_1>
        - <error_2>
        - ...
        
        Fluency score (1-5): <score>

        Text: {text}
        Output:
        '''
        
        prompts = [eval_fluency_prompt.format(language=self.language, text=item["output"]) for item in evaluation_data]
        responses = self.llm_object.generate(prompts)
        for idx, response in enumerate(responses):
            no_valid_score, grammatical_errors, fluency_score = self._validate_and_parse_response_fluency_score(response)
            if no_valid_score:
                evaluation_data[idx]["llmasjudge_response"] = response
                evaluation_data[idx]["grammatical_errors"] = []
                evaluation_data[idx]["fluency_score"] = -1
            else:
                evaluation_data[idx]["llmasjudge_response"] = response
                evaluation_data[idx]["grammatical_errors"] = grammatical_errors
                evaluation_data[idx]["fluency_score"] = int(fluency_score)

        num_valid_scores = len([item for item in evaluation_data if item["fluency_score"] != -1])
        overall_score = sum(item["fluency_score"] for item in evaluation_data if item["fluency_score"] != -1) / num_valid_scores
        overall_scores = {
            "fluency_score": overall_score,
            "percentage_valid_scores": num_valid_scores / len(evaluation_data) * 100 if len(evaluation_data) > 0 else 0,
            "num_valid_scores": num_valid_scores,
        }
        return evaluation_data, overall_scores


    def _validate_and_parse_response_md_win_rate(self, response: str) -> Tuple[List[str], int]:
        '''
        Validate and parse the response for MD win rate.
        '''
        # Valid response should be a JSON string of the specified format
        no_valid_response = False
        try:
            json.loads(response)
        except:
            print(f"Invalid JSON string: {response}")
            no_valid_response = True
            return no_valid_response, {}
        output = json.loads(response)
        keys = ["semantics_winner", "semantics_rationale", "morphology_winner", "morphology_rationale", "word_order_winner", "word_order_rationale", "overall_winner", "overall_rationale"]
        for key in keys:
            if key not in output:
                no_valid_response = True
            if "winner" in key and output[key] not in ["First", "Second"]:
                no_valid_response = True
        if no_valid_response:
            return no_valid_response, {}
        return no_valid_response, output
    
    def _evaluate_md_win_rate(self, base_filepath: Union[str, List[Dict[str, Any]]], eval_filepath: Union[str, List[Dict[str, Any]]], base_data_name:str = "base") -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
        '''
        Evaluate the multidimensional win rate of outputs from eval_filepath against outputs from base_filepath.
        '''
        if not isinstance(base_filepath, str):
            base_data = base_filepath
        else:
            with open(base_filepath, 'r', encoding='utf-8') as f:
                base_data = json.load(f)

        if not isinstance(eval_filepath, str):
            evaluation_data = eval_filepath
        else:
            with open(eval_filepath, 'r', encoding='utf-8') as f:
                evaluation_data = json.load(f)

        base_outputs = [item["output"] for item in base_data]
        eval_outputs = [item["output"] for item in evaluation_data]

        prompt = '''You will be given an input, a reference, and two candidate translations. Your task is to identify the better candidate, based on 1) semantics 2) morphological correctness *regardless of semantics* 3) word order *regardless of semantics*, 4) overall quality of translation. 
        Evaluate morphology (agreement, inflection, word structure) and word order (natural clause and word ordering) even if the translation is semantically wrong or nonsensical, based on characteristics of the target language.
        The final criterion should judge general quality.
        For each criterion, output "First" if the first candidate is better, "Second" if the second candidate is better. Please decide on a definite winner; ties are not allowed.
        Please evaluate the two candidates on each criterion *as independently as possible*. *The judgements for each criterion may or may not agree with others*. 
        For each, please additionally output a brief one-sentence rationale.
        Output a JSON string of the following format:
        {{
            "semantics_winner": "<'First' or 'Second'>",
            "semantics_rationale": "<one-sentence rationale for semantics winner>",
            "morphology_winner": "<'First' or 'Second'>",
            "morphology_rationale": "<one-sentence rationale for morphology winner>",
            "word_order_winner": "<'First' or 'Second'>",
            "word_order_rationale": "<one-sentence rationale for word order winner>",
            "overall_winner": "<'First' or 'Second'>",
            "overall_rationale": "<one-sentence rationale for overall winner>"
        }}
        DO NOT output any other text than the JSON string. Ensure that the JSON string is valid and complete, with only the options specified above. Ensure that all keys are present and that the values are valid.

        Input:\n{input}
        Reference:\n{reference}
        Candidate 1:\n{candidate1}
        Candidate 2:\n{candidate2}
        Output:
        '''

        # Random order the order or the base and eval output to show to the LLM
        position_of_eval = [random.choice([0, 1]) for _ in range(len(evaluation_data))]
        prompts = []
        for i, item in enumerate(evaluation_data):
            if eval_outputs[i] == "" or base_outputs[i] == "":
                prompts.append(None)
                continue
            if position_of_eval[i] == 0:
                prompts.append(prompt.format(input=item["input"], reference=item["reference"], candidate1=eval_outputs[i], candidate2=base_outputs[i]))
            else:
                prompts.append(prompt.format(input=item["input"], reference=item["reference"], candidate1=base_outputs[i], candidate2=eval_outputs[i]))
        # prompts = [prompt.format(input=item["input"], reference=item["reference"], candidate1=base_outputs[i], candidate2=eval_outputs[i]) for i, item in enumerate(evaluation_data)]

        # responses = self.llm_object.generate(prompts)
        responses = []
        for prompt in prompts:
            if prompt is not None:
                response = self.llm_object.generate([prompt])[0]
                responses.append(response)
            else:
                responses.append(None)

        index_key_map = {0: "First", 1: "Second"} # If position of eval is 0, then we win if answer is "First", else "Second"

        for idx, response in enumerate(responses):

            # Debugging
            print(f"Base output: {base_outputs[idx]}")
            print(f"Eval output: {eval_outputs[idx]}")
            print(f"Position of eval: {position_of_eval[idx]}")
            print(f"Prompt: {prompts[idx]}")
            print(f"Response: {response}")

            if response is None:
                no_valid_response = True
            else:
                no_valid_response, output = self._validate_and_parse_response_md_win_rate(response)
            for key in output:
                if no_valid_response:
                    evaluation_data[idx][f"llmasjudge_{base_data_name}_{key}"] = None
                    continue


                if "winner" in key:
                    evaluation_data[idx][f"llmasjudge_{base_data_name}_{key}"] = index_key_map[position_of_eval[idx]] == output[key]
                    print(f"Key: {key}")
                    print(f"Winner: {index_key_map[position_of_eval[idx]] == output[key]}")
                else:
                    print(f"Key: {key}")
                    print(f"Output: {output[key]}")
                    evaluation_data[idx][f"llmasjudge_{base_data_name}_{key}"] = output[key]

            print("--------------------------------")

        # Win rate is the number of times the eval candidate is the winner. We take the order of the base and eval output into account.

        overall_semantics_win_rate = sum(1 for i, item in enumerate(evaluation_data) if item[f"llmasjudge_{base_data_name}_semantics_winner"]) / len([item for item in evaluation_data if item[f"llmasjudge_{base_data_name}_semantics_winner"] != None])
        overall_morphology_win_rate = sum(1 for i, item in enumerate(evaluation_data) if item[f"llmasjudge_{base_data_name}_morphology_winner"]) / len([item for item in evaluation_data if item[f"llmasjudge_{base_data_name}_morphology_winner"] != None])
        overall_word_order_win_rate = sum(1 for i, item in enumerate(evaluation_data) if item[f"llmasjudge_{base_data_name}_word_order_winner"]) / len([item for item in evaluation_data if item[f"llmasjudge_{base_data_name}_word_order_winner"] != None])
        overall_overall_win_rate = sum(1 for i, item in enumerate(evaluation_data) if item[f"llmasjudge_{base_data_name}_overall_winner"]) / len([item for item in evaluation_data if item[f"llmasjudge_{base_data_name}_overall_winner"] != None])
        overall_scores = {
            f"llmasjudge_{base_data_name}_semantics_win_rate": overall_semantics_win_rate,
            f"llmasjudge_{base_data_name}_morphology_win_rate": overall_morphology_win_rate,
            f"llmasjudge_{base_data_name}_word_order_win_rate": overall_word_order_win_rate,
            f"llmasjudge_{base_data_name}_overall_win_rate": overall_overall_win_rate,
        }
        return evaluation_data, overall_scores

    
    def _validate_and_parse_response_md_win_rate_separate(self, response: str, criterion: str) -> Tuple[List[str], int]:
        '''
        Validate and parse the response for MD win rate.
        '''
        # Valid response should be a JSON string of the specified format
        no_valid_response = False
        try:
            json.loads(response)
        except:
            print(f"Invalid JSON string: {response}")
            no_valid_response = True
            return no_valid_response, {}
        output = json.loads(response)
        if criterion == "word_order":
            keys = ["word_order_reasoning", "word_order_winner"]
        elif criterion == "overall":
            keys = ["overall_reasoning", "overall_winner"]
        else:
            raise ValueError(f"Invalid criterion: {criterion}")
        for key in keys:
            if key not in output:
                no_valid_response = True
            if "winner" in key and output[key] not in ["First", "Second"]:
                no_valid_response = True
        if no_valid_response:
            return no_valid_response, {}
        return no_valid_response, output
    
    def _evaluate_md_win_rate_separate(self, base_filepath: Union[str, List[Dict[str, Any]]], eval_filepath: Union[str, List[Dict[str, Any]]], base_data_name:str = "base") -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
        '''
        Evaluate the multidimensional win rate of outputs from eval_filepath against outputs from base_filepath. Make separate API calls for each criterion.
        '''
        if not isinstance(base_filepath, str):
            base_data = base_filepath
        else:
            with open(base_filepath, 'r', encoding='utf-8') as f:
                base_data = json.load(f)

        if not isinstance(eval_filepath, str):
            evaluation_data = eval_filepath
        else:
            with open(eval_filepath, 'r', encoding='utf-8') as f:
                evaluation_data = json.load(f)

        base_outputs = [item["output"] for item in base_data]
        eval_outputs = [item["output"] for item in evaluation_data]

        prompt_word_order = '''You will be given a reference text, and two candidate translations. Your task is to identify the better candidate, based on word order in the target language *regardless of meaning/adequacy*. Word order refers to the natural ordering of words and clauses in a sentence, depending on the syntax of the target language. Evaluate the two candidates based on this even if they are incorrect and flawed translations. 
        First, output your reasoning for your choice as a 1-sentence rationale.
        Then output "First" if the first candidate is better, and "Second" if the second candidate is better. Please decide on a definite winner; ties are not allowed.
        Output a JSON string of the following format:
        {{
            "word_order_reasoning": "<1-sentence rationale>",
            "word_order_winner": "<'First' or 'Second'>"
        }}
        DO NOT output any other text than the JSON string. Ensure that the JSON object is valid and complete, with only the options specified above. Ensure that all keys are present and that the values are valid.

        Reference:\n{reference}
        Candidate 1:\n{candidate1}
        Candidate 2:\n{candidate2}
        Output:
        '''

        prompt_general = '''You will be given an input, a reference text, and two candidate translations. Your task is to identify the better overall candidate taking into account how well the meaning is conveyed as well as grammaticality and fluency.
        First, output your reasoning for your choice as *short* 1-sentence rationale.
        Then output "First" if the first candidate is better, and "Second" if the second candidate is better. Please decide on a definite winner; ties are not allowed.
        Output a JSON string of the following format:
        {{
            "overall_reasoning":<1-sentence reasoning>,
            "overall_winner": "<'First' or 'Second'>"
        }}
        DO NOT output any other text than the JSON string. Ensure that the JSON string is valid and complete, with only the options specified above. Ensure that all keys are present and that the values are valid.

        Input:\n{input}
        Reference:\n{reference}
        Candidate 1:\n{candidate1}
        Candidate 2:\n{candidate2}
        Output:
        '''

        # Random order the order or the base and eval output to show to the LLM
        position_of_eval = [random.choice([0, 1]) for _ in range(len(evaluation_data))]
        prompts_word_order = []
        prompts_general = []
        for i, item in enumerate(evaluation_data):
            if eval_outputs[i] == "" or base_outputs[i] == "":
                prompts_word_order.append(None)
                prompts_general.append(None)
                continue
            if position_of_eval[i] == 0:
                prompts_word_order.append(prompt_word_order.format(reference=item["reference"], candidate1=eval_outputs[i], candidate2=base_outputs[i]))
                prompts_general.append(prompt_general.format(input=item["input"], reference=item["reference"], candidate1=eval_outputs[i], candidate2=base_outputs[i]))
            else:
                prompts_word_order.append(prompt_word_order.format(reference=item["reference"], candidate1=base_outputs[i], candidate2=eval_outputs[i]))
                prompts_general.append(prompt_general.format(input=item["input"], reference=item["reference"], candidate1=base_outputs[i], candidate2=eval_outputs[i]))
        # prompts = [prompt.format(input=item["input"], reference=item["reference"], candidate1=base_outputs[i], candidate2=eval_outputs[i]) for i, item in enumerate(evaluation_data)]

        # responses = self.llm_object.generate(prompts)
        responses_word_order = []
        responses_general = []
        for prompt_word_order, prompt_general in zip(prompts_word_order, prompts_general):
            if prompt_word_order is not None and prompt_general is not None:
                response_word_order = self.llm_object.generate([prompt_word_order])[0]
                response_general = self.llm_object.generate([prompt_general])[0]
                # response_word_order = "{\"word_order_reasoning_spans\": \"f\", \"word_order_winner\": \"First\"}"
                # response_general = "{\"overall_reasoning\": \"The first candidate is better because it is more fluent and natural.\", \"overall_winner\": \"First\"}"
                responses_word_order.append(response_word_order)
                responses_general.append(response_general)
            else:
                responses_word_order.append(None)
                responses_general.append(None)

        index_key_map = {0: "First", 1: "Second"} # If position of eval is 0, then we win if answer is "First", else "Second"

        for idx, (response_word_order, response_general) in enumerate(zip(responses_word_order, responses_general)):

            # Debugging
            print(f"Base output: {base_outputs[idx]}")
            print(f"Eval output: {eval_outputs[idx]}")
            print(f"Position of eval: {position_of_eval[idx]}")
            print(f"Response word order: {response_word_order}")
            print(f"Response general: {response_general}")

            if response_word_order is None or response_general is None:
                no_valid_response = True
            else:
                no_valid_response1, output_word_order = self._validate_and_parse_response_md_win_rate_separate(response_word_order, "word_order")
                no_valid_response2, output_general = self._validate_and_parse_response_md_win_rate_separate(response_general, "overall")
                no_valid_response = no_valid_response1 or no_valid_response2
                output = {**output_word_order, **output_general} if not no_valid_response else {}
            for key in output:
                if no_valid_response:
                    evaluation_data[idx][f"llmasjudge_{base_data_name}_{key}"] = None
                    continue

                if "winner" in key:
                    evaluation_data[idx][f"llmasjudge_{base_data_name}_{key}"] = index_key_map[position_of_eval[idx]] == output[key]
                    print(f"Key: {key}")
                    print(f"Winner: {index_key_map[position_of_eval[idx]] == output[key]}")
                else:
                    print(f"Key: {key}")
                    print(f"Output: {output[key]}")
                    evaluation_data[idx][f"llmasjudge_{base_data_name}_{key}"] = output[key]

            print("--------------------------------")

        # Win rate is the number of times the eval candidate is the winner. We take the order of the base and eval output into account.
        overall_word_order_win_rate = sum(1 for i, item in enumerate(evaluation_data) if item[f"llmasjudge_{base_data_name}_word_order_winner"] is True) / len([item for item in evaluation_data if item[f"llmasjudge_{base_data_name}_word_order_winner"] is not None])
        overall_overall_win_rate = sum(1 for i, item in enumerate(evaluation_data) if item[f"llmasjudge_{base_data_name}_overall_winner"] is True) / len([item for item in evaluation_data if item[f"llmasjudge_{base_data_name}_overall_winner"] is not None])
        overall_scores = {
            f"llmasjudge_{base_data_name}_word_order_win_rate": overall_word_order_win_rate,
            f"llmasjudge_{base_data_name}_overall_win_rate": overall_overall_win_rate,
        }
        return evaluation_data, overall_scores

# This is the prompt in the AutoMQM paper.
# Based on the given source and reference, identify the major and minor errors in this
# translation. Note that Major errors refer to actual translation or grammatical errors,
# and Minor errors refer to smaller imperfections, and purely subjective opinions about
# the translation.
# {src_lang} source: "{source}"
# {tgt_lang} human reference: "{reference}"
# {tgt_lang} translation: "{candidate}"

    