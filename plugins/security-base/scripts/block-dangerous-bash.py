#!/usr/bin/env python3
"""PreToolUse:Bash — block dangerous commands.

Blocks: rm -rf to system/home/wildcard, git push --force / -f, git reset --hard.
Allows: rm -rf <relative-path>, git push --force-with-lease.
"""
import json
import re
import sys


def block(command: str, reason: str) -> None:
    sys.stderr.write(f"[security-base] 차단된 명령: {command}\n")
    sys.stderr.write(f"사유: {reason}\n")
    sys.stderr.write("정말 필요하면 직접 터미널에서 실행하세요.\n")
    sys.exit(2)


try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(0)

command = (data.get("tool_input") or {}).get("command", "")
if not command:
    sys.exit(0)

normalized = re.sub(r"\s+", " ", command).strip()

rm_rf = re.search(
    r"\brm\s+(-[a-zA-Z]*[rR][a-zA-Z]*[fF][a-zA-Z]*|-[a-zA-Z]*[fF][a-zA-Z]*[rR][a-zA-Z]*)\b",
    normalized,
)
if rm_rf:
    after = normalized[rm_rf.end():].strip()
    for token in after.split():
        if token.startswith("-"):
            continue
        if token in ("/", "~", "*", "..", "$HOME", "${HOME}"):
            block(command, f"rm -rf 위험 대상: {token}")
        if token.startswith("~/") or token.startswith("$HOME/") or token.startswith("${HOME}/"):
            block(command, f"rm -rf 홈 디렉터리 대상: {token}")
        if token.startswith("../"):
            block(command, f"rm -rf 상위 경로 대상: {token}")
        if re.match(
            r"^/(usr|etc|var|bin|sbin|System|Library|Applications|Users|opt|private|root)(/|$)",
            token,
        ):
            block(command, f"rm -rf 시스템 경로 대상: {token}")
        if token.startswith("/") and len(token) <= 4:
            block(command, f"rm -rf 루트 인접 경로 대상: {token}")

if re.search(r"\bgit\s+push\b", normalized):
    if re.search(r"\bgit\s+push\b[^;&|]*--force(?!-with-lease)(\s|=|$)", normalized):
        block(command, "git push --force 차단 (--force-with-lease 만 허용)")
    if re.search(r"\bgit\s+push\b[^;&|]*\s-[a-zA-Z]*f(\s|$|[a-zA-Z]+\s|[a-zA-Z]+$)", normalized):
        block(command, "git push -f 차단")

if re.search(r"\bgit\s+reset\b[^;&|]*--hard\b", normalized):
    block(command, "git reset --hard 차단")

sys.exit(0)
