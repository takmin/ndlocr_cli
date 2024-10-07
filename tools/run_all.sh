#!/bin/bash

# 引数でパスを受け取る
INPUT_PATH=$1
OUTPUT_PATH=$2

# Dockerコンテナを起動
docker run --gpus all -d --rm --name annotation_runner --shm-size=256m -v ${INPUT_PATH}:/root/input_dir/ -v ${OUTPUT_PATH}:/root/output_dir/ -i ocr-v2-cli-py38:latest

# コンテナ内でコマンドを実行
docker exec -it annotation_runner bash -c "/root/ocr_cli/tools/proc_all.sh /root/input_dir /root/output_dir"

# コンテナを停止して削除
docker stop annotation_runner
