---
name: stage-review
description: 스테이지된 변경(`git diff --cached`)에서 (A) 보안/위생 점검 — console 로그, 신규 TODO/FIXME, 시크릿 패턴, .env 스테이징, 외부 도메인 — 과 (B) React/JS/TS 코드 리뷰 — **재사용 가능한 기존 로직 탐지 / 코드 효율 / 리렌더링 최적화**를 최우선으로, 그리고 일반 안티패턴·연산 최적화 — 를 검사하고 리포트만 출력. 자동 수정 금지.
---

# stage-review

`git diff --cached`만 검사. 워킹트리·이전 커밋 X. **리포트만, 자동 수정 금지.**
변경된 라인과 그 주변만 본다. 변경 안 된 코드는 지적 안 함 (스코프 크리프 방지).

---

## A) 보안 / 위생 점검

### 1) console 로그 (`*.{ts,tsx,js,jsx}`)
신규 라인 `console.(log|error|warn|debug|info|trace)`. 기존 라인 수정이면 "기존 코드" 라벨.

### 2) 신규 TODO/FIXME
신규 추가된 `TODO`/`FIXME`/`XXX`/`HACK`.

### 3) 시크릿 의심 (하드코딩)
- `(SECRET|TOKEN|API_KEY|PASSWORD|PRIVATE_KEY)\s*=\s*['"][^'"]{4,}['"]`
- `Bearer\s+[A-Za-z0-9._-]{10,}`, AWS `AKIA[0-9A-Z]{16}`, GitHub `ghp_[A-Za-z0-9]{36}` / `github_pat_*`, Slack `xox[baprs]-*`
- `process.env.X`, `import.meta.env.X` 참조는 제외

### 4) `.env` 스테이징
`.env` 또는 `.env.*` (단 `.env.example|sample|template`은 정상)

### 5) 외부 도메인 변경
신규 URL 중 사내(`*.vendys.co.kr`, `*.mealc.co.kr`) 외 강조

---

## B) 코드 리뷰 (`*.{ts,tsx,js,jsx}` 변경 라인 한정)

발견 시 **파일:라인** + **현재 → 제안** 형태로 짧게.

### 🔍 최우선 검토

**(가) 재활용 가능한 기존 로직**
신규 함수·훅·유틸·컴포넌트가 이미 프로젝트에 있는지 적극 grep:
- `src/utils/`, `src/hooks/`, `src/components/`, `src/lib/`, `src/common/` 우선
- 동의어 검색 (예: `formatPrice` → `format`, `Currency`, `dayjs`)
- 발견 못 해도 단언 X — "유사 구현 발견 못 함" 표기 가능

**(나) 코드 효율**
- 알고리즘 복잡도 (Set/Map 인덱스, O(n²) 회피)
- 중복 계산 → 변수 캐시
- 매 호출/렌더 객체·배열·정규식 생성 → 모듈 스코프
- `&&` 평가 순서 (저비용 먼저)

**(다) 리렌더링 (React)**

| 패턴 | 제안 |
|---|---|
| JSX `<Foo data={[...]} onChange={() => ...}/>` (inline 객체/배열/함수) | 상수 추출 / `useMemo` / `useCallback` |
| `Context.Provider value={{a, b}}` 매 렌더 | `useMemo`로 value 메모 |
| 리스트 `key={index}` (재정렬·삽입 가능) | 안정 식별자 |
| 부모 state 변경이 무관 자식까지 전파 | state 위치 내리기 / 자식 `React.memo` |
| 비싼 계산 매 렌더 (`sort`, 큰 변환) | `useMemo` (deps 안정적일 때만) |
| `useEffect` deps에 매 렌더 새 객체/함수 | primitive로 좁히거나 ref |

원칙: `memo`/`useMemo`/`useCallback`은 **이익 > 비용일 때만**. 작은 컴포넌트엔 낭비.

### 6) React 안티패턴 (위와 별개)

