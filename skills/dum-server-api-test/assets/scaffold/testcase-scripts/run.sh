#!/bin/bash
# 用法: run.sh <服务目录> <config.yml> [--module A,B] [--priority p0,p1] [--interface Name] [--list] [--run <regex>]
#   <服务目录>    如 <service>-api-test
#   --module      模块字母(逗号分隔)，如 A,B,K
#   --priority    优先级(逗号分隔) p0/p1/p2
#   --interface   按 @interface 注解匹配接口语义名
#   --list        只列出可选模块/优先级/接口，不跑
#   --run         直接指定 -test.run 正则(覆盖上面的拼装)
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

DIR=""
CONFIG=""
MODULES=""
PRIORITIES=""
IFACE=""
RAW_RUN=""
LIST=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --module)    MODULES="$2"; shift 2;;
    --priority)  PRIORITIES="$2"; shift 2;;
    --interface) IFACE="$2"; shift 2;;
    --run)       RAW_RUN="$2"; shift 2;;
    --list)      LIST=1; shift;;
    *)
      if [[ -z "$DIR" ]]; then DIR="$1"; shift
      elif [[ -z "$CONFIG" ]]; then CONFIG="$1"; shift
      else echo "unknown arg: $1"; exit 1; fi;;
  esac
done

if [[ -z "$DIR" ]]; then echo "错误：未指定服务目录（如 <service>-api-test）"; exit 1; fi

# 配置路径在 cd 前解析为绝对路径，避免 cd 进服务目录后相对路径失效
if [[ -n "$CONFIG" ]]; then CONFIG="$(cd "$(dirname "$CONFIG")" && pwd)/$(basename "$CONFIG")"; fi

cd "$SCRIPT_DIR/$DIR"

if [[ "$LIST" == "1" ]]; then
  echo "== 模块字母 =="; grep -rhoE '^func Test_[A-Z][0-9]+_' *_test.go | sed -E 's/^func Test_([A-Z])[0-9].*/\1/' | sort -u
  echo "== 优先级 =="; grep -rhoE '_P[0-9]_' *_test.go | tr -d '_' | sort -u
  echo "== 接口 =="; grep -rhoE '@interface:.*' *_test.go | sed 's/@interface://' | tr ',' '\n' | sed 's/^ *//;/^$/d' | sort -u
  exit 0
fi

if [[ -z "$CONFIG" ]]; then echo "错误：未指定配置文件路径（如 ./test.yml）"; exit 1; fi

# 构造 -test.run 正则
build_regex() {
  local mod_part=".*" pri_part=".*"
  if [[ -n "$MODULES" ]]; then mod_part="($(echo "$MODULES" | tr ',' '|'))"; fi
  if [[ -n "$PRIORITIES" ]]; then pri_part="($(echo "$PRIORITIES" | tr ',' '|' | tr 'a-z' 'A-Z'))"; fi
  echo "^Test_${mod_part}[0-9]+_${pri_part}_"
}

if [[ -n "$RAW_RUN" ]]; then
  RUN="$RAW_RUN"
elif [[ -n "$IFACE" ]]; then
  # 按 @interface 注解取对应函数名并 OR 拼接
  FUNCS=$(grep -A4 -E "@interface:.*${IFACE}" *_test.go | grep -oE 'Test_[A-Za-z0-9_]+' | sort -u | paste -sd '|' -)
  if [[ -z "$FUNCS" ]]; then echo "没有匹配 @interface=${IFACE} 的测试"; exit 1; fi
  RUN="^($FUNCS)$"
else
  RUN="$(build_regex)"
fi

echo "-test.run: $RUN"
if [[ -x ./apitest.test ]]; then
  echo "run: ./apitest.test (compiled)"
  ./apitest.test -test.v -test.run "$RUN" -c "$CONFIG"
else
  echo "run: go test (source)"
  go test -v -run "$RUN" -args -c "$CONFIG"
fi
