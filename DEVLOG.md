# Bus Routing Auditor — 개발 로그

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

---

## 2026-04-10

### 버그 수정
- **ADM File3 → UI_PassThrough 오인식**: Sound 자체 stale값이 Phase 2에 포함 → stale dict에서 `type == "Sound"` 제외
- **WU 스캔 오탐**: `search`에 Sound 자신의 이름이 포함돼 WU 키워드로 오탐 → `parent_path = path[:path.rfind("\\")]` 사용
- **UI_PassThroughMix 등 미매칭**: keyword 분리 후 비교 → keyword literal + WORD_SEP 경계 regex로 교체

### 기능 추가
- **한/영 UI 전환**: `STRINGS["ko"/"en"]` + `_lang_updaters` 콜백 리스트 (툴팁 포함)
- **Wwise에서 보기**: `FindInProjectExplorerSelectionChannel1` + `Inspect` 조합
- **싱글턴 창**: `FindWindowW` → `SW_RESTORE + SetForegroundWindow`

---

## 2026-04-13  ·  V.1.0.0

### 기능 추가
- **항목별 검색 필터**: `ttk.Combobox`로 필드 선택 (전체/이름/WU/버스/기대키워드), 언어 전환 시 자동 갱신
- **경로 컬럼 너비**: 600 → 1200px
- **위반 없음 메시지**: 스캔 완료 후 결과 없으면 트리에 녹색 `✓` 메시지 표시 (`_scanned_*` 플래그로 미스캔과 구분)
- **다중 키워드 OR 검색**: 소스 키워드(에셋 이름 / WU 경로)·버스 키워드 모두 `+` 버튼으로 OR 조건 추가 가능
  - `extra_keywords` / `extra_work_unit_keywords` / `extra_bus_keywords` 필드로 JSON 저장
  - 트리거 / 기대버스 컬럼에 `"A | B"` 형식으로 표시
- **룰 저장 안내 레이블**: 저장 버튼 왼쪽 `⚠ 룰 변경 시 저장 후 스캔`
- **버스 미설정 체크박스 보조 설명**: 체크박스 오른쪽에 회색으로 `(위반된 최상위 항목의 하위 에셋들이 모두 노출됩니다)` 표시
- **스캔 2 WU 키워드 `?` 툴팁**: 검색 대상 3가지(WU 이름/경로/상위계층) + 부분 이름 매칭 동작 + 전체 이름 지정 방법 안내

### 버그 수정
- **TCombobox 포커스 이탈 텍스트 소실**: clam 테마 `readonly !focus` → `s.map("TCombobox", ...)` 명시 고정
- **Property Editor 포커스 미이동**: SyncGroup 커맨드 미존재 확인 → SelectionChannel1 + Inspect 조합으로 수정
- **Wwise 종료 시 툴 안 꺼짐**: WAAPI call hang → `socket.create_connection("127.0.0.1", 8080, timeout=2)` port 체크로 교체
- **Objects WU 오브젝트 → Ambience 오인식**: Phase 2가 중간 컨테이너 stale값(이동/복사 잔류) 우선 반환 → `_find_stale_highest`로 교체 (루트까지 순회 후 가장 높은 stale 조상 반환, stale_cache 제거)
- **Silence 등 내부 생성 SFX → Master Audio Bus**: Sound 자체 stale 제외로 Phase 1+2 모두 실패 → Phase 3 추가: Phase 1+2 결과가 Master Audio Bus일 때만 Sound 자신의 `@OutputBus` 사용 (ADM File3 회귀 없음 — 그 Sound는 Phase 2에서 처리됨)
- **OR 행 정렬 어긋남**: src_section/bus_section 별도 프레임 → 단일 grid(`g`) 방식으로 재작성. 소스 OR·버스 OR 행이 같은 grid row를 공유하여 나란히 표시, 삭제 시 빈 행 공간 자동 소멸
- **`_check_workunit_rules` OR 로직 누락**: `extra_work_unit_keywords`가 JSON 저장은 됐으나 검사 조건에 반영 안 됨 → `all_src = [work_unit_keyword] + extra_work_unit_keywords` OR 로 수정

---

## 2026-04-13  —  GitHub 배포 및 검증

### 배포
- GitHub 레포 생성: `https://github.com/samter96/Wwise-Bus-Routing-Auditor`
- 계정명 `samter96-stack` → `samter96` 변경, 전체 커밋 author `samter96@gmail.com` 으로 통일 (rebase --root)

### install_addon.bat 버그 수정
- **원인**: PowerShell 명령을 `^` 줄 연결로 3줄에 분리 → 빈 줄이 연결을 끊어 명령 미전달
- **추가 오류**: `%LAUNCH_PATH:\\=\\\\%` 이중 이스케이프 → JSON 경로 4중 백슬래시 오류
- **수정**: PowerShell 명령 한 줄 통합, `%LAUNCH_PATH%` 그대로 전달 (ConvertTo-Json이 `\` → `\\` 자동 처리)

### 클린 설치 검증 (2회)
- 로컬 전체 삭제 → GitHub 클론 → `install.bat` (uv Python 탐지, .venv, waapi-client) → `install_addon.bat` (JSON 생성) 모두 정상


