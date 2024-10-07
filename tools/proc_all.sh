#!/bin/bash

SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
input_dir=$(readlink -f "$1")
output_dir=$(readlink -f "$2")

cd $SCRIPT_DIR

python3 proc_ndlocr.py $input_dir $output_dir
json_dir="${output_dir}/json"
easy_ocr_dir="${output_dir}/easyocr"
python3 proc_easyocr.py $input_dir $json_dir $easy_ocr_dir
result_dir="${output_dir}/latexocr"
python3 proc_latexocr.py $input_dir $easy_ocr_dir $result_dir 
