#!/bin/bash

# 引数でパスを受け取る
DATASET_PATH=$1

# Dockerコンテナを起動
docker run --gpus all -d --rm --name ocr_cli_runner --shm-size=256m -v ${DATASET_PATH}:/root/tmpdir/ -i ocr-v2-cli-py38:latest

# コンテナ内でコマンドを実行
docker exec -it ocr_cli_runner bash -c "python /root/ocr_cli/main.py infer /root/tmpdir/ /root/tmpdir/result -s s -x -p 2..3"

# コンテナを停止して削除
docker stop ocr_cli_runner
