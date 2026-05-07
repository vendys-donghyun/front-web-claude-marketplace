---
name: pr-create
description: 현재 브랜치 diff/커밋을 분석해 `[<type>/<TICKET>] <요약>` 형식 PR 제목과 AS-IS/TO-BE 형식 본문을 생성하고 `gh pr create --web --title --body`로 develop 타깃 PR 생성 페이지를 브라우저에 엽니다. 사용자가 직접 검토 후 "Create pull request" 클릭.
---

# pr-create

스테이지가 아닌 **브랜치 전체 변경**을 `develop` 대비 분석해 PR 페이지를 브라우저에 띄운다. 즉시 PR을 만들지 않는다.

## 절차

### 1. 소스 브랜치 검증 (차단 규칙)

`git rev-parse --abbrev-ref HEAD` 결과가 아래에 해당하면 **즉시 중단**하고 사용자에게 작업 브랜치로 이동을 안내한다.

| 차단 패턴 | 예 |
|---|---|
| `main`, `master`, `develop` (정확히 일치) | `main`, `develop` |
| `release` 또는 `release/...` 또는 `release-...` | `release/2026-01`, `release-v2` |

차단 메시지 예:
```
[pr-create] 차단: 현재 브랜치 'develop'에서는 PR을 생성할 수 없습니다.
작업 브랜치(feature/* 또는 fix/*)로 이동 후 다시 호출해주세요.
```

### 2. 타깃(base) 브랜치 = `develop` 고정

`gh repo view`로 default branch를 확인하지 않는다. **항상 `develop`** 으로 PR을 만든다.

origin에 develop이 없으면 한 번만 사용자에게 확인하고 중단.
```bash
git ls-remote --heads origin develop
```

### 3. 브랜치명에서 type · TICKET 파싱

브랜치명은 **`<type>/<TICKET>` 형태만 존재**한다 (slug 없음).

```
예: feature/PROD-00000
    fix/PROD-00000
```

- **type**: 브랜치명에서 첫 `/` 앞 토큰 (`feature`, `fix`, `feat`, `bugfix`, `hotfix`, `chore`, `refactor` 등). 표시는 브랜치명 그대로 사용.
- **TICKET**: `/` 뒤 부분, 정규식 `[A-Z][A-Z0-9]+-\d+` 매치 (예: `PROD-00000`).
- **파싱 실패 시** (type 없음 또는 ticket 없음): 사용자에게 한 번 확인. 추측해서 진행하지 않는다.

브랜치명에는 **작업 내용(한글) 정보가 없다**. 한글 요약은 6단계에서 커밋 메시지/diff로 도출한다.

### 4. 변경 정보 수집

```bash
git log --oneline develop..HEAD                  # 커밋 목록
git diff develop...HEAD --stat                   # 파일별 라인 수
git diff develop...HEAD                          # 본문 (필요시 부분)
```

### 5. 변경 항목 통합

여러 커밋·파일 단위 변경을 **"무엇을 바꾸는 변경이냐"** 기준으로 묶는다. 같은 의도의 변경은 한 항목으로 합친다.

통합된 항목들은 **각각 AS-IS bullet 1줄 + TO-BE bullet 1줄**로 표현한다 (항목별 헤더 없이 한 곳에 모음). AS-IS와 TO-BE의 bullet 순서를 맞춰 같은 항목이 같은 인덱스에 오도록 한다.

### 6. PR 제목 생성

형식:
```
[<type>/<TICKET>] <한글 요약>
```

예:
- `[feature/PROD-00000] 기능 추가`
- `[fix/PROD-00000] 기능 오류 수정`

규칙:
- `<한글 요약>`은 **커밋 메시지를 1순위, diff 내용을 2순위**로 도출한다. 브랜치명은 type/TICKET만 들어있어 요약 정보가 없으므로 의존하지 않는다.
- 커밋 메시지가 한 줄이면 그 톤을 그대로 따르고, 여러 커밋이면 공통 의도를 한 문장으로 요약.
- 길이 제한: 전체 70자 이하 (브래킷 포함). 한글 요약은 보통 12~20자.
- `[type/TICKET]` 부분은 대괄호·슬래시 형태 그대로 유지.

