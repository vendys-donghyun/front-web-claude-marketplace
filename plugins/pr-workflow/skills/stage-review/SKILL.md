---
name: stage-review
description: 스테이지된 변경(`git diff --cached`)에서 (A) 보안/위생 점검 — console 로그, 신규 TODO/FIXME, 시크릿 패턴, .env 스테이징, 외부 도메인 — 과 (B) React/JS/TS 코드 리뷰 — **재사용 가능한 기존 로직 탐지 / 코드 효율 / 리렌더링 최적화**를 최우선으로, 그리고 일반 안티패턴·연산 최적화 — 를 검사하고 리포트만 출력. 자동 수정 금지.
---

# stage-review

`git diff --cached`만 검사한다. 워킹트리·이전 커밋은 보지 않는다. **리포트만, 자동 수정 금지**.

리뷰 범위는 **수정된 라인과 그 주변 컨텍스트**. 변경되지 않은 코드는 지적하지 않는다 (스코프 크리프 방지).

---

## A) 보안 / 위생 점검

### 1) console 로그 (`*.ts`, `*.tsx`, `*.js`, `*.jsx`)
- 신규 라인에서 `console.(log|error|warn|debug|info|trace)`
- 기존 라인 수정이면 "기존 코드" 라벨로 구분

### 2) 신규 TODO/FIXME
- 신규 추가된 `TODO`, `FIXME`, `XXX`, `HACK` (대소문자)

### 3) 시크릿 의심 패턴 (하드코딩)
정규식:
- `(SECRET|TOKEN|API_KEY|PASSWORD|PRIVATE_KEY)\s*=\s*['"][^'"]{4,}['"]`
- `Bearer\s+[A-Za-z0-9._-]{10,}`
- AWS: `AKIA[0-9A-Z]{16}`
- GitHub: `ghp_[A-Za-z0-9]{36}`, `github_pat_[A-Za-z0-9_]+`
- Slack: `xox[baprs]-[A-Za-z0-9-]+`

환경변수 참조(`process.env.X`, `import.meta.env.X`)는 정상이므로 제외.

### 4) `.env` 스테이징
- `git diff --cached --name-only`에 `.env` 또는 `.env.*` 포함 여부
- 단 `.env.example` / `.env.sample` / `.env.template` 은 정상

