#!/bin/bash
# 用法: run.sh <config.yml> [--module A,B] [--priority p0,p1] [--interface Name] [--list] [--run <regex>]
set -e

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
    *)           if [[ -z "$CONFIG" ]]; then CONFIG="$1"; shift; else echo "unknown arg: $1"; exit 1; fi;;
  esac
done

if [[ "$LIST" == "1" ]]; then
  echo "== 模块字母 =="; grep -rhoE '^func Test_[A-Z][0-9]+_' *_test.go | sed -E 's/^func Test_([A-Z])[0-9].*/\1/' | sort -u
  echo "== 优先级 =="; grep -rhoE '_P[0-9]_' *_test.go | tr -d '_' | sort -u
  echo "== 接口 =="; grep -rhoE '@interface:.*' *_test.go | sed 's/@interface://' | tr ',' '\n' | sed 's/^ *//;/^$/d' | sort -u
  exit 0
fi

if [[ -z "$CONFIG" ]]; then echo "错误：未指定配置文件路径"; exit 1; fi

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
go test -v -run "$RUN" -args -c "$CONFIG"
