#!/bin/bash

# 引数でパスを受け取る
INPUT_PATH=$1
OUTPUT_PATH=$2

INPUT_ABS_PATH=$(readlink -f "$INPUT_PATH")
OUTPUT_ABS_PATH=$(readlink -f "$OUTPUT_PATH")

# Dockerコンテナを起動
docker run --gpus all -d --rm --name annotation_runner --shm-size=256m -v ${INPUT_ABS_PATH}:/root/input_dir/ -v ${OUTPUT_ABS_PATH}:/root/output_dir/ -i ocr-v2-cli-py38:latest

# コンテナ内でコマンドを実行
docker exec -it annotation_runner bash -c "python /root/ocr_cli/proc_ndlocr.py /root/input_dir /root/output_dir -j"

# コンテナを停止して削除
docker stop annotation_runner