### 5) 외부 도메인 변경
- diff에서 신규 추가된 URL (`https?://[^\s'"`<>]+`)
- 사내 도메인 외(`*.vendys.co.kr`, `*.mealc.co.kr` 외)는 강조

---

## B) 코드 리뷰 (React / JS / TS)

`*.ts`, `*.tsx`, `*.js`, `*.jsx` 파일의 변경된 라인을 대상. 발견 시 **파일:라인**과 **현재 코드 → 제안** 형태로 짧게 표시.

### 🔍 최우선 검토 영역 (특히 깊이 본다)

#### (가) 재활용 가능한 기존 로직 탐지

신규 추가된 함수·훅·유틸·컴포넌트가 **이미 프로젝트에 비슷한 구현이 있는지** 적극적으로 찾는다. "있는 줄 모르고 새로 만든 코드"가 가장 흔한 부채.

탐지 절차:
1. 신규 함수의 이름·시그니처·핵심 로직 추출
2. 코드베이스 grep:
   - `src/utils/`, `src/hooks/`, `src/components/`, `src/lib/`, `src/common/` 우선
   - 동의어 검색: 예) `formatDate` 신규면 `format`, `Date`, `Time`, `dayjs`, `moment` 등 검색
   - 정규식 / 계산 로직은 핵심 패턴(예: `replace.*[0-9]`, `Math.round`)으로 검색
3. 비슷한 게 발견되면:
   ```
   ⚠️ src/feature/Foo.tsx:42 — 새 함수 `formatPrice`
      → src/utils/format.ts:18 의 `formatCurrency`와 거의 동일. 재사용 검토.
   ```

발견 못 해도 단언하지 않는다 — "유사 구현 발견 못 함"으로 표기 가능 (검색 한계 인정).

#### (나) 코드 효율

같은 결과를 더 적은 비용으로 얻는 방법. 변경된 라인 한정.
- 알고리즘 복잡도: 8번 표 참조 (Set/Map 인덱스, O(n²) 회피)
- 중복 계산: 같은 값을 한 함수 안에서 여러 번 계산 → 변수로 캐시
- 불필요한 객체/배열 생성: 루프마다 new Date(), 매 호출 새 정규식 → 모듈 스코프로 끌어올리기
- 조건 평가 순서: 비용 낮은 조건을 `&&` 앞쪽에

#### (다) 리렌더링 최적화 (React)

수정·추가된 컴포넌트·훅에 대해 다음을 본다.

| 패턴 | 영향 | 제안 |
|---|---|---|
| JSX 속성에 inline 객체/배열/함수 (`<Foo data={[...]} onChange={() => ...}/>`) | 자식이 `React.memo`여도 매 렌더 새 참조로 깨짐 | 상수 추출 / `useMemo` / `useCallback` |
| `Context.Provider value={{a, b}}` 매 렌더 새 객체 | 모든 consumer 재렌더 | `useMemo`로 value 메모 |
| 리스트 `key={index}` (재정렬·삽입 가능) | 재마운트 / 상태 꼬임 | 안정 식별자 (id 등) |
| 부모 state가 자식과 무관한데 부모 전체 리렌더 | 자식까지 같이 렌더 | state 위치 내리기 (lift down) 또는 자식 `React.memo` |
| 큰 트리 안 한 leaf만 자주 바뀜 | 형제까지 재렌더 | leaf만 분리 + `React.memo` |
| 비싼 계산을 매 렌더 (`sort`, 큰 배열 변환) | CPU | `useMemo` (단, deps가 자주 바뀌면 의미 없음) |
| `useEffect` deps에 매 렌더 새 객체/함수 | 무한 루프 또는 매 렌더 effect | deps를 primitive로 좁히거나 ref 사용 |
| state 1개로 묶을 수 있는데 여러 `useState`로 쪼개 매번 다같이 set | 다중 렌더 | `useReducer` 또는 1번에 set |

원칙:
- `React.memo`/`useMemo`/`useCallback`은 **이익이 비용보다 클 때만**. 단순 prop만 받는 작은 컴포넌트엔 오히려 낭비.
- 리렌더가 실제로 문제가 될 만한 곳(자주 변하는 부모, 큰 리스트, 무거운 자식)에 집중.

### 6) React 안티패턴

| 패턴 | 지적 사유 | 제안 |
|---|---|---|
| `useEffect` deps 누락 / 과다 | stale closure 또는 무한 렌더 | exhaustive-deps 기준으로 보정 |
| 조건부/반복문 안에서 hook 호출 | rules-of-hooks 위반 | 컴포넌트 최상위로 이동 |
| state 직접 mutation (`state.x = ...`, `arr.push`) | React가 변경 감지 못 함 | spread / immer / functional setter |
| 리스트 `key={index}` (재정렬·삽입 가능 리스트) | 재마운트로 상태 꼬임 | 안정 식별자 사용 |
| JSX 속성에 새 객체/배열 inline (`style={{...}}`, `data={[...]}`) | 매 렌더마다 새 참조 → 자식 메모 무력화 | 상수 추출 또는 `useMemo` |
| `useMemo`/`useCallback` 무분별 사용 (단순 값/함수) | 메모 비용 > 이익 | 그냥 인라인 |
| state 1개로 충분한데 `useReducer` 과설계 | 가독성 저하 | `useState` |
| `setState` 콜백 없이 이전 state 참조 (`setX(x+1)`) | race | `setX(prev => prev+1)` |

### 7) JS / TS 안티패턴

| 패턴 | 제안 |
|---|---|
| `any` / `as any` 신규 추가 | 구체 타입, `unknown` + 좁히기 |
| `@ts-ignore` / `@ts-expect-error` 신규 (사유 주석 없음) | 타입 오류 직접 해결 또는 사유 한 줄 주석 동반 |
| 빈 `catch {}` / `catch(e) {}` (e 미사용) | 최소 `console.error(e)` + 상위 전파, 의도면 `_e` + 주석 |
| `==` / `!=` | `===` / `!==` |
| `var` | `const` / `let` |
| `forgotten await` (Promise를 await 없이 사용) | `await` 추가 또는 `void` 명시 |
| `try` 없는 외부 호출 (fetch/axios 등) | 에러 처리 또는 boundary로 위임 |
| nullable 체크 누락 (`obj.x.y` 가 undefined 가능) | `?.`, `??` |
| `Array.prototype.push/sort/splice`로 외부 배열 변경 | `[...arr, x]`, `[...arr].sort()` |
| 매직 넘버 (3자리 이상 의미 불명) | 상수 추출 |
| 같은 객체에 여러 번 인덱싱 (`obj.a.b`, `obj.a.c`) | 디스트럭처링 |
| 깊은 중첩 `if` 또는 `else if` 체인 | early return / `switch` / 룩업 객체 |

### 8) 연산 / 수식 / 자료구조

| 패턴 | 제안 |
|---|---|
| `arr.filter(...).map(...)` 다단 체인을 매번 | 한 번의 `for` 또는 `reduce`로 합치기 (단, 가독성 우선) |
| `O(n²)` 검색 (`arr.includes`/`find`를 루프 안에서) | `Set` / `Map` 으로 인덱스 빌드 후 조회 |
| 부동소수 직접 비교 (`a === 0.1 + 0.2`) | epsilon 비교 또는 `Math.abs(a-b) < ε` |
| 정수 나눗셈 의도인데 `/` 사용 | `Math.trunc` / `Math.floor` 명시 |
| 큰 배열 복사를 매 렌더에서 수행 | `useMemo` 또는 상위로 끌어올리기 |
| 문자열 누적을 `+=` 으로 반복 (대량) | 배열 push 후 `.join('')` |
| 날짜 파싱/포맷을 매 렌더 | 메모이즈 / 라이브러리 캐시 |

### 9) 일반 가독성 (수정사항 한정)

- 함수 50줄 초과 신규 추가 → 분리 검토
- 같은 로직 반복 3회+ → 함수화
- 주석 없이 의미 불명한 비트 연산 / 정규식 → 한 줄 설명 권장
- 사용하지 않는 import / 변수 신규 추가 → 제거 제안

---

## 절차

```bash
git diff --cached --name-only           # 파일 목록
git diff --cached                        # 본문
```

검사 후 아래 형식으로 출력.

## 출력 형식

```
## stage-review 결과