| 패턴 | 제안 |
|---|---|
| `useEffect` deps 누락/과다 | exhaustive-deps 보정 |
| 조건부/반복문 안 hook 호출 | 컴포넌트 최상위로 |
| state 직접 mutation (`state.x=`, `arr.push`) | spread / immer / functional setter |
| `setX(x+1)` (콜백 없이 prev 참조) | `setX(prev => prev+1)` |
| state 1개로 충분한데 `useReducer` 과설계 | `useState` |

### 7) JS / TS 안티패턴

| 패턴 | 제안 |
|---|---|
| `any` / `as any` 신규 | 구체 타입 / `unknown` + 좁히기 |
| `@ts-ignore` / `@ts-expect-error` (사유 주석 없음) | 직접 해결 또는 사유 한 줄 주석 |
| 빈 `catch {}` / `catch(e) {}` (e 미사용) | 최소 `console.error(e)` + 전파, 의도면 `_e` + 주석 |
| `==` / `!=` | `===` / `!==` |
| `var` | `const` / `let` |
| forgotten `await` (Promise 사용 누락) | `await` 또는 `void` 명시 |
| `try` 없는 외부 호출 (fetch/axios) | 에러 처리 또는 boundary 위임 |
| nullable 누락 (`obj.x.y`) | `?.`, `??` |
| `arr.push/sort/splice` 로 외부 배열 변경 | 불변 패턴 (`[...arr, x]`) |
| 매직 넘버 (3자리+ 의미 불명) | 상수 추출 |

### 8) 연산 / 자료구조

| 패턴 | 제안 |
|---|---|
| 루프 안 `arr.includes`/`find` (O(n²)) | `Set`/`Map` 인덱스 |
| `arr.filter().map()` 다단 | 한 번의 `for`/`reduce` (가독성 우선) |
| 부동소수 직접 비교 | `Math.abs(a-b) < ε` |
| 정수 나눗셈인데 `/` | `Math.trunc`/`Math.floor` 명시 |
| `+=` 문자열 누적 (대량) | 배열 push + `.join('')` |
| 매 렌더 큰 배열 복사 / 날짜 파싱 | `useMemo` / 상위 끌어올리기 |

### 9) 가독성

함수 50줄+ 신규 / 같은 로직 3회+ / 의미 불명 비트연산·정규식 무주석 / 미사용 import·변수 → 각각 분리·함수화·주석·제거 제안.

---

## 출력 형식

```
## stage-review 결과

### A) 보안 / 위생
1) console (N건): src/foo.ts:123 — `console.log(user)`
2) TODO/FIXME (N건): ...
3) 시크릿 (N건): ⚠️ src/api.ts:45 — `API_KEY = "ab...cd"` (마스킹)
4) .env: 없음 / .env.production (⚠️)
5) 외부 도메인: 사내 OK / ⚠️ cdn.thirdparty.com

### B) 코드 리뷰
🔍 최우선 — 재사용/효율/리렌더링 (N건):
- ⚠️ src/Foo.tsx:42 — 새 함수 `formatPrice` → src/utils/format.ts:18 `formatCurrency`와 동일
- src/Bar.tsx:88 — `<Child data={[1,2,3]} />` (inline 배열) → 상수 추출 / `useMemo`
- src/list.ts:55 — 루프 안 `arr.includes` (O(n²)) → `new Set(arr).has(x)`

6) React (N건): ...
7) JS/TS (N건): ...
8) 연산 (N건): ...
9) 가독성 (N건): ...

---
결론
- 차단 권장: N (시크릿/.env)
- 검토 권장: N
- 칭찬: <한두 줄 가능>
```

---

## 원칙

- **수정된 라인 한정** — 스코프 크리프 X
- **항상 "→ 제안"** — 지적만 X
- **모호하면 `?` 표기** ("의도적이면 무시")
- **prettier/eslint 영역 지적 X** (따옴표·세미콜론)
- **칭찬 1~2건 가능** (명확히 좋아진 부분)

## 절대 하지 말 것

- ❌ 자동 수정 / 자동 리팩터링
- ❌ 시크릿 값 그대로 출력 (앞뒤 4자만, 가운데 마스킹)
- ❌ 워킹트리 검사 (항상 `--cached`만)
- ❌ 변경 안 된 라인 리뷰
- ❌ 대안 없이 지적만
