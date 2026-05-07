# security-base

벤디스 프론트엔드 공통 보안 정책 플러그인

## 무엇을 차단하는가

### 위험 bash 명령 (`PreToolUse:Bash`)

| 패턴 | 차단 | 허용 |
|---|---|---|
| `rm -rf <대상>` | 시스템 경로(`/usr`, `/etc`, ...), 홈(`~`, `$HOME`), 와일드카드(`*`), 상위 경로(`..`) | 상대 경로 (`rm -rf node_modules`, `rm -rf dist`) |
| `git push` | `--force`, `-f` | `--force-with-lease` |
| `git reset --hard` | 모두 | (없음) |
| `git commit/push --no-verify` | 모두 (pre-commit/push 훅 우회 금지) | (없음) |
| `curl ... \| sh`, `wget ... \| bash` | 원격 스크립트 직접 실행 | 단순 다운로드 (`curl url > file`) |
| `chmod 777` | `chmod 777`, `chmod -R 777`, `chmod 0777` | `chmod 644`, `chmod 755` 등 일반 권한 |
| `npm/pnpm/yarn publish` | 모두 (실수 publish 방지) | (없음) |

### 시크릿 파일 (`PreToolUse:Read\|Write\|Edit\|NotebookEdit`)

| 패턴 | 차단 | 허용 |
|---|---|---|
| `.env*` | `.env`, `.env.production`, `.env.development`, `.env.local` 등 | `.env.example`, `.env.sample`, `.env.template` |

## 권장 추가: `permissions.deny` (각 프로젝트 settings.json)

플러그인은 hook으로 차단하지만, **정책 가시성**과 **다중 방어선**을 위해 각 프로젝트 `.claude/settings.json`에 아래 deny 리스트를 함께 적용하는 것을 권장합니다.

```jsonc
{
  "permissions": {
    "deny": [
      "Bash(rm -rf /:*)",
      "Bash(rm -rf ~:*)",
      "Bash(rm -rf $HOME:*)",
      "Bash(git push --force:*)",
      "Bash(git push -f:*)",
      "Bash(git reset --hard:*)",
      "Bash(git commit --no-verify:*)",
      "Bash(git push --no-verify:*)",
      "Bash(chmod 777:*)",
      "Bash(npm publish:*)",
      "Bash(pnpm publish:*)",
      "Bash(yarn publish:*)",
      "Read(./.env)",
      "Read(./.env.*)",
      "Write(./.env)",
      "Write(./.env.*)",
      "Edit(./.env)",
      "Edit(./.env.*)"
    ]
  }
}
```

> Note: deny 리스트의 `.env.*`는 `.env.example`까지 막습니다. 템플릿 편집이 필요하면 deny 리스트에서 해당 항목을 빼고 hook 차단(템플릿 허용)에 의존하세요.

## 동작 검증 방법

플러그인 install 후 세션 재시작 → 다음을 시도:

```bash
# 차단되어야 함
rm -rf /
git push --force
git reset --hard HEAD~1
```

```text
# 차단되어야 함 (Read tool로 .env 열기)
.env 파일 보여줘
```

차단 시 stderr에 `[security-base] 차단된 ...` 메시지가 표시됩니다.

## 의존성

- `python3` (macOS/Linux 기본 탑재)
- 추가 패키지 없음

## 우회

Claude를 거치지 않고 직접 터미널에서 실행하면 차단되지 않습니다. 이 플러그인은 **AI 에이전트가 의도치 않게 위험한 작업을 수행하는 것**을 막기 위한 hook이며, 사용자의 직접 행동은 막지 않습니다.
