'''
This file contains a class TaskData that loads task data for different tasks.
It downloads the data if necessary from HF, or loads it locally.
It standardizes all task data into the following format:
A list of dictionaries, where each dictionary contains the following keys:
- "input": The input text for the task.
- "output": The output text for the task.
- "metadata": A dictionary containing any additional metadata for the task.

'''

from datasets import load_dataset
from .utils.lang_codes import LANGS
from typing import List, Dict, Any, Optional
from collections import Counter
import random
random.seed(42)

class TaskData:
    def __init__(self, task_name: str, language: str, data_dir: str = "data"):
        self.task_name = task_name
        self.language = language
        self.data_dir = data_dir
        self.data: Optional[List[Dict[str, Any]]] = None

        load_data_methods = {
            "mtfloresplus": self._load_mtfloresplus_data,
            "mtwmtpp": self._load_wmtpp_data,
            "mcqmmluprox": self._load_mmlu_prox_data,
            "xnli": self._load_xnli_data,
            "xstorycloze": self._load_xstory_cloze_data,
        }
        if task_name not in load_data_methods:
            raise ValueError(f"Task {task_name} not supported")
        self.load_data_method = load_data_methods[task_name]


    def _load_mtfloresplus_data(self, direction = "comprehension",split: str = "dev", num_examples: int = None) -> List[Dict[str, Any]]:
        '''Load data from the MT-FloresPlus dataset from HF and format
        
        Args:
            split: Dataset split to load ({"dev", "dev-exemplars", "test"}). If num_examples is provided, we will return num_examples examples.
            direction: Direction of the task (default: "comprehension"). Can be "comprehension" or "generation".
        
        Returns:
            List of dictionaries with "input", "output", and "metadata" keys
        '''
        # Load the MT-FloresPlus dataset from HuggingFace
        split_to_load = "dev" if "dev" in split else "devtest"
        lang_dataset = load_dataset("openlanguagedata/flores_plus", self.language, split=split_to_load)
        eng_dataset = load_dataset("openlanguagedata/flores_plus", "eng_Latn", split=split_to_load)
        
        # Convert to lists and create ID mappings
        lang_list = [(x["id"], x["text"]) for x in lang_dataset]
        eng_list = [(x["id"], x["text"]) for x in eng_dataset]
        
        # Get common IDs
        lang_ids = {item[0] for item in lang_list}
        eng_ids = {item[0] for item in eng_list}
        common_ids = lang_ids & eng_ids
        
        # Filter to only common IDs and sort
        lang_dataset = sorted([item for item in lang_list if item[0] in common_ids], key=lambda x: x[0])
        eng_dataset = sorted([item for item in eng_list if item[0] in common_ids], key=lambda x: x[0])
        
        assert len(lang_dataset) == len(eng_dataset)
        data = []
        for lang_item, eng_item in zip(lang_dataset, eng_dataset):
            if direction == "comprehension":
                data.append({"input": lang_item[1], "output": eng_item[1], "metadata": {"id": lang_item[0]}})
            elif direction == "generation":
                data.append({"input": eng_item[1], "output": lang_item[1], "metadata": {"id": eng_item[0]}})
            else:
                raise ValueError(f"Direction {direction} not supported")

        if split == "dev-exemplars": # In this case we have loaded the dev set
            return data[:300][:num_examples] if num_examples is not None else data[:300] # Keep 300 for choosing exemplars
        elif split == "dev": # In this case we have loaded the dev set
            return data[300:][:num_examples] if num_examples is not None else data[300:] # Keep remaining for dev analysis
        elif split == "test": # In this case we have loaded the devtest set, we return as is
            return data[:num_examples] if num_examples is not None else data


    def _load_wmtpp_data(self, direction = "comprehension", split: str = "dev", num_examples: int = None) -> List[Dict[str, Any]]:
        '''Load data from the WMT-PP dataset from HF and format. For dev, we will return examples split equally across domains.
        
        Args:
            split: Dataset split to load (default: "dev"). If num_examples is provided, we will return num_examples examples.
            direction: Direction of the task (default: "comprehension"). Can be "comprehension" or "generation".
        '''
        if split =="dev" and num_examples is not None and num_examples > 300:
            raise ValueError(f"num_examples must be less than or equal to 300 for dev split")
        if split == "dev-exemplars" and num_examples is not None and num_examples > 300:
            raise ValueError(f"num_examples must be less than or equal to 300 for dev-exemplars split")
        
        wmtpp_code = LANGS[self.language]["wmtpp_code"]
        dataset = load_dataset("google/wmt24pp", f"en-{wmtpp_code}")["train"]
        data = []
        for item in dataset:
            if item["is_bad_source"]:
                continue
            if direction == "comprehension":
                data.append({"input": item["target"], "output": item["source"], "metadata": {"domain": item["domain"], "id": item["segment_id"]}}) # English is stored in item["source"]
            elif direction == "generation":
                data.append({"input": item["source"], "output": item["target"], "metadata": {"domain": item["domain"], "id": item["segment_id"]}})
            else:
                raise ValueError(f"Direction {direction} not supported")
        
        # Let's bucket by domain
        domains = Counter(item["metadata"]["domain"] for item in data)
        domains_list = list(domains.keys())
        domains_list.sort(key=lambda x: domains[x], reverse=True)
        data_bucketed = {domain: [] for domain in domains_list}
        for item in data:
            data_bucketed[item["metadata"]["domain"]].append(item)

        rng = random.Random(42)
        for domain in domains_list:
            rng.shuffle(data_bucketed[domain])

        # Next, we will split the data into dev, dev-exemplars, and test sets, containing 300, 300, and remaining examples respectively.
        # If num_examples is provided, we will return num_examples examples.
        # However, just for dev subset, we want to distribute the examples evenly across domains.


        data_dev = []
        remaining_data = []
        each_domain_size = 300 // len(domains_list)
        each_domain_samples = each_domain_size if num_examples is None else num_examples // len(domains_list)


        for domain in domains_list:
            data_dev.extend(data_bucketed[domain][:each_domain_samples])
            remaining_data.extend(data_bucketed[domain][each_domain_size:]) # takes fixed remaining samples regardless of num_examples

        rng.shuffle(remaining_data)
        if split == "dev": # Keep first 300 for dev analysis
            return data_dev
        elif split == "dev-exemplars": # Keep next 300 for choosing exemplars
            return remaining_data[:300][:num_examples] if num_examples is not None else remaining_data[:300]
        elif split == "test": # Keep remaining for test analysis
            return remaining_data[300:][:num_examples] if num_examples is not None else remaining_data[300:]
        elif split == "all": # Return all data
            return data[:num_examples] if num_examples is not None else data
    
    def _load_mmlu_prox_data(self, direction="comprehension", split: str = "dev", num_examples: int = None) -> List[Dict[str, Any]]:
        if direction != "comprehension":
            raise ValueError("Only comprehension direction supported.")

        if split in {"dev", "dev-exemplars"} and num_examples is not None and num_examples > 300:
            raise ValueError(f"num_examples must be <= 300 for split={split}")

        lang_code = LANGS[self.language]["gtrans_code"]
        ds = load_dataset("li-lab/MMLU-ProX", lang_code, split="test")

        data = []
        for example in ds:
            options = [example[f"option_{i}"] for i in range(10)]

            prompt = example["question"].strip() + "\n"
            for idx, opt in enumerate(options):
                idx += 1 # to start from 1 for readability
                prompt += f"{idx}) {opt}\n"

            label_idx = str(int(example["answer_index"]) + 1) # to start from 1 for readability and match option idx

            data.append({
                "input": prompt,
                "output": label_idx, 
                "metadata": {
                    "options": options,
                    "answer_index": label_idx,
                }
            })


        rng = random.Random(42)
        rng.shuffle(data)

        data_dev = data[:300]
        data_dev_exemplars = data[300:600]
        data_test = data[600:]

        if split == "dev":
            return data_dev[:num_examples] if num_examples is not None else data_dev
        elif split == "dev-exemplars":
            return (
                data_dev_exemplars[:num_examples]
                if num_examples is not None
                else data_dev_exemplars
            )
        elif split == "test":
            return data_test[:num_examples] if num_examples is not None else data_test
        elif split == "all":
            return data[:num_examples] if num_examples is not None else data
        else:
            raise ValueError(f"Split {split} not supported")
    
    def _load_xnli_data(self, direction: str = "comprehension", split: str = "dev", num_examples: int = None,) -> List[Dict[str, Any]]:
        if direction != "comprehension":
            raise ValueError("XNLI only supports comprehension direction.")

        if split in {"dev", "dev-exemplars"} and num_examples is not None and num_examples > 300:
            raise ValueError(f"num_examples must be <= 300 for split={split}")

        xnli_lang = LANGS[self.language]["gtrans_code"]

        raw_data = load_dataset("xnli", xnli_lang, split="test")

        data = []
        for ex in raw_data:
            data.append({
                "input": "Premise: " + "<" + ex["premise"] + ">" + "\n" + "Hypothesis: " +  "<" + ex["hypothesis"] + ">",
                "output": str(ex["label"]),
                "metadata": {
                    "premise": ex["premise"],
                    "hypothesis": ex["hypothesis"],
                    "label": ex["label"],
                },
            })

        rng = random.Random(42)
        rng.shuffle(data)

        data_dev = data[:300]
        data_dev_exemplars = data[300:600]
        data_test = data[600:]

        if split == "dev":
            return data_dev[:num_examples] if num_examples is not None else data_dev
        elif split == "dev-exemplars":
            return (
                data_dev_exemplars[:num_examples]
                if num_examples is not None
                else data_dev_exemplars
            )
        elif split == "test":
            return data_test[:num_examples] if num_examples is not None else data_test
        elif split == "all":
            return data[:num_examples] if num_examples is not None else data
        else:
            raise ValueError(f"Split {split} not supported")
    
    def _load_xstory_cloze_data(self, direction: str = "comprehension", split: str = "dev", num_examples: int = None) -> List[Dict[str, Any]]:
        """
        Load data from the XStoryCloze dataset (HF: juletxara/xstory_cloze).

        Task format:
        - Input: story context + two candidate endings
        - Output: correct ending index ("1" or "2")
        """

        if direction != "comprehension":
            raise ValueError("XStoryCloze only supports comprehension direction.")

        if split in {"dev", "dev-exemplars"} and num_examples is not None and num_examples > 300:
            raise ValueError(f"num_examples must be <= 300 for split={split}")

        lang_code = LANGS[self.language]["gtrans_code"]

        raw_data = load_dataset("juletxara/xstory_cloze", lang_code, split="eval")

        data = []
        for ex in raw_data:
            context = " ".join(
                [
                    ex["input_sentence_1"],
                    ex["input_sentence_2"],
                    ex["input_sentence_3"],
                    ex["input_sentence_4"],
                ]
            ).strip()

            prompt = (
                f"Story:\n{context}\n\n"
                f"1) {ex['sentence_quiz1']}\n"
                f"2) {ex['sentence_quiz2']}"
            )


            data.append(
                {
                    "input": prompt,
                    "output": str(ex["answer_right_ending"]),
                    "metadata": {
                        "ending_1": ex["sentence_quiz1"],
                        "ending_2": ex["sentence_quiz2"],
                    },
                }
            )

        rng = random.Random(42)
        rng.shuffle(data)

        data_dev = data[:300]
        data_dev_exemplars = data[300:600]
        data_test = data[600:]

        if split == "dev":
            return data_dev[:num_examples] if num_examples is not None else data_dev
        elif split == "dev-exemplars":
            return (
                data_dev_exemplars[:num_examples]
                if num_examples is not None
                else data_dev_exemplars
            )
        elif split == "test":
            return data_test[:num_examples] if num_examples is not None else data_test
        elif split == "all":
            return data[:num_examples] if num_examples is not None else data
        else:
            raise ValueError(f"Split {split} not supported")



# Sample usage
if __name__ == "__main__":
    # task_data = TaskData(task_name="mtfloresplus", language="hin_Deva")
    # task_data = TaskData(task_name="mcqmmluprox", language="fra_Latn")
    task_data = TaskData(task_name="mtwmtpp", language="hin_Deva")
    data = task_data.load_data_method(direction="generation", split="dev")
    print(len(data))
    print(data[0]["input"])
    print(data[0]["output"])
    print(data[0]["metadata"])
