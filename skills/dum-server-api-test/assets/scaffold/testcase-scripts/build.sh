#!/bin/bash
# 编译某个 api-test 工程为可执行的 apitest.test（不实际跑用例）。
# 用法: build.sh <服务目录>    如 build.sh <service>-api-test
set -e
export GO111MODULE=on
DIR="$1"
if [[ -z "$DIR" ]]; then echo "用法: build.sh <服务目录>（如 <service>-api-test）"; exit 1; fi
cd "$(dirname "$0")/$DIR"
go test -c -o apitest.test
echo "built: $DIR/apitest.test"
