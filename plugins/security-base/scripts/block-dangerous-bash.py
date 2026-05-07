#!/usr/bin/env python3
"""PreToolUse:Bash — block dangerous commands.

Blocks:
- rm -rf to system/home/wildcard/parent
- git push --force / -f
- git reset --hard
- git commit/push --no-verify
- curl|sh, wget|bash (remote script execution)
- chmod 777 (world-writable)
- npm/pnpm/yarn publish

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

if re.search(r"\bgit\s+(commit|push)\b[^;&|]*--no-verify\b", normalized):
    block(command, "git --no-verify 차단 (pre-commit/pre-push 훅 우회 금지)")

if re.search(r"\b(curl|wget|fetch)\b[^;&|]*\|\s*\b(sh|bash|zsh|ash|dash)\b", normalized):
    block(command, "원격 스크립트 직접 실행 차단 (curl|sh / wget|bash 패턴)")

if re.search(r"\bchmod\b[^;&|]*?\b0?777\b", normalized):
    block(command, "chmod 777 차단 (world-writable, 보안 악화)")

if re.search(r"\b(npm|pnpm|yarn)\s+publish\b", normalized):
    block(command, "package publish 차단 (실수로 공개 publish 방지)")

sys.exit(0)
