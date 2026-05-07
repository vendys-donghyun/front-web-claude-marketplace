# pr-workflow

PR 생성/스테이지 리뷰 자동화 플러그인

## 제공 skill

| 호출 | 역할 |
|---|---|
| `/pr-workflow:pr-create` | 브랜치 변경을 분석해 `[<type>/<TICKET>] <요약>` 제목과 **AS-IS / TO-BE 본문**을 생성하고 `gh pr create --web --base develop`으로 브라우저에 PR 생성 페이지를 띄움.(즉시 PR 생성하지 않음) |
| `/pr-workflow:stage-review` | `git diff --cached`에 대해 (A) 보안/위생 — console 로그, TODO/FIXME, 시크릿, .env, 외부 도메인 — 과 (B) 코드 리뷰 — **재사용 가능한 기존 로직 탐지 / 코드 효율 / 리렌더링 최적화**를 최우선으로, 그 외 React·JS·TS 안티패턴까지 — 를 함께 검사하고 리포트만 출력. 자동 수정 없음 |

## 의존성

- `gh` CLI 설치 + `gh auth login` 완료
- `git`

## pr-create 규칙

### 소스 브랜치 차단
`main`, `master`, `develop`, `release` / `release/*` / `release-*` 에서는 PR 생성 차단. 작업 브랜치(`feature/*`, `fix/*` 등)에서만 호출.

### 타깃 브랜치 = `develop` 고정
default branch 자동 감지를 무시하고 항상 `develop`으로 PR.

### 제목 형식
`[<type>/<TICKET>] <한글 요약>`

브랜치명은 `<type>/<TICKET>` 형태만 존재 (slug 없음). 한글 요약은 커밋 메시지에서 도출.

- `<type>`: 브랜치명 첫 슬래시 앞 토큰 (`feature`, `fix`, ...)
- `<TICKET>`: 브랜치명 `/` 뒤, 정규식 `[A-Z][A-Z0-9]+-\d+` (`PROD-00000`)
- `<한글 요약>`: **커밋 메시지 1순위, diff 2순위**로 도출 (한글 12~20자)
- type 또는 TICKET 누락 시 사용자 확인 후 진행

### 본문 포맷 — AS-IS / TO-BE (통합 1쌍)

수정사항을 **변경 의도 단위**로 묶되, 본문에는 **AS-IS 1개 / TO-BE 1개** 섹션으로 통합. 항목별 서브 헤더 없이 bullet 순서로 매칭.

```markdown
## 요약
- "왜"

## 변경사항

**AS-IS**
- 이전 동작 1
- 이전 동작 2

**TO-BE**
- 이번 PR 후 동작 1
- 이번 PR 후 동작 2

## 테스트 계획
- [ ] ...
```

## 주의사항

- `gh pr create`에 **`--fill` 절대 금지** (title/body 무시됨, cli/cli#10527)
- Assignee/Reviewer/Label은 사용자가 PR 페이지에서 직접 선택 (자동 추가 안 함)
- 시크릿이 의심되는 diff 본문은 PR body에 포함하지 않음

## 디렉터리 구조

```
plugins/pr-workflow/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   ├── pr-create/
│   │   └── SKILL.md
│   └── stage-review/
│       └── SKILL.md
└── README.md
```