### A) 보안 / 위생

#### 1) console 로그 (N건)
- src/foo.ts:123 — `console.log(user)`
- (없으면 "없음")

#### 2) 신규 TODO/FIXME (N건)
- ...

#### 3) 시크릿 의심 (N건)
- ⚠️ src/api.ts:45 — `API_KEY = "abcd..."`  (값은 앞뒤 4자만 표시)

#### 4) .env 스테이징
- 없음 / .env.production 스테이징됨 (⚠️)

#### 5) 외부 도메인
- 사내: api.vendys.co.kr
- ⚠️ 외부: cdn.thirdparty.com

### B) 코드 리뷰

#### 🔍 최우선 — 재사용 / 효율 / 리렌더링 (N건)
- ⚠️ src/feature/Foo.tsx:42 — 새 함수 `formatPrice`
  → src/utils/format.ts:18 `formatCurrency`와 거의 동일. 재사용 검토.
- src/Bar.tsx:88 — `<Child data={[1,2,3]} />` (inline 배열)
  → 모듈 스코프 상수 또는 `useMemo`. 자식이 memo여도 현재는 매번 깨짐.
- src/list.ts:55 — 루프 안 `arr.includes` (O(n²))
  → `const set = new Set(arr); set.has(x)`

#### 6) React (N건)
- src/Foo.tsx:42 — `useEffect` deps 누락(`userId`)
  → exhaustive-deps 추가 또는 의도적 누락이면 eslint-disable 사유 주석

#### 7) JS / TS (N건)
- src/util.ts:18 — `as any` 신규
  → 구체 타입 또는 `unknown` 후 좁히기

#### 8) 연산 / 자료구조 (N건)
- src/list.ts:55 — 루프 안 `arr.includes` (O(n²))
  → `const set = new Set(arr)` 후 `set.has(x)`

#### 9) 가독성 (N건)
- ...

---
## 결론
- 차단 권장: <개수> (시크릿/.env)
- 검토 권장: <개수> (console/TODO/외부 도메인/리뷰 지적)
- 칭찬: <개수> (잘 한 점)  ← 있으면 한두 줄
```

## 작성 원칙

- **수정된 라인 한정**: 같은 파일이라도 변경 안 된 부분은 지적하지 않는다. PR 스코프 보호.
- **대안 제시 의무**: 지적만 하지 말고 항상 "→ 제안"을 한 줄 함께.
- **확신 없는 건 표시**: 안티패턴인지 의도된 건지 모호하면 `?`로 표기 ("의도적이면 무시").
- **잡소리 금지**: 코드 스타일(따옴표·세미콜론) 등 prettier/eslint가 잡는 건 지적하지 않는다.
- **칭찬 1~2건**: 패턴이 명확히 좋아진 부분은 짧게 칭찬. 항상은 아님.

## 절대 하지 말 것

- ❌ 발견된 console.log를 자동으로 제거하거나 파일 수정
- ❌ 시크릿으로 보이는 값을 그대로 출력 (앞뒤 4자만 표시, 가운데 마스킹)
- ❌ 워킹트리 변경(스테이지 안 된 것) 검사 — 항상 `--cached`만
- ❌ 변경 안 된 라인까지 리뷰 (스코프 크리프)
- ❌ 자동 수정 / 자동 리팩터링 — 사용자가 결정
- ❌ "이건 잘못됐다"만 적고 대안 없이 끝내기
