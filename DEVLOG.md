# Bus Routing Auditor — 개발 로그

현재 버전의 상태만 기록합니다. 과거 버전별 작업 내역은 남기지 않습니다.

---

## V.2.0.1 (현재)

### 구조

- `src/` React + TypeScript UI, `src-tauri/` Rust bridge, `bus_backend.py` JSON-lines Python sidecar
- 스캔 모드: 에셋 이름 / Work Unit
- 룰 편집, 범위 선택, 결과 검토, Wwise에서 보기, CSV 내보내기, 대상 버스 재라우팅

### 브랜딩

- 상단바는 YSG Audio Labs 스위트 헤더와 제품 행 2단 구성
- 스위트 마크·워드마크는 Attenuation Auditor와 동일한 규격을 사용
- HUB 배지는 `src/branding.ts`의 `hubLink` export로 분리 — 다른 브랜드 빌드는 이 export를 빼면 배지가 렌더링되지 않음
- HUB 링크는 `tauri-plugin-opener`로 기본 브라우저에서 열리며, 권한은 허브 도메인으로 스코프 제한

### 빌드

- `build_v2.bat` — Python 백엔드 PyInstaller 패키징 후 Tauri + NSIS 인스톨러 생성
- 검증: `npm run build`, `cargo check`, 인스톨러 설치 및 실행 확인

---

## WAAPI 커맨드 레퍼런스 (재조회 방지)

> `mcp__sk-wwise-ui__get_commands` 로 직접 확인 — 이 Wwise 버전 기준

| 커맨드 | 설명 |
|--------|------|
| `FindInProjectExplorerSelectionChannel1` | 채널 1 선택 (정상 동작) |
| `FindInProjectExplorer` / `FindInProjectExplorer1` | 폴백 |
| `Inspect` | Property Editor 포커스 |
| ~~`FindInProjectExplorerSyncGroup1/2/3`~~ | **이 버전에 없음** — 새 창 열림 원인 |

| WAAPI 함수 | 용도 |
|------------|------|
| `ak.wwise.core.object.get` | 계층 전체 조회 |
| `ak.wwise.ui.commands.execute` | UI 커맨드 실행 |
| `ak.wwise.core.object.setReference` | OutputBus 재라우팅 |
