# front-web-claude-marketplace

벤디스 프론트엔드 7개 프로젝트(cafeteria-web-electron, corp-web, market-web, sikdae-webview, store-web, vendys-homepage, vone-web)에 적용하는 Claude Code 공통 정책 마켓플레이스.

## 포함 플러그인

| 이름 | 설명 |
|---|---|
| `security-base` | 공통 보안 정책 (위험 명령 차단, 시크릿 파일 보호, deny 리스트) |
| `pr-workflow` | PR 생성/스테이지 리뷰 자동화 |

## 설치

각 프로젝트 `.claude/settings.json`에 마켓플레이스를 등록하고, 플러그인을 수동 설치합니다.

### 1) 마켓플레이스 등록

```jsonc
// .claude/settings.json
{
  "extraKnownMarketplaces": {
    "vendys-marketplace": {
      "source": {
        "source": "github",
        "repo": "vendys-donghyun/front-web-claude-marketplace"
      }
    }
  }
}
```

### 2) GitHub 인증 (Private 레포 접근)

```bash
gh auth login
```

### 3) Claude Code에서 플러그인 설치

```text
/plugin install security-base@vendys-marketplace
/plugin install pr-workflow@vendys-marketplace
```

설치 후 **세션 재시작 필수**.

## 호출 형식

```text
/pr-workflow:pr-create
/pr-workflow:stage-review
```

## 운영 정책

- 자동 업데이트 OFF (검토 후 적용)
- 강제력 필요한 정책만 hook/deny로 마켓에 포함. 코딩 컨벤션·비즈니스 규칙은 각 프로젝트 `CLAUDE.md`에.

## 디렉터리 구조

```
front-web-claude-marketplace/
├── .claude-plugin/
│   └── marketplace.json
├── plugins/
│   ├── security-base/
│   │   └── .claude-plugin/
│   │       └── plugin.json
│   └── pr-workflow/
│       └── .claude-plugin/
│           └── plugin.json
└── README.md
```
