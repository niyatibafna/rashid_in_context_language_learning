# Run some lang_info experiments
HOME_DIR="/weka/home/nbafna1/projects/llm_language_learning"
#HOME_DIR="/mounts/Users/cisintern/soheunshim/projects/llm_language_learning"

language="hin_Deva"
task_name="mcqmmluprox"
direction="comprehension"
max_new_tokens=256
num_examples=200
batch_size=1
prompt_builder_config_file="${HOME_DIR}/experiments/configs_exps/lang_info.json"
# model_key="llama"
model_key="gpt-5.1"
use_cipher=True

output_dir_all="${HOME_DIR}/task_outputs/lang_info_${task_name}/${model_key}_dir-${direction}_samples-${num_examples}"
mkdir -p ${output_dir_all}
echo "Output directory: ${output_dir_all}"

exp_ids=("B0" "E0" "E1a" "E1" "E2a" "E2" "E3" "E4" "E9")
for exp_id in "${exp_ids[@]}"; do
    exp_name="lang-${language}_ps-lang_info_exp-${exp_id}"
    output_file="${output_dir_all}/${exp_name}/output.json"
    results_dir="${output_dir_all}/${exp_name}/results"
    mkdir -p ${results_dir}

    echo "--------------------------------"
    echo "Running experiment: ${exp_name}"
    echo "Output file: ${output_file}"
    echo "Results directory: ${results_dir}"
    echo "--------------------------------"

    python ${HOME_DIR}/experiments/pipeline_task.py \
    --language="${language}" \
    --task_name="${task_name}" \
    --direction="${direction}" \
    --max_new_tokens="${max_new_tokens}" \
    --num_examples="${num_examples}" \
    --batch_size="${batch_size}" \
    --prompt_builder_config_file="${prompt_builder_config_file}" \
    --prompt_builder_config_id="${exp_id}" \
    --use_cipher="${use_cipher}" \
    --model_key="${model_key}" \
    --output_file="${output_file}" \
    --results_dir="${results_dir}" > output_${model_key}.log
done