### 7. PR 본문 생성

프로젝트에 PR 템플릿이 있으면 그것 우선. 없으면 아래 템플릿 사용.

```markdown
## 요약
- 1-3 bullet, "왜" 위주 (배경/이슈/목적)

## 변경사항

**AS-IS**
- 이전 동작/구조 1 (항목 A)
- 이전 동작/구조 2 (항목 B)
- 이전 동작/구조 3 (항목 C)

**TO-BE**
- 이번 PR 후 동작/구조 1 (항목 A)
- 이번 PR 후 동작/구조 2 (항목 B)
- 이번 PR 후 동작/구조 3 (항목 C)
```

작성 원칙:
- 항목은 **변경 의도** 단위로 묶는다 (커밋 1:1 매핑 아님)
- AS-IS와 TO-BE는 각 1개 섹션, 항목별 서브 헤더 없음 — bullet 순서로 매칭
- AS-IS는 "현재 코드는 X였다" 같은 사실 진술
- TO-BE는 "이제 Y로 동작한다" — 구현 디테일이 아니라 **관찰 가능한 동작/구조**

### 8. origin 업스트림 확인

`gh pr create`는 브랜치가 **origin에 push된 상태**여야 동작한다. 호출 전 확인:

```bash
git ls-remote --heads origin <branch>
```

결과가 비어 있으면 **PR 생성 진행 X**. 사용자에게 안내:

```
[pr-create] 현재 브랜치 '<branch>'가 origin에 없습니다.
먼저 push 해주세요:
  git push -u origin <branch>
push 후 다시 호출하시면 됩니다.
```

자동으로 `git push` 를 실행하지 않는다 (사용자 의도 확인 필요). 사용자가 명시적으로 진행 요청하면 그때 push.

추가 점검: 로컬이 origin보다 앞서있다면(unpushed commits) 표시:
```bash
git rev-list --count origin/<branch>..HEAD
```
0이 아니면 "로컬에 push 안 된 커밋 N개 있습니다. push 후 진행 권장" 안내.

### 9. 브라우저에서 PR 페이지 열기

```bash
gh pr create --web --base develop --title "<생성한 title>" --body "<생성한 body>"
```

`--base develop` 명시. PR 생성 **직전** 페이지를 브라우저에 띄운다. 즉시 생성하지 않는다.

### 10. 폴백 (gh가 없거나 실패)

URL 직접 구성 후 `open` (macOS):
```
https://github.com/<owner>/<repo>/compare/develop...<head>?quick_pull=1&title=<urlencoded>&body=<urlencoded>
```

## 절대 하지 말 것

- ❌ `main`/`master`/`develop`/`release*` 브랜치에서 PR 생성 진행 (1단계에서 차단)
- ❌ 타깃 브랜치를 `main`이나 default branch로 자동 설정 — **항상 `develop`**
- ❌ 브랜치명에 type·TICKET이 없는데 추측해서 제목 만들기 — 사용자에게 확인
- ❌ `[type/TICKET]` 부분에 한글 요약을 영어로 직역해서 넣기 — diff 기반으로 한글 작성
- ❌ `--fill` 사용 (title/body가 무시됨, cli/cli#10527)
- ❌ `--assignee` / `--reviewer` / `--label` 추가 — 사용자가 페이지에서 직접 선택
- ❌ `--web` 빼고 `gh pr create` 실행 (즉시 PR 생성 금지)
- ❌ 시크릿이 들어간 diff 본문을 PR body에 포함 (마스킹/제외)
- ❌ 변경 항목을 커밋 단위로 1:1 나열 (의도 단위로 묶기)
- ❌ origin 업스트림 확인 없이 `gh pr create` 실행 (8단계 필수)
- ❌ 사용자 동의 없이 `git push` 자동 실행

## 출력 (Claude → 사용자)

명령 실행 전 한 번:
```
[pr-create]
- base: develop
- head: <branch>
- type: <feature|fix|...>  ticket: <PROD-XXXXX>
- 커밋 N개, 파일 M개 변경
- 변경 항목 K개로 통합

제목: "[<type>/<TICKET>] <요약>"
본문 미리보기:
<body>

→ gh pr create --web --base develop 으로 브라우저를 엽니다.
```
