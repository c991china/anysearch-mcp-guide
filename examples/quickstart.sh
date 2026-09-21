#!/usr/bin/env bash
# 一键运行 AnySearch 最小客户端
# 用法：bash examples/quickstart.sh "你的查询"
set -euo pipefail
cd "$(dirname "$0")/.."
if [ -z "${ANYSEARCH_API_KEY:-}" ]; then
  echo "请先设置： export ANYSEARCH_API_KEY=as_sk_xxxx"
  exit 1
fi
python3 examples/anysearch_client.py "$@"
