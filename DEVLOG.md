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

### install_addon.bat 버그 수정
- **원인**: PowerShell 명령을 `^` 줄 연결로 3줄에 분리 → 빈 줄이 연결을 끊어 명령 미전달
- **추가 오류**: `%LAUNCH_PATH:\\=\\\\%` 이중 이스케이프 → JSON 경로 4중 백슬래시 오류
- **수정**: PowerShell 명령 한 줄 통합, `%LAUNCH_PATH%` 그대로 전달 (ConvertTo-Json이 `\` → `\\` 자동 처리)

### 클린 설치 검증 (2회)
- 로컬 전체 삭제 → GitHub 클론 → `install.bat` (uv Python 탐지, .venv, waapi-client) → `install_addon.bat` (JSON 생성) 모두 정상

---

## 2026-04-14

### 버그 수정 (V2 신호 흐름 3종)

- **노드 구조 사라짐 (SFX만 표시)**: `_build_graph`에서 `filePath`를 multi-type `ofType` 쿼리에 포함하면 Wwise가 `{"return":[]}` 반환 → 그래프 비어 있어 `_get_signal_chain`이 Sound 노드만 반환. **수정**: Phase 1(전체 계층, filePath 제외) + Phase 2(WorkUnit 전용 filePath fetch) 2단계 분리. Phase 2 결과로 `.wwu` 확장자 없는 WorkUnit → `PhysicalFolder` 타입으로 교정.
- **노드 hover/click 애니메이션 없음**: `_draw_node`에서 `cv.create_rectangle()` 반환값을 `rect`에 저장하지 않아 클로저 내 `NameError` → 첫 줄을 `rect = cv.create_rectangle(...)` 으로 수정.
- **자동 리빌드 미동작**: 위 Bug 1로 인해 그래프가 비어 있어 리빌드해도 변화 없음. Bug 1 수정 후 정상화. 추가로 `_register_subscriptions` 반환값(등록 성공 수)을 상태 바에 `⚡ 자동감지 N개`로 표시해 활성 여부 가시화.

---

## 2026-04-15  ·  UI 개선 8종

### 기능 변경

1. **상태바 분리**: 헤더에 프로젝트 이름(`_proj_lbl`, ACCENT 색) + 상태 메시지(`_status_lbl`) 분리 표시. `_set_proj_name()` 별도 메서드. `_cur_status_key/args`로 언어 전환 시 상태 메시지 자동 재번역 (`_refresh_lang`에서 처리).

2. **결과 목록 상속/오버라이드 색깔**: `inherited_vio` 태그(주황 WARN) / `overridden_vio` 태그(빨강 ERR_CLR)로 분리. `_apply_filter`에서 `r.get("inherited")` 기준으로 태그 결정.

3. **에셋 이름 기준 탭도 동일 색깔 적용**: `_apply_filter`가 `is_name` 여부와 무관하게 `inherited_vio`/`overridden_vio` 태그 사용.

4. **마우스오버 텍스트 하이라이트**: `<Motion>` 이벤트로 hover 행 감지 → `_hover` 태그(bold) 추가, `<Leave>`에서 원상 복귀. 결과 목록 트리 + 신호 흐름 탭 위반 목록 모두 적용.

5. **히트맵 레이아웃 통일**: `_update_heatmap`이 에셋 이름/WU 기준 동일 코드 → `cv.update_idletasks()` 후 `winfo_width()` 사용해 실제 너비 기준 동적 COLS 계산. 두 탭 동일 결과.

6. **버스 히트맵 전면 재설계**: 룰/키워드 무관, 프로젝트 전체 버스를 `_bus_hierarchy` 계층 DFS 순서대로 나열. 초록(위반 없음) 포함 전체 표시. 위반율 = 해당 버스에 직접 라우팅된 Sound 중 위반 비율. `sort_by_vio` 체크박스 제거. 위반율 정의를 헤더 오른쪽에 한줄 표시.

7. **탭 이름 변경**: "결과 목록" → "키워드 설정 / 검색" (한/영 모두).

8. **룰 초기화 버튼**: "룰 저장" 오른쪽에 "룰 초기화(danger)" 버튼. 클릭 시 `askyesno` 경고 팝업 → 확인하면 모든 rule_rows 제거 + JSON 저장.

9. **버스 트리 선택 필터 수정**: `_on_sf_bus_select`에서 서브트리 전체가 아닌 선택한 버스 자신에 직접 할당된 위반만 필터링 (`bus_key ==` 정확 비교).
