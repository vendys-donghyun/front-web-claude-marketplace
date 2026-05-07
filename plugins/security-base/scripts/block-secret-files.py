#!/usr/bin/env python3
"""PreToolUse:Read|Write|Edit|NotebookEdit — block .env* files.

Blocks: .env, .env.production, .env.development, .env.local, ...
Allows: .env.example, .env.sample, .env.template (template files).
"""
import json
import os
import re
import sys


try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

tool_input = data.get("tool_input") or {}
file_path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
if not file_path:
    sys.exit(0)

filename = os.path.basename(file_path)

if re.fullmatch(r"\.env\.(example|sample|template)", filename):
    sys.exit(0)

if re.fullmatch(r"\.env(\..+)?", filename):
    sys.stderr.write(f"[security-base] 차단된 파일 접근: {file_path}\n")
    sys.stderr.write(".env* 파일은 시크릿이 포함될 수 있어 차단됩니다.\n")
    sys.stderr.write("템플릿(.env.example/.env.sample/.env.template)은 허용됩니다.\n")
    sys.exit(2)

sys.exit(0)
