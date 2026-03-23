#!/usr/bin/env bash
# 便捷入口：自动设置 PYTHONPATH
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHONPATH="$SCRIPT_DIR/src" exec "$SCRIPT_DIR/.venv/bin/python" -m setri.cli "$@"
