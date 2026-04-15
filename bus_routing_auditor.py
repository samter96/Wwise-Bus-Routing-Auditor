#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font as tkfont
import json, os, csv, threading, time, re, socket

try:
    from waapi import WaapiClient, CannotConnectToWaapiException
    WAAPI_AVAILABLE = True
except ImportError:
    WAAPI_AVAILABLE = False

VERSION     = "V.2.0.0"
WAAPI_URL   = "ws://127.0.0.1:8080/waapi"
SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "bus_routing_rules.json")
WORD_SEP    = re.compile(r'[ _\-\./\\()\[\]{},;:\s]+')
DEFAULT_CONFIG = {
    "name_rules": [
        {"keyword": "UI",    "expected_bus_keyword": "UI",    "case_sensitive": False},
        {"keyword": "Music", "expected_bus_keyword": "Music", "case_sensitive": False},
        {"keyword": "AMB",   "expected_bus_keyword": "AMB",   "case_sensitive": False},
        {"keyword": "VO",    "expected_bus_keyword": "VO",    "case_sensitive": False},
    ],
    "workunit_rules": [
        {"work_unit_keyword": "UI",    "expected_bus_keyword": "UI",    "case_sensitive": False},
        {"work_unit_keyword": "Music", "expected_bus_keyword": "Music", "case_sensitive": False},
        {"work_unit_keyword": "AMB",   "expected_bus_keyword": "AMB",   "case_sensitive": False},
        {"work_unit_keyword": "VO",    "expected_bus_keyword": "VO",    "case_sensitive": False},
    ],
    "flag_unset_bus": True,
}
STRINGS = {
    "ko": {
        "reconnect":      "⟳  재연결",
        "help_btn":       "?  도움말",
        "help_title":     "Bus Routing Auditor — 사용 방법",
        "help_body": (
            "【 연결 】\n"
            "• Wwise 실행 후 WAAPI 활성화 (Project > User Preferences > Enable WAAPI)\n"
            "• 상단 ⟳ 재연결 버튼으로 연결. 연결 후 그래프 자동 빌드\n"
            "• Wwise 프로젝트 구조 변경 시 1.5초 후 자동 리빌드 (재연결 불필요)\n"
            "\n"
            "【 룰 설정 】\n"
            "• 스캔 1: 에셋 이름에 키워드 포함 → 버스 이름에 해당 키워드가 있어야 함\n"
            "• 스캔 2: Sound가 속한 Work Unit / 경로에 키워드 포함 → 버스 이름 검사\n"
            "• + 버튼으로 OR 조건 추가 가능. 룰 수정 후 반드시 저장 후 스캔\n"
            "\n"
            "【 결과 목록 】\n"
            "• 위반 에셋 더블클릭 → Wwise에서 해당 에셋 선택 + 프로퍼티 에디터 포커스\n"
            "• ⟲ 일괄 재라우팅: 선택 에셋의 OutputBus를 지정 버스로 일괄 변경\n"
            "• 검색 필드로 이름 / WU / 버스 / 기대 키워드 단위 필터링\n"
            "\n"
            "【 신호 흐름 탭 】\n"
            "• 좌측 버스 트리 — 빨강: 직접 위반 버스, 주황: 하위에 위반 에셋 존재\n"
            "• 버스 클릭 → 우측 에셋 목록 필터링\n"
            "• 에셋 선택 → 하단 계층 그래프: Sound → 컨테이너 → WU → 현재 버스 ✗ → 기대 키워드 ✓\n"
            "• 계층 그래프 각 노드 클릭 → Wwise에서 해당 오브젝트 포커스\n"
            "• ··· N 노드 클릭 → 중간 계층 전체 펼치기\n"
            "\n"
            "【 히트맵 탭 】\n"
            "• 버스별 위반율 시각화 — 초록(0%) → 노랑(<15%) → 주황(<35%) → 빨강(35%+)\n"
            "• 셀 클릭 → 해당 버스 신호 흐름 탭으로 이동\n"
            "\n"
            "【 멀티 키워드 OR 룰 】\n"
            "• NPC_AMB_Walla처럼 여러 룰에 매칭될 때: 하나라도 만족하면 통과\n"
            "• 모두 실패 시에만 위반 — 기대 버스에 'NPC or AMB' 형식으로 표시\n"
        ),
        "lang_toggle":    "EN",
        "tab1":           "  스캔 1  ·  에셋 이름 기준  ",
        "tab2":           "  스캔 2  ·  Work Unit 기준  ",
        "rule_title":     "룰 설정",
        "desc_name":      "이름에 키워드 포함 → 버스 이름에도 해당 키워드 있어야 함",
        "desc_wu":        "Work Unit / 경로에 키워드 포함 → 버스 이름에도 해당 키워드 있어야 함",
        "kw_name":        "에셋 이름 키워드",
        "kw_wu":          "Work Unit / 경로 키워드",
        "bus_kw_hdr":     "→  버스 이름 키워드",
        "case_hdr":       "대소문자",
        "flag_unset":     "버스 미설정(상속됨) 항목도 위반으로 표시",
        "add_rule":       "+ 룰 추가",
        "save_rules":     "룰 저장",
        "search_lbl":     "검색",
        "search_hint":    "단어 단위 검색 (예: UI  /  AMB Metal  /  PC Attack)",
        "inherited":      "↑ 상속됨",
        "overridden":     "◆ 오버라이드됨",
        "col_name":       "에셋 이름",
        "col_work_unit":  "Work Unit",
        "col_cur_bus":    "현재 버스",
        "col_trigger":    "위반 원인",
        "col_exp_kw":     "기대 버스 키워드",
        "col_path":       "전체 경로",
        "scan":           "▶  스캔 실행",
        "view_wwise":     "⊙  Wwise에서 보기",
        "reroute":        "⟲  일괄 재라우팅",
        "select_all":     "전체 선택",
        "export_csv":     "↓  CSV 내보내기",
        "connecting":     "Wwise 연결 중...",
        "connected_fmt":  "연결됨  ·  버스 {}개",
        "connect_fail":   "연결 실패  —  Project > User Preferences > WAAPI 활성화 필요  ({})",
        "no_waapi":       "waapi-client 미설치  →  install.bat 을 실행하거나  pip install waapi-client",
        "scanning":       "스캔 중...",
        "scan_done_name": "[이름 스캔 완료]  {}개 Sound  ·  위반 {}개",
        "scan_done_wu":   "[Work Unit 스캔 완료]  {}개 Sound  ·  위반 {}개",
        "scan_fail":      "스캔 실패: {}",
        "filter_applied": "필터 적용  ·  {} / {}개",
        "no_violations":  "총 {}개  ·  위반 없음 ✓",
        "violations":     "총 {}개  ·  위반 {}개",
        "no_wwise":       "Wwise에 연결되지 않았습니다.",
        "select_item":    "항목을 선택하세요.",
        "select_reroute": "재라우팅할 항목을 선택하세요.",
        "no_export":      "내보낼 결과가 없습니다.",
        "rules_saved":    "룰이 저장되었습니다.",
        "rules_reset":    "룰 초기화",
        "rules_reset_confirm": "현재 저장된 모든 룰이 삭제됩니다.\n계속하시겠습니까?",
        "save_title":     "저장",
        "error_title":    "오류",
        "info_title":     "안내",
        "scan_error":     "스캔 오류",
        "reroute_title":  "버스 재라우팅",
        "reroute_fmt":    "{}개 항목을 재라우팅합니다.",
        "reroute_bus_sel":"각 키워드 그룹에 적용할 버스를 선택하세요:",
        "cancel":         "취소",
        "apply_reroute":  "재라우팅 적용",
        "reroute_done":   "{}개 재라우팅 완료.",
        "reroute_partial":"{} 완료  /  {} 실패\n\n{}",
        "partial_title":  "일부 실패",
        "complete_title": "완료",
        "csv_title":      "CSV로 내보내기",
        "csv_done":       "저장 완료:\n{}",
        "not_found":      "Wwise에서 오브젝트를 선택할 수 없었습니다.\nProject Explorer에서 수동으로 찾아주세요.",
        "bus_missing":    '버스 "{}" 없음',
        "search_all":     "전체",
        "save_reminder":  "⚠ 룰 변경 시 저장 후 스캔",
        "flag_unset_note": "(위반된 최상위 항목의 하위 에셋들이 모두 노출됩니다)",
        "tip_kw_wu": (
            "┌─ Work Unit 키워드 — 매칭 방식 ───────────────────────────\n"
            "│  입력한 키워드가 아래 항목 중 하나라도 포함되면 매칭됩니다:\n"
            "│    · Work Unit 이름\n"
            "│    · Work Unit 전체 경로\n"
            "│\n"
            "│  ⚠ Actor-Mixer 폴더 이름은 검색 대상이 아닙니다.\n"
            "│     WU 파일 이름/경로를 기준으로만 판단합니다.\n"
            "│\n"
            "│  ⚠ 부분 이름도 매칭됩니다 (단어 경계 기준)\n"
            "│  예) 키워드: AMB\n"
            "│      → AMB_Sounds ✓  /  Default_AMB ✓  /  AMB ✓\n"
            "│      → AMBIENT ✗  (단어 경계 없음)\n"
            "│\n"
            "│  특정 Work Unit만 검색하려면 이름 전체를 키워드로 입력하세요.\n"
            "│  예) 'NPC_Main'만 → 키워드: NPC_Main\n"
            "└──────────────────────────────────────────────────────────"
        ),
        "tip_name": (
            "┌─ 스캔 1  에셋 이름 기준 ────────────────────────────────\n"
            "│  Sound 오브젝트의 이름을 검사합니다.\n"
            "│\n"
            "│  동작 방식\n"
            "│  이름에 '에셋 이름 키워드'가 단어 토큰으로 포함되어 있으면\n"
            "│  해당 Sound가 라우팅된 버스 이름에도 '버스 이름 키워드'가\n"
            "│  단어 토큰으로 포함되어야 합니다. 없으면 위반으로 표시합니다.\n"
            "│\n"
            "│  단어 토큰이란?\n"
            "│  _  (언더바)  /  Space  /  -  /  .  /  /  등으로 구분된 단어.\n"
            "│  'UI'는 UI_Click ✓, NPC_UI ✓ 에 매칭되지만\n"
            "│  BUILD ✗, QUIT ✗ 에는 매칭되지 않습니다.\n"
            "│  키워드가 'UI_Mix' 처럼 _ 포함 시 연속 토큰 매칭을 사용합니다.\n"
            "│\n"
            "│  예시 룰:  PC  →  PC\n"
            "│    PC_Attack_01  라우팅→  PC_Bus      ✓\n"
            "│    PC_Attack_01  라우팅→  NPC_Bus     ✗  (NPC ≠ PC)\n"
            "└──────────────────────────────────────────────────────────"
        ),
        "tip_wu": (
            "┌─ 스캔 2  Work Unit / 경로 기준 ─────────────────────────\n"
            "│  Sound의 소속 경로를 검사합니다.\n"
            "│  검색 대상: Work Unit 이름 + Work Unit 전체 경로\n"
            "│             + 오브젝트 상위 경로 (Sound 자신의 이름 제외)\n"
            "│\n"
            "│  예시 룰:  경로 키워드: UI  →  버스 이름 키워드: UI\n"
            "│    \\SFX\\UI\\Buttons\\Click_01  라우팅→  UI_Bus  ✓\n"
            "│    \\SFX\\UI\\Buttons\\Click_01  라우팅→  SFX_Bus ✗\n"
            "│\n"
            "│  ▸ 상속됨 필터  (노랑)\n"
            "│    버스가 부모 오브젝트에서 상속된 항목\n"
            "│  ▸ 오버라이드됨 필터  (빨강)\n"
            "│    버스가 이 Sound에 직접 명시적으로 설정된 항목\n"
            "└──────────────────────────────────────────────────────────"
        ),
        "tab_results":          "  키워드 설정 / 검색  ",
        "tab_results_name":     "  키워드 설정 / 검색 · 에셋 이름 기준  ",
        "tab_results_wu":       "  키워드 설정 / 검색 · Work Unit 기준  ",
        "tab_sf":               "  신호 흐름 · 버스 분석  ",
        "tab_sf_name":          "  신호 흐름 · 버스 분석 · 에셋 이름 기준  ",
        "tab_sf_wu":            "  신호 흐름 · 버스 분석 · Work Unit 기준  ",
        "tab_heatmap":          "  히트맵  ",
        "tab_heatmap_name":     "  히트맵 · 에셋 이름 기준  ",
        "tab_heatmap_wu":       "  히트맵 · Work Unit 기준  ",
        "graph_building":   "그래프 빌드 중...",
        "graph_ready_fmt":  "그래프 완료  ·  {}개 오브젝트",
        "graph_rebuild":    "⟳  그래프 재빌드",
        "no_scan_result":   "스캔 1 또는 스캔 2를 먼저 실행하세요",
        "bus_tree_hdr":     "버스별 위반",
        "sf_hdr":           "신호 흐름",
        "sf_hdr_name":      "신호 흐름  ·  에셋 이름 기준",
        "sf_hdr_wu":        "신호 흐름  ·  Work Unit 기준",
        "hm_hdr_name":      "버스 위반 히트맵  ·  에셋 이름 기준",
        "hm_hdr_wu":        "버스 위반 히트맵  ·  Work Unit 기준",
        "sf_hint":          "위반 항목을 클릭하면 신호 흐름이 표시됩니다",
        "graph_not_ready":  "그래프 빌드가 필요합니다  —  Wwise 연결 후 자동 빌드됩니다",
        "heatmap_hdr":      "버스 위반 히트맵",
        "heatmap_hint":     "버스 셀을 클릭하면 해당 버스의 위반 목록을 신호 흐름 탭에서 확인합니다",
        "all_buses":        "전체 버스",
        "sf_no_graph":      "그래프 빌드 대기 중  —  Wwise 연결 시 자동 시작",
        "sf_select_item":   "위에서 위반 항목을 선택하세요",
        "collapsed_fmt":    "[ ··· 중간 {}단계 축약 — 클릭하여 펼치기 ]",
        "decision_point":   "★ 라우팅 결정 지점",
        "cur_bus_label":    "현재 버스  ✗",
        "exp_bus_label":    "기대 버스  ✓",
    },
    "en": {
        "reconnect":      "⟳  Reconnect",
        "help_btn":       "?  Help",
        "help_title":     "Bus Routing Auditor — How to Use",
        "help_body": (
            "【 Connect 】\n"
            "• Launch Wwise and enable WAAPI (Project > User Preferences > Enable WAAPI)\n"
            "• Click ⟳ Reconnect. Graph builds automatically after connection\n"
            "• Project structure changes are detected and graph rebuilds in 1.5s automatically\n"
            "\n"
            "【 Rule Setup 】\n"
            "• Scan 1: asset name contains keyword → bus name must also contain that keyword\n"
            "• Scan 2: Sound's Work Unit / path contains keyword → bus name is checked\n"
            "• Use + button for OR conditions. Save rules before scanning\n"
            "\n"
            "【 Results List 】\n"
            "• Double-click violation → select asset in Wwise + focus Property Editor\n"
            "• ⟲ Batch Reroute: change OutputBus for selected assets in bulk\n"
            "• Search field supports name / WU / bus / expected keyword filtering\n"
            "\n"
            "【 Signal Flow Tab 】\n"
            "• Left bus tree — Red: direct violation bus, Orange: has violations in sub-buses\n"
            "• Click bus → filter asset list on right\n"
            "• Select asset → bottom graph: Sound → containers → WU → current bus ✗ → expected ✓\n"
            "• Click any graph node → focus that object in Wwise\n"
            "• Click ··· N node → expand collapsed middle layers\n"
            "\n"
            "【 Heatmap Tab 】\n"
            "• Violation rate by bus — green(0%) → yellow(<15%) → orange(<35%) → red(35%+)\n"
            "• Click cell → navigate to that bus in Signal Flow tab\n"
            "\n"
            "【 Multi-keyword OR Rules 】\n"
            "• Assets matching multiple rules (e.g. NPC_AMB_Walla): pass if ANY rule satisfied\n"
            "• Only flagged if ALL matching rules fail — shown as 'NPC or AMB'\n"
        ),
        "lang_toggle":    "KO",
        "tab1":           "  Scan 1  ·  Asset Name  ",
        "tab2":           "  Scan 2  ·  Work Unit  ",
        "rule_title":     "Rule Settings",
        "desc_name":      "If name contains keyword → bus name must also contain keyword",
        "desc_wu":        "If Work Unit / path contains keyword → bus name must also contain keyword",
        "kw_name":        "Asset Name Keyword",
        "kw_wu":          "Work Unit / Path Keyword",
        "bus_kw_hdr":     "→  Bus Name Keyword",
        "case_hdr":       "Case",
        "flag_unset":     "Also flag unset (inherited) bus as violation",
        "add_rule":       "+ Add Rule",
        "save_rules":     "Save Rules",
        "search_lbl":     "Search",
        "search_hint":    "Word search (e.g.: UI  /  AMB Metal  /  PC Attack)",
        "inherited":      "↑ Inherited",
        "overridden":     "◆ Overridden",
        "col_name":       "Asset Name",
        "col_work_unit":  "Work Unit",
        "col_cur_bus":    "Current Bus",
        "col_trigger":    "Violation Cause",
        "col_exp_kw":     "Expected Bus KW",
        "col_path":       "Full Path",
        "scan":           "▶  Run Scan",
        "view_wwise":     "⊙  View in Wwise",
        "reroute":        "⟲  Bulk Reroute",
        "select_all":     "Select All",
        "export_csv":     "↓  Export CSV",
        "connecting":     "Connecting to Wwise...",
        "connected_fmt":  "Connected  ·  {} buses",
        "connect_fail":   "Connection failed  —  Enable WAAPI in Project > User Preferences  ({})",
        "no_waapi":       "waapi-client not installed  →  run install.bat or  pip install waapi-client",
        "scanning":       "Scanning...",
        "scan_done_name": "[Name scan done]  {} Sounds  ·  {} violations",
        "scan_done_wu":   "[Work Unit scan done]  {} Sounds  ·  {} violations",
        "scan_fail":      "Scan failed: {}",
        "filter_applied": "Filtered  ·  {} / {}",
        "no_violations":  "{} total  ·  No violations ✓",
        "violations":     "{} total  ·  {} violations",
        "no_wwise":       "Not connected to Wwise.",
        "select_item":    "Please select an item.",
        "select_reroute": "Please select items to reroute.",
        "no_export":      "No results to export.",
        "rules_saved":    "Rules saved.",
        "rules_reset":    "Reset Rules",
        "rules_reset_confirm": "All saved rules will be deleted.\nContinue?",
        "save_title":     "Saved",
        "error_title":    "Error",
        "info_title":     "Info",
        "scan_error":     "Scan Error",
        "reroute_title":  "Bus Reroute",
        "reroute_fmt":    "Rerouting {} items.",
        "reroute_bus_sel":"Select target bus for each keyword group:",
        "cancel":         "Cancel",
        "apply_reroute":  "Apply Reroute",
        "reroute_done":   "{} items rerouted.",
        "reroute_partial":"{} done  /  {} failed\n\n{}",
        "partial_title":  "Partial Failure",
        "complete_title": "Complete",
        "csv_title":      "Export as CSV",
        "csv_done":       "Saved:\n{}",
        "not_found":      "Could not select object in Wwise.\nPlease find it manually in Project Explorer.",
        "bus_missing":    'Bus "{}" not found',
        "search_all":     "All",
        "save_reminder":  "⚠ Save rules before scanning",
        "flag_unset_note": "(All sub-assets under the violating top-level item are also shown)",
        "tip_kw_wu": (
            "┌─ Work Unit Keyword — How matching works ─────────────────\n"
            "│  A keyword matches if it appears in any of the following:\n"
            "│    · Work Unit name\n"
            "│    · Work Unit full path\n"
            "│\n"
            "│  ⚠ Actor-Mixer folder names are NOT searched.\n"
            "│     Only the WU file name/path is checked.\n"
            "│\n"
            "│  ⚠ Partial names also match (at word boundaries)\n"
            "│  e.g. keyword: AMB\n"
            "│      → AMB_Sounds ✓  /  Default_AMB ✓  /  AMB ✓\n"
            "│      → AMBIENT ✗  (no word boundary)\n"
            "│\n"
            "│  To target a specific Work Unit, enter its full name.\n"
            "│  e.g. search only 'NPC_Main' → keyword: NPC_Main\n"
            "└──────────────────────────────────────────────────────────"
        ),
        "tip_name": (
            "┌─ Scan 1  Asset Name ────────────────────────────────────\n"
            "│  Inspects the name of each Sound object.\n"
            "│\n"
            "│  How it works\n"
            "│  If the name contains an 'Asset Name Keyword' as a word token,\n"
            "│  the bus name must also contain the 'Bus Name Keyword'.\n"
            "│  A violation is flagged if it does not.\n"
            "│\n"
            "│  What is a word token?\n"
            "│  Words separated by _  /  Space  /  -  /  .  /  /  etc.\n"
            "│  'UI' matches UI_Click ✓, NPC_UI ✓\n"
            "│  but NOT BUILD ✗, QUIT ✗.\n"
            "│  Keywords containing '_' (e.g. 'UI_Mix') use consecutive token matching.\n"
            "│\n"
            "│  Example rule:  PC  →  PC\n"
            "│    PC_Attack_01  routed→  PC_Bus      ✓\n"
            "│    PC_Attack_01  routed→  NPC_Bus     ✗  (NPC ≠ PC)\n"
            "└──────────────────────────────────────────────────────────"
        ),
        "tip_wu": (
            "┌─ Scan 2  Work Unit / Path ──────────────────────────────\n"
            "│  Inspects the hierarchy path of each Sound object.\n"
            "│  Search targets: Work Unit name + Work Unit full path\n"
            "│                  + object parent path (excludes Sound's own name)\n"
            "│\n"
            "│  Example rule:  Path KW: UI  →  Bus KW: UI\n"
            "│    \\SFX\\UI\\Buttons\\Click_01  routed→  UI_Bus  ✓\n"
            "│    \\SFX\\UI\\Buttons\\Click_01  routed→  SFX_Bus ✗\n"
            "│\n"
            "│  ▸ Inherited filter  (yellow)\n"
            "│    Bus is inherited from a parent object\n"
            "│  ▸ Overridden filter  (red)\n"
            "│    Bus is explicitly set on this Sound\n"
            "└──────────────────────────────────────────────────────────"
        ),
        "tab_results":          "  Keyword / Search  ",
        "tab_results_name":     "  Keyword / Search · Asset Name  ",
        "tab_results_wu":       "  Keyword / Search · Work Unit  ",
        "tab_sf":               "  Signal Flow · Bus Analysis  ",
        "tab_sf_name":          "  Signal Flow · Asset Name  ",
        "tab_sf_wu":            "  Signal Flow · Work Unit  ",
        "tab_heatmap":          "  Heatmap  ",
        "tab_heatmap_name":     "  Heatmap · Asset Name  ",
        "tab_heatmap_wu":       "  Heatmap · Work Unit  ",
        "graph_building":   "Building graph...",
        "graph_ready_fmt":  "Graph ready  ·  {} objects",
        "graph_rebuild":    "⟳  Rebuild Graph",
        "no_scan_result":   "Run Scan 1 or Scan 2 first",
        "bus_tree_hdr":     "Violations by Bus",
        "sf_hdr":           "Signal Flow",
        "sf_hdr_name":      "Signal Flow  ·  Asset Name",
        "sf_hdr_wu":        "Signal Flow  ·  Work Unit",
        "hm_hdr_name":      "Bus Violation Heatmap  ·  Asset Name",
        "hm_hdr_wu":        "Bus Violation Heatmap  ·  Work Unit",
        "sf_hint":          "Click a violation to view its signal flow",
        "graph_not_ready":  "Graph not built  —  auto-starts on Wwise connect",
        "heatmap_hdr":      "Bus Violation Heatmap",
        "heatmap_hint":     "Click a bus cell to view violations in the Signal Flow tab",
        "all_buses":        "All Buses",
        "sf_no_graph":      "Waiting for graph build  —  starts automatically on connect",
        "sf_select_item":   "Select a violation above",
        "collapsed_fmt":    "[ ··· {} steps collapsed — click to expand ]",
        "decision_point":   "★ Routing Decision Point",
        "cur_bus_label":    "Current Bus  ✗",
        "exp_bus_label":    "Expected Bus  ✓",
    },
}

# ── Color System ─────────────────────────────────────────────────────────────
BG      = "#0D1117"   # main window bg
BG2     = "#161B22"   # card / rule panel
BG3     = "#1C2128"   # elevated panel / header areas
PANEL   = "#21262D"   # inputs, raised buttons
BORDER  = "#30363D"   # subtle borders
BORDER2 = "#444C56"   # hover-state borders
ACCENT  = "#58A6FF"   # primary blue
ACCENT2 = "#A78BFA"   # secondary purple (V2)
DANGER  = "#DA3633"   # danger
OK_CLR  = "#3FB950"   # success
WARN    = "#D29922"   # warning/amber
ERR_CLR = "#F85149"   # error red (bright)
FG      = "#E6EDF3"   # primary text
FG_DIM  = "#8B949E"   # secondary text
FG_MUT  = "#484F58"   # muted / placeholder
SEL_BG  = "#1F6FEB"   # treeview selection

# ── Typography ───────────────────────────────────────────────────────────────
_UI     = "Segoe UI"
_MN     = "Consolas"
FONT_H1    = (_UI, 11, "bold")
FONT_H2    = (_UI, 10, "bold")
FONT_UI    = (_UI,  9)
FONT_UIB   = (_UI,  9, "bold")
FONT_SM    = (_UI,  8)
FONT_CODE  = (_MN,  9)
FONT_CODE_B= (_MN,  9, "bold")
FONT_CODE_L= (_MN, 10, "bold")

# Legacy aliases — used directly in logic code, keep same names
MONO    = FONT_CODE
MONO_B  = FONT_CODE_B
MONO_LG = FONT_CODE_L

# ── Button animation presets  (bg, fg, hover_bg, press_bg) ───────────────────
_BP = {
    "primary": ("#1F6FEB", "#FFFFFF",  "#388BFD", "#1158C7"),
    "danger":  ("#3D0E11", "#F28B82",  "#5A1317", "#2A080A"),
    "ghost":   (PANEL,     FG,         "#2D333B", BG3),
    "add":     ("#0A2016", OK_CLR,     "#0F2E1E", "#071612"),
    "add_bus": ("#0A1830", ACCENT,     "#0E2244", "#071020"),
    "remove":  (PANEL,     FG_DIM,     "#3D1A1A", "#2A0F0F"),
    "lang":    ("#1E1833", "#BC8CFF",  "#271F42", "#140F24"),
    "icon":    (BG3,       FG_DIM,     PANEL,     BG2),
    "muted":   (BG2,       FG_DIM,     BG3,       BG),
}

FIND_CMD_PRIMARY   = ["FindInProjectExplorerSelectionChannel1","FindInProjectExplorer","FindInProjectExplorer1"]
SEARCH_FIELDS      = ["", "name", "work_unit", "current_bus", "expected_bus_keyword"]
SEARCH_FIELD_SKEYS = ["search_all", "col_name", "col_work_unit", "col_cur_bus", "col_exp_kw"]


# ── Animated button factory ───────────────────────────────────────────────────
def _ab(parent, text, cmd=None, preset="ghost", font=None, padx=14, pady=0, width=None, **kw):
    """Return an animated tk.Button with hover/press state transitions."""
    bg, fg, hov, prs = _BP[preset]
    extra = {"width": width} if width is not None else {}
    b = tk.Button(parent, text=text, command=cmd,
                  bg=bg, fg=fg, relief="flat", bd=0,
                  font=font or FONT_UIB, padx=padx, pady=pady + 6,
                  cursor="hand2", disabledforeground=FG_MUT,
                  activebackground=hov, activeforeground=fg,
                  **extra, **kw)
    def _enter(e):
        if str(b.cget("state")) != "disabled": b.config(bg=hov)
    def _leave(e):
        if str(b.cget("state")) != "disabled": b.config(bg=bg)
        else: b.config(bg=bg)
    def _press(e):
        if str(b.cget("state")) != "disabled": b.config(bg=prs)
    def _release(e):
        if str(b.cget("state")) != "disabled": b.config(bg=hov)
    b.bind("<Enter>",           _enter)
    b.bind("<Leave>",           _leave)
    b.bind("<Button-1>",        _press)
    b.bind("<ButtonRelease-1>", _release)
    return b


def _styled_entry(parent, var, width=16):
    """Entry with focus-glow animation."""
    e = tk.Entry(parent, textvariable=var,
                 bg=PANEL, fg=FG, insertbackground=FG,
                 width=width, font=FONT_CODE, relief="flat",
                 highlightthickness=1,
                 highlightbackground=BORDER,
                 highlightcolor=ACCENT)
    e.bind("<FocusIn>",  lambda ev: e.config(highlightbackground=ACCENT))
    e.bind("<FocusOut>", lambda ev: e.config(highlightbackground=BORDER))
    return e


class BusRoutingAuditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Bus Routing Auditor  —  Wwise")
        sh = self.root.winfo_screenheight()
        win_h = int(sh * 0.80)
        win_w = max(1400, int(win_h * 1.75))
        self.root.geometry(f"{win_w}x{win_h}")
        self.root.minsize(1000, 680)
        self.root.configure(bg=BG)
        self.client = None
        self._was_connected = False
        self.results_name = []; self.results_wu = []
        self.filtered_name = []; self.filtered_wu = []
        self._scanned_name = False; self._scanned_wu = False
        self.buses = {}
        self._find_cmd = None
        self._sort_reverse = {}
        self._status_anim_id = None
        self.config = self._load_config()
        self._lang = "ko"
        self._lang_updaters = []
        self._nb = None; self._lang_btn = None
        self._proj_name = ""
        self._cur_status_key = None
        self._cur_status_args = ()
        self._cur_status_color = FG_DIM
        self._name_show_inherited = tk.BooleanVar(value=True)
        self._name_show_override  = tk.BooleanVar(value=True)
        self._search_field_idx_name = None; self._search_field_idx_wu = None
        # V2: graph cache
        import threading as _threading
        self._graph = {}
        self._graph_ready = False
        self._graph_lock = _threading.Lock()
        self._bus_hierarchy = {}   # path → {id, name, parent_path}
        self._subscriptions = []   # WAAPI subscription handles
        self._debounce_timer = None
        # V2: signal flow / heatmap — per-mode ctx dicts
        self._sf_ctx = {}   # mode('name'|'wu') → widget/state dict
        self._hm_ctx = {}
        self._sf_expanded_paths = set()
        self._type_icons = {}   # type_name → PhotoImage
        self._apply_styles()
        self._build_ui()
        self._load_type_icons()
        self._start_wwise_watchdog()
        self.root.after(200, lambda: threading.Thread(target=self._connect_waapi, daemon=True).start())

    # ── i18n ─────────────────────────────────────────────────────────────────
    def _t(self, key):
        return STRINGS[self._lang].get(key, STRINGS["ko"].get(key, key))

    def _toggle_lang(self):
        self._lang = "en" if self._lang == "ko" else "ko"
        self._refresh_lang()

    def _refresh_lang(self):
        for fn in self._lang_updaters:
            try: fn()
            except Exception: pass
        # 상태 메시지 재번역
        if self._cur_status_key:
            try:
                msg = self._t(self._cur_status_key)
                if self._cur_status_args:
                    msg = msg.format(*self._cur_status_args)
                self._status_lbl.config(text=msg, fg=self._cur_status_color)
                self._status_dot.config(fg=self._cur_status_color)
            except Exception:
                pass
        # 프로젝트 이름 레이블 갱신
        if hasattr(self, '_proj_lbl') and self._proj_name:
            self._proj_lbl.config(text=self._proj_name)

    # ── Config ───────────────────────────────────────────────────────────────
    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for k, v in DEFAULT_CONFIG.items():
                    data.setdefault(k, v)
                return data
            except Exception: pass
        return json.loads(json.dumps(DEFAULT_CONFIG))

    def _save_config(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)

    # ── Watchdog ─────────────────────────────────────────────────────────────
    def _start_wwise_watchdog(self):
        def _watch():
            while True:
                time.sleep(3)
                if not self._was_connected: continue
                try:
                    s = socket.create_connection(("127.0.0.1", 8080), timeout=2); s.close()
                except Exception:
                    self.root.after(0, self.root.destroy); return
        threading.Thread(target=_watch, daemon=True).start()

    # ── WAAPI ─────────────────────────────────────────────────────────────────
    def _show_help(self):
        dlg = tk.Toplevel(self.root)
        dlg.title(self._t("help_title"))
        dlg.configure(bg=BG)
        dlg.resizable(True, True)
        dlg.grab_set()

        # 헤더
        hdr = tk.Frame(dlg, bg=BG3)
        hdr.pack(fill="x")
        tk.Frame(hdr, bg=ACCENT, height=2).pack(fill="x", side="bottom")
        tk.Label(hdr, text=self._t("help_title"), bg=BG3, fg=FG,
                 font=FONT_H2, anchor="w").pack(padx=16, pady=10)

        # 본문 (스크롤 가능 텍스트)
        body = tk.Frame(dlg, bg=BG)
        body.pack(fill="both", expand=True, padx=2, pady=2)
        vsb = ttk.Scrollbar(body, orient="vertical")
        vsb.pack(side="right", fill="y")
        txt = tk.Text(body, bg=BG2, fg=FG, font=FONT_UI, wrap="word",
                      relief="flat", borderwidth=0, padx=16, pady=12,
                      yscrollcommand=vsb.set, state="normal", cursor="arrow")
        txt.pack(fill="both", expand=True)
        vsb.config(command=txt.yview)

        # 색상 태그
        txt.tag_config("section", foreground=ACCENT, font=FONT_UIB)
        txt.tag_config("body",    foreground=FG_DIM, font=FONT_UI)

        body_text = self._t("help_body")
        for line in body_text.split("\n"):
            if line.startswith("【"):
                txt.insert("end", line + "\n", "section")
            else:
                txt.insert("end", line + "\n", "body")
        txt.config(state="disabled")

        # 닫기
        btn_f = tk.Frame(dlg, bg=BG3)
        btn_f.pack(fill="x")
        tk.Frame(btn_f, bg=BORDER, height=1).pack(fill="x", side="top")
        tk.Button(btn_f, text="닫기", command=dlg.destroy,
                  bg=PANEL, fg=FG_DIM, activebackground=BORDER2,
                  activeforeground=FG, relief="flat", font=FONT_UIB,
                  padx=20, pady=6, cursor="hand2").pack(side="right", padx=12, pady=8)

        # 크기 조정
        dlg.update_idletasks()
        dlg.geometry("560x540")

    def _connect_waapi(self):
        self._set_status(self._t("connecting"), WARN, pulsing=True)
        if not WAAPI_AVAILABLE:
            self._set_status(self._t("no_waapi"), ERR_CLR); return
        try:
            if self.client:
                # 기존 구독 해제
                for handle in self._subscriptions:
                    try: self.client.unsubscribe(handle)
                    except Exception: pass
                self._subscriptions.clear()
                try: self.client.disconnect()
                except Exception: pass
            self.client = WaapiClient(url=WAAPI_URL)
            self._find_cmd = None
            self._fetch_buses()
            r = self.client.call("ak.wwise.core.object.get",
                {"from": {"ofType": ["Project"]}, "options": {"return": ["name"]}})
            items = r.get("return", [])
            proj_name = items[0]["name"] if items else "—"
            self._was_connected = True
            self._set_proj_name(proj_name)
            self._set_status(self._t("connected_fmt").format(len(self.buses)), OK_CLR,
                             key="connected_fmt", args=(len(self.buses),))
            threading.Thread(target=self._build_graph, daemon=True).start()
        except Exception as e:
            self.client = None
            self._set_proj_name("")
            self._set_status(self._t("connect_fail").format(e), ERR_CLR)

    def _fetch_buses(self):
        r = self.client.call("ak.wwise.core.object.get",
            {"from": {"ofType": ["Bus","AuxBus"]}, "options": {"return": ["id","name","path"]}})
        self.buses = {obj["name"]: obj["id"] for obj in (r or {}).get("return", [])}

    _HIERARCHY_TYPES = ["Sound","ActorMixer","BlendContainer","RandomSequenceContainer","SwitchContainer","WorkUnit","Folder"]

    def _get_all_sounds(self):
        if self._graph_ready:
            with self._graph_lock:
                all_objects = [
                    {"id": v["id"], "name": v["name"], "path": k,
                     "type": v["type"], "@OutputBus": v["output_bus"],
                     "@OverrideOutput": v["override_output"], "workunit": v["workunit"]}
                    for k, v in self._graph.items()
                ]
        else:
            r = self.client.call("ak.wwise.core.object.get", {
                "from": {"ofType": self._HIERARCHY_TYPES},
                "options": {"return": ["id","name","path","type","@OutputBus","@OverrideOutput","workunit"]},
            })
            all_objects = (r or {}).get("return", [])
        effective = self._resolve_effective_buses(all_objects)
        _DEFAULT = "masteraudiobus"
        sounds = []
        for obj in all_objects:
            if obj.get("type") != "Sound": continue
            path = obj.get("path", "")
            eff = effective.get(path) or {"name": "Master Audio Bus", "id": ""}
            if eff.get("name", "").replace(" ", "").lower() == _DEFAULT:
                own = obj.get("@OutputBus") or {}
                own_name = own.get("name", "")
                if own_name and own_name.replace(" ", "").lower() != _DEFAULT:
                    eff = own
            obj["_effective_bus_name"] = eff.get("name", "")
            obj["_effective_bus_id"]   = eff.get("id", "")
            obj["_bus_inherited"]      = not obj.get("@OverrideOutput", False)
            sounds.append(obj)
        return sounds

    def _resolve_effective_buses(self, all_objects):
        DEFAULT_BUS = "masteraudiobus"
        overrides = {}; stale = {}
        for obj in all_objects:
            bus = obj.get("@OutputBus") or {}
            bus_name = bus.get("name", "")
            if not bus_name: continue
            path = obj["path"]
            if obj.get("@OverrideOutput", False):
                overrides[path] = bus
            elif bus_name.replace(" ","").lower() != DEFAULT_BUS and obj.get("type") != "Sound":
                stale[path] = bus
        override_cache = {}

        def _find_override(path):
            chain = []; cur = path
            while True:
                if cur in overrides:
                    val = overrides[cur]; override_cache[cur] = val
                    for p in chain: override_cache[p] = val
                    return val
                if cur in override_cache:
                    val = override_cache[cur]
                    for p in chain: override_cache[p] = val
                    return val
                chain.append(cur)
                sep = cur.rfind("\\")
                if sep <= 0: break
                cur = cur[:sep]
            for p in chain: override_cache[p] = {}
            return {}

        def _find_stale_highest(path):
            cur = path; last_val = {}
            while True:
                if cur in stale: last_val = stale[cur]
                sep = cur.rfind("\\")
                if sep <= 0: break
                cur = cur[:sep]
            return last_val

        final = {}
        for obj in all_objects:
            path = obj["path"]
            bus = _find_override(path)
            if not bus: bus = _find_stale_highest(path)
            final[path] = bus
        return final

    def _select_in_wwise(self, object_id):
        if not self.client: return
        if self._find_cmd:
            try:
                self.client.call("ak.wwise.ui.commands.execute",
                    {"command": self._find_cmd, "objects": [object_id]})
            except Exception:
                self._find_cmd = None
        if not self._find_cmd:
            for cmd in FIND_CMD_PRIMARY:
                try:
                    self.client.call("ak.wwise.ui.commands.execute",
                        {"command": cmd, "objects": [object_id]})
                    self._find_cmd = cmd; break
                except Exception: continue
            else:
                self.root.after(0, lambda: messagebox.showwarning(
                    self._t("info_title"), self._t("not_found"), parent=self.root))
                return
        try:
            self.client.call("ak.wwise.ui.commands.execute",
                {"command": "Inspect", "objects": [object_id]})
        except Exception: pass

    def _set_output_bus(self, object_id, bus_id):
        self.client.call("ak.wwise.core.object.setReference",
            {"object": object_id, "reference": "OutputBus", "value": bus_id})

    @staticmethod
    def _word_match(text, keyword, cs):
        flags = 0 if cs else re.IGNORECASE
        sep = r'[ _\-\./\\()\[\]{},;:\s]'
        pat = r'(?:^|' + sep + r')' + re.escape(keyword) + r'(?:$|' + sep + r')'
        return bool(re.search(pat, text, flags))

    def _bus_display(self, bus_name, inherited):
        return (bus_name + "  ↑") if (bus_name and inherited) else bus_name

    def _check_name_rules(self, sounds):
        rules = self.config.get("name_rules", [])
        flag_unset = self.config.get("flag_unset_bus", True)
        violations = []
        for sound in sounds:
            name = sound.get("name",""); path = sound.get("path","")
            bus_name = sound.get("_effective_bus_name",""); bus_id = sound.get("_effective_bus_id","")
            inherited = sound.get("_bus_inherited", False)
            wu_obj = sound.get("workunit") or {}; wu_name = wu_obj.get("name","")
            no_bus = not bus_name
            # collect matching rules
            matching = []
            for rule in rules:
                cs = rule.get("case_sensitive", False)
                all_src = [rule["keyword"]] + rule.get("extra_keywords", [])
                if any(self._word_match(name, sk, cs) for sk in all_src):
                    matching.append(rule)
            if not matching: continue
            # check each matching rule — pass if ANY is satisfied
            failed = []
            for rule in matching:
                cs = rule.get("case_sensitive", False)
                all_bus = [rule["expected_bus_keyword"]] + rule.get("extra_bus_keywords", [])
                mismatch = (not no_bus) and not any(self._word_match(bus_name, bk, cs) for bk in all_bus)
                if mismatch or (no_bus and flag_unset):
                    failed.append((rule, all_bus))
            if len(failed) < len(matching): continue  # at least one rule satisfied → pass
            if not failed: continue
            # all matching rules failed → one combined violation
            trigger_parts = [f'이름에 "{" | ".join([r["keyword"]] + r.get("extra_keywords",[]))}" 포함' for r, _ in failed]
            expected_parts = [" | ".join(ab) for _, ab in failed]
            violations.append({"id": sound.get("id",""), "name": name, "path": path,
                "work_unit": wu_name, "current_bus": self._bus_display(bus_name, inherited),
                "current_bus_id": bus_id,
                "trigger": " or ".join(trigger_parts) if len(trigger_parts) > 1 else trigger_parts[0],
                "expected_bus_keyword": " or ".join(expected_parts) if len(expected_parts) > 1 else expected_parts[0],
                "unset": no_bus, "inherited": inherited, "scan_type": "name"})
        return violations

    def _check_workunit_rules(self, sounds):
        rules = self.config.get("workunit_rules", [])
        flag_unset = self.config.get("flag_unset_bus", True)
        violations = []
        for sound in sounds:
            name = sound.get("name",""); path = sound.get("path","")
            bus_name = sound.get("_effective_bus_name",""); bus_id = sound.get("_effective_bus_id","")
            inherited = sound.get("_bus_inherited", False)
            wu_obj = sound.get("workunit") or {}; wu_name = wu_obj.get("name",""); wu_path = wu_obj.get("path","")
            search = f"{wu_name} {wu_path}"
            no_bus = not bus_name
            # collect matching rules
            matching = []
            for rule in rules:
                cs = rule.get("case_sensitive", False)
                all_src = [rule["work_unit_keyword"]] + rule.get("extra_work_unit_keywords", [])
                if any(self._word_match(search, sk, cs) for sk in all_src):
                    matching.append(rule)
            if not matching: continue
            # check each matching rule — pass if ANY is satisfied
            failed = []
            for rule in matching:
                cs = rule.get("case_sensitive", False)
                all_kws = [rule["expected_bus_keyword"]] + rule.get("extra_bus_keywords", [])
                mismatch = (not no_bus) and not any(self._word_match(bus_name, ek, cs) for ek in all_kws)
                if mismatch or (no_bus and flag_unset):
                    failed.append((rule, all_kws))
            if len(failed) < len(matching): continue  # at least one rule satisfied → pass
            if not failed: continue
            # all matching rules failed → one combined violation
            trigger_parts = [f'경로에 "{" | ".join([r["work_unit_keyword"]] + r.get("extra_work_unit_keywords",[]))}" 포함' for r, _ in failed]
            expected_parts = [" | ".join(ak) for _, ak in failed]
            violations.append({"id": sound.get("id",""), "name": name, "path": path,
                "work_unit": wu_name, "current_bus": self._bus_display(bus_name, inherited),
                "current_bus_id": bus_id,
                "trigger": " or ".join(trigger_parts) if len(trigger_parts) > 1 else trigger_parts[0],
                "expected_bus_keyword": " or ".join(expected_parts) if len(expected_parts) > 1 else expected_parts[0],
                "unset": no_bus, "inherited": inherited, "scan_type": "workunit"})
        return violations

    def _run_scan(self, mode):
        if not self.client:
            messagebox.showerror(self._t("error_title"), self._t("no_wwise"), parent=self.root); return
        self._set_status(self._t("scanning"), WARN)
        self.btn_scan_name.config(state="disabled"); self.btn_scan_wu.config(state="disabled")
        def worker():
            try:
                sounds = self._get_all_sounds()
                if mode == "name":
                    self.results_name = self._check_name_rules(sounds)
                    self._scanned_name = True
                    results = self.results_name
                    self.root.after(0, lambda: self._apply_filter("name"))
                    self.root.after(0, lambda: self._set_count(self.lbl_count_name, len(sounds), len(results)))
                    _c = ERR_CLR if results else OK_CLR
                    self.root.after(0, lambda c=_c, s=len(sounds), r=len(results): self._set_status(
                        self._t("scan_done_name").format(s, r), c,
                        key="scan_done_name", args=(s, r)))
                else:
                    self.results_wu = self._check_workunit_rules(sounds)
                    self._scanned_wu = True
                    results = self.results_wu
                    self.root.after(0, lambda: self._apply_filter("workunit"))
                    self.root.after(0, lambda: self._set_count(self.lbl_count_wu, len(sounds), len(results)))
                    _c = ERR_CLR if results else OK_CLR
                    self.root.after(0, lambda c=_c, s=len(sounds), r=len(results): self._set_status(
                        self._t("scan_done_wu").format(s, r), c,
                        key="scan_done_wu", args=(s, r)))
                # V2: update signal flow and heatmap panels
                self.root.after(0, self._refresh_v2_panels)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror(self._t("scan_error"), str(e), parent=self.root))
                self.root.after(0, lambda: self._set_status(self._t("scan_fail").format(e), ERR_CLR))
            finally:
                self.root.after(0, lambda: self.btn_scan_name.config(state="normal"))
                self.root.after(0, lambda: self.btn_scan_wu.config(state="normal"))
        threading.Thread(target=worker, daemon=True).start()

    def _apply_filter(self, mode):
        is_name = (mode == "name")
        src    = self.results_name if is_name else self.results_wu
        tree   = self.tree_name    if is_name else self.tree_wu
        search = (self._search_var_name if is_name else self._search_var_wu).get().strip()
        search_tokens = [t for t in WORD_SEP.split(search) if t]
        filtered = []
        for r in src:
            if is_name:
                is_inh = r.get("inherited", True)
                if is_inh     and not self._name_show_inherited.get(): continue
                if not is_inh and not self._name_show_override.get():  continue
            else:
                is_inh = r.get("inherited", True)
                if is_inh     and not self._wu_show_inherited.get(): continue
                if not is_inh and not self._wu_show_override.get():  continue
            if search_tokens:
                fv = self._search_field_idx_name if is_name else self._search_field_idx_wu
                field_key = SEARCH_FIELDS[fv.get() if fv else 0]
                if field_key:
                    target = r.get(field_key, "")
                else:
                    target = " ".join([r.get("name",""), r.get("work_unit",""), r.get("path",""),
                                       r.get("current_bus",""), r.get("expected_bus_keyword","")])
                hay = {t.upper() for t in WORD_SEP.split(target) if t}
                if not all(st.upper() in hay for st in search_tokens): continue
            filtered.append(r)
        tree.delete(*tree.get_children())
        if is_name: self.filtered_name = filtered
        else:       self.filtered_wu   = filtered
        for i, r in enumerate(filtered):
            sfx = "e" if i % 2 == 0 else "o"
            if r.get("unset"):       row_tag = f"uns_{sfx}"
            elif r.get("inherited"): row_tag = f"inh_{sfx}"
            else:                    row_tag = f"ovr_{sfx}"
            tags = (row_tag,)
            tree.insert("", "end", values=(
                r["name"], r["work_unit"], r["current_bus"],
                r["trigger"], r["expected_bus_keyword"], r["path"],
            ), tags=tags)
        total = len(src); shown = len(filtered)
        scanned = self._scanned_name if is_name else self._scanned_wu
        lbl = self.lbl_count_name if is_name else self.lbl_count_wu
        if search_tokens or (not is_name and not (self._wu_show_inherited.get() and self._wu_show_override.get())):
            lbl.config(text=self._t("filter_applied").format(shown, total), fg=WARN if shown < total else FG_DIM)
        else:
            if not scanned: lbl.config(text="—", fg=FG_DIM)
            elif shown == 0:
                lbl.config(text=self._t("no_violations").format(total), fg=OK_CLR)
                tree.insert("", "end",
                    values=("✓  " + self._t("no_violations").format(total), "", "", "", "", ""),
                    tags=("ok_msg",))
            else: lbl.config(text=self._t("violations").format(total, shown), fg=ERR_CLR)

    # ── ttk Styles ───────────────────────────────────────────────────────────
    def _load_type_icons(self):
        """Wwise 설치 폴더에서 오브젝트 타입 아이콘을 로드."""
        import glob as _glob
        from tkinter import PhotoImage
        candidates = _glob.glob(r"C:\Audiokinetic\*\Authoring\Data\Themes\classic\images\ObjectIcons")
        if not candidates:
            return
        d = candidates[-1]   # 가장 최신 버전

        _MAP = {
            "Sound":                   "ObjectIcons_SoundFX_nor.png",
            "RandomSequenceContainer": "ObjectIcons_RandomSequenceContainer_nor.png",
            "BlendContainer":          "ObjectIcons_BlendContainer_nor.png",
            "SwitchContainer":         "ObjectIcons_SwitchContainer_nor.png",
            "ActorMixer":              "ObjectIcons_ActorMixer_nor.png",
            "Folder":                  "ObjectIcons_Folder_nor.png",
            "PhysicalFolder":          "ObjectIcons_PhysicalFolder_nor.png",
            "WorkUnit":                "ObjectIcons_Workunit_nor.png",
            "Bus":                     "ObjectIcons_Bus_nor.png",
            "AuxBus":                  "ObjectIcons_AuxBus_nor.png",
        }
        import os
        for ttype, fname in _MAP.items():
            path = os.path.join(d, fname)
            if os.path.exists(path):
                try:
                    self._type_icons[ttype] = PhotoImage(file=path)
                except Exception:
                    pass

    def _apply_styles(self):
        s = ttk.Style(); s.theme_use("clam")

        # Notebook / Tabs
        s.configure("TNotebook", background=BG, borderwidth=0,
                    tabmargins=[0, 4, 0, 0])
        s.configure("TNotebook.Tab",
                    background=BG2, foreground=FG_MUT,
                    padding=[18, 8], font=FONT_UIB,
                    borderwidth=0, relief="flat",
                    focuscolor=BG2)
        s.map("TNotebook.Tab",
              background=[("selected", BG3),  ("active", PANEL)],
              foreground=[("selected", ACCENT), ("active", FG_DIM)],
              font=[("selected", (_UI, 9, "bold"))],
              expand=[("selected", [0, 2, 0, 0])])

        # Treeview
        s.configure("Treeview",
                    background=BG2, foreground=FG,
                    fieldbackground=BG2,
                    rowheight=26,
                    font=FONT_CODE,
                    borderwidth=0,
                    relief="flat")
        s.configure("Treeview.Heading",
                    background=BG3, foreground=FG_DIM,
                    font=FONT_UIB, relief="flat",
                    padding=[8, 6])
        s.map("Treeview",
              background=[("selected", SEL_BG)],
              foreground=[("selected", "#FFFFFF")])
        s.map("Treeview.Heading",
              background=[("active", PANEL)])

        # Scrollbars
        s.configure("Vertical.TScrollbar",
                    background=PANEL, troughcolor=BG2,
                    arrowcolor=FG_DIM, borderwidth=0,
                    relief="flat", width=8)
        s.configure("Horizontal.TScrollbar",
                    background=PANEL, troughcolor=BG2,
                    arrowcolor=FG_DIM, borderwidth=0,
                    relief="flat", width=8)
        s.map("Vertical.TScrollbar",   background=[("active", BORDER2)])
        s.map("Horizontal.TScrollbar", background=[("active", BORDER2)])

        # Combobox
        s.configure("TCombobox",
                    fieldbackground=PANEL, background=BG3,
                    foreground=FG, selectbackground=PANEL,
                    selectforeground=FG, insertcolor=FG,
                    arrowcolor=FG_DIM, borderwidth=0,
                    relief="flat", padding=[6, 4])
        s.map("TCombobox",
              fieldbackground=[("readonly", PANEL), ("readonly !focus", PANEL)],
              foreground=[("readonly", FG), ("readonly !focus", FG)],
              selectbackground=[("readonly", PANEL), ("readonly !focus", PANEL)],
              selectforeground=[("readonly", FG), ("readonly !focus", FG)],
              arrowcolor=[("active", ACCENT), ("pressed", ACCENT)])

    # ── Main Window ───────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Header bar ──────────────────────────────────────────────────────
        hdr = tk.Frame(self.root, bg=BG3, height=52)
        hdr.pack(fill="x"); hdr.pack_propagate(False)

        # Left: app identity
        id_frame = tk.Frame(hdr, bg=BG3)
        id_frame.pack(side="left", padx=(16, 0), pady=0)
        tk.Label(id_frame, text="◈", bg=BG3, fg=ACCENT,
                 font=(_UI, 16)).pack(side="left", padx=(0, 8))
        tk.Label(id_frame, text="Bus Routing Auditor", bg=BG3, fg=FG,
                 font=FONT_H1).pack(side="left")
        tk.Label(id_frame, text=f"  {VERSION}", bg=BG3, fg=FG_MUT,
                 font=FONT_SM).pack(side="left", pady=(3, 0))

        # Right: buttons
        btn_area = tk.Frame(hdr, bg=BG3)
        btn_area.pack(side="right", padx=(0, 12))

        self._lang_btn = _ab(btn_area, self._t("lang_toggle"),
                             self._toggle_lang, preset="lang",
                             font=FONT_UIB, padx=12)
        self._lang_btn.pack(side="right", padx=(4, 0), pady=10)
        self._lang_updaters.append(lambda: self._lang_btn.config(text=self._t("lang_toggle")))

        btn_rc = _ab(btn_area, self._t("reconnect"),
                     lambda: threading.Thread(target=self._connect_waapi, daemon=True).start(),
                     preset="ghost", font=FONT_UI, padx=12)
        btn_rc.pack(side="right", padx=4, pady=10)
        self._lang_updaters.append(lambda w=btn_rc: w.config(text=self._t("reconnect")))

        btn_help = _ab(btn_area, self._t("help_btn"), self._show_help,
                       preset="ghost", font=FONT_UI, padx=12)
        btn_help.pack(side="right", padx=(0, 0), pady=10)
        self._lang_updaters.append(lambda w=btn_help: w.config(text=self._t("help_btn")))

        # Center: status — 프로젝트 이름 | 상태 메시지 분리
        status_area = tk.Frame(hdr, bg=BG3)
        status_area.pack(side="left", fill="x", expand=True, padx=20)
        self._status_dot = tk.Label(status_area, text="●", bg=BG3, fg=FG_MUT,
                                    font=(_UI, 10))
        self._status_dot.pack(side="left", padx=(0, 6))
        # 프로젝트 이름 레이블 (연결 후 표시)
        self._proj_lbl = tk.Label(status_area, text="", bg=BG3,
                                  fg=ACCENT, font=FONT_UIB, anchor="w")
        self._proj_lbl.pack(side="left")
        # 구분자 (프로젝트 이름 있을 때만 표시)
        self._proj_sep = tk.Label(status_area, text="", bg=BG3,
                                  fg=FG_MUT, font=FONT_UI)
        self._proj_sep.pack(side="left", padx=(4, 4))
        # 상태 메시지
        self._status_lbl = tk.Label(status_area, text="초기화 중...", bg=BG3,
                                    fg=FG_DIM, font=FONT_UI, anchor="w")
        self._status_lbl.pack(side="left", fill="x")

        # Accent separator line
        tk.Frame(self.root, bg=ACCENT, height=2).pack(fill="x")

        # ── Notebook ────────────────────────────────────────────────────────
        nb = ttk.Notebook(self.root)
        nb.pack(fill="both", expand=True)
        self._nb = nb

        # ── 스캔 1 (상위 탭) ──
        outer1 = tk.Frame(nb, bg=BG); nb.add(outer1, text=self._t("tab1"))
        self._lang_updaters.append(lambda: self._nb.tab(0, text=self._t("tab1")))
        nb1 = ttk.Notebook(outer1); nb1.pack(fill="both", expand=True)
        self._nb1 = nb1

        s1_res = tk.Frame(nb1, bg=BG); nb1.add(s1_res, text=self._t("tab_results"))
        self._lang_updaters.append(lambda: self._nb1.tab(0, text=self._t("tab_results")))
        self._build_tab(s1_res, "name")

        s1_sf = tk.Frame(nb1, bg=BG); nb1.add(s1_sf, text=self._t("tab_sf"))
        self._lang_updaters.append(lambda: self._nb1.tab(1, text=self._t("tab_sf")))
        self._build_signal_flow_tab(s1_sf, mode='name')

        s1_hm = tk.Frame(nb1, bg=BG); nb1.add(s1_hm, text=self._t("tab_heatmap"))
        self._lang_updaters.append(lambda: self._nb1.tab(2, text=self._t("tab_heatmap")))
        self._build_heatmap_tab(s1_hm, mode='name')

        # ── 스캔 2 (상위 탭) ──
        outer2 = tk.Frame(nb, bg=BG); nb.add(outer2, text=self._t("tab2"))
        self._lang_updaters.append(lambda: self._nb.tab(1, text=self._t("tab2")))
        nb2 = ttk.Notebook(outer2); nb2.pack(fill="both", expand=True)
        self._nb2 = nb2

        s2_res = tk.Frame(nb2, bg=BG); nb2.add(s2_res, text=self._t("tab_results"))
        self._lang_updaters.append(lambda: self._nb2.tab(0, text=self._t("tab_results")))
        self._build_tab(s2_res, "workunit")

        s2_sf = tk.Frame(nb2, bg=BG); nb2.add(s2_sf, text=self._t("tab_sf"))
        self._lang_updaters.append(lambda: self._nb2.tab(1, text=self._t("tab_sf")))
        self._build_signal_flow_tab(s2_sf, mode='wu')

        s2_hm = tk.Frame(nb2, bg=BG); nb2.add(s2_hm, text=self._t("tab_heatmap"))
        self._lang_updaters.append(lambda: self._nb2.tab(2, text=self._t("tab_heatmap")))
        self._build_heatmap_tab(s2_hm, mode='wu')

    # ── Tab ──────────────────────────────────────────────────────────────────
    def _build_tab(self, parent, mode):
        is_name  = (mode == "name")
        rule_key = "name_rules" if is_name else "workunit_rules"
        reg = self._lang_updaters

        # ── Rule Panel ──────────────────────────────────────────────────────
        outer = tk.Frame(parent, bg=BORDER); outer.pack(fill="x", padx=12, pady=(10, 0))
        rp = tk.Frame(outer, bg=BG2); rp.pack(fill="both", padx=1, pady=(0, 1))

        # Top accent bar
        tk.Frame(rp, bg=ACCENT, height=2).pack(fill="x")

        # Panel header
        ph = tk.Frame(rp, bg=BG2); ph.pack(fill="x", padx=14, pady=(10, 6))

        lbl_rt = tk.Label(ph, text=self._t("rule_title"), bg=BG2, fg=FG, font=FONT_H2)
        lbl_rt.pack(side="left")
        reg.append(lambda w=lbl_rt: w.config(text=self._t("rule_title")))

        sep = tk.Frame(ph, bg=BORDER, width=1); sep.pack(side="left", fill="y", padx=12, pady=2)

        desc_key = "desc_name" if is_name else "desc_wu"
        lbl_desc = tk.Label(ph, text=self._t(desc_key), bg=BG2, fg=FG_DIM, font=FONT_UI)
        lbl_desc.pack(side="left")
        reg.append(lambda w=lbl_desc, k=desc_key: w.config(text=self._t(k)))

        tip_key = "tip_name" if is_name else "tip_wu"
        help_btn = tk.Label(ph, text=" ? ", bg=PANEL, fg=ACCENT, font=FONT_UIB,
                            cursor="question_arrow", relief="flat")
        help_btn.pack(side="left", padx=(8, 0))
        self._attach_tooltip(help_btn, lambda k=tip_key: self._t(k))

        # Column headers
        col_hdr = tk.Frame(rp, bg=BG3); col_hdr.pack(fill="x", padx=14, pady=(4, 2))
        kw_key = "kw_name" if is_name else "kw_wu"

        lbl_kw = tk.Label(col_hdr, text=self._t(kw_key), bg=BG3, fg=FG_MUT,
                          font=FONT_SM, width=27, anchor="w")
        lbl_kw.grid(row=0, column=0, padx=(4, 0))
        reg.append(lambda w=lbl_kw, k=kw_key: w.config(text=self._t(k)))

        if not is_name:
            kw_tip = tk.Label(col_hdr, text=" ? ", bg=PANEL, fg=ACCENT,
                              font=FONT_UIB, cursor="question_arrow", relief="flat")
            kw_tip.grid(row=0, column=1, padx=(2, 6))
            self._attach_tooltip(kw_tip, lambda: self._t("tip_kw_wu"))
        else:
            tk.Label(col_hdr, text="", bg=BG3, width=4).grid(row=0, column=1)

        lbl_bus_kw = tk.Label(col_hdr, text=self._t("bus_kw_hdr"), bg=BG3, fg=FG_MUT,
                              font=FONT_SM, width=22, anchor="w")
        lbl_bus_kw.grid(row=0, column=2, padx=4)
        reg.append(lambda w=lbl_bus_kw: w.config(text=self._t("bus_kw_hdr")))

        lbl_case = tk.Label(col_hdr, text=self._t("case_hdr"), bg=BG3, fg=FG_MUT,
                            font=FONT_SM, width=8, anchor="w")
        lbl_case.grid(row=0, column=3, padx=4)
        reg.append(lambda w=lbl_case: w.config(text=self._t("case_hdr")))

        # Rule rows container
        rows_frame = tk.Frame(rp, bg=BG2); rows_frame.pack(fill="x", padx=14, pady=(0, 4))
        rule_rows = []

        # ── add_row ──────────────────────────────────────────────────────────
        def add_row(kw="", bus="", cs=False, extra_src=None, extra_buses=None):
            row_frame = tk.Frame(rows_frame, bg=BG2, pady=1)
            row_frame.pack(fill="x")

            # Subtle separator line above each row
            tk.Frame(row_frame, bg=BORDER, height=1).pack(fill="x")

            kw_var  = tk.StringVar(value=kw)
            bus_var = tk.StringVar(value=bus)
            cs_var  = tk.BooleanVar(value=cs)
            src_extra_list = []; bus_extra_list = []

            g = tk.Frame(row_frame, bg=BG2); g.pack(fill="x", pady=2)

            # col 0: or-label placeholder (src side)
            # col 1: source entry
            # col 2: + button (src)
            # col 3: arrow
            # col 4: or-label placeholder (bus side)
            # col 5: bus entry
            # col 6: + button (bus)
            # col 7: case checkbox
            # col 8: × remove button

            tk.Label(g, bg=BG2, width=3).grid(row=0, column=0)
            _styled_entry(g, kw_var, 18).grid(row=0, column=1, padx=(0, 2), pady=2, ipady=3)

            src_add = _ab(g, "+", lambda: add_src_extra(), preset="add",
                          font=FONT_CODE_B, padx=6, pady=0, width=2)
            src_add.grid(row=0, column=2, padx=2)

            tk.Label(g, text="→", bg=BG2, fg=FG_MUT, font=FONT_UI).grid(
                row=0, column=3, padx=(18, 18))

            tk.Label(g, bg=BG2, width=3).grid(row=0, column=4)
            _styled_entry(g, bus_var, 18).grid(row=0, column=5, padx=(0, 2), pady=2, ipady=3)

            bus_add = _ab(g, "+", lambda: add_bus_extra(), preset="add_bus",
                          font=FONT_CODE_B, padx=6, pady=0, width=2)
            bus_add.grid(row=0, column=6, padx=2)

            # Case checkbox — custom styled
            cb_frame = tk.Frame(g, bg=BG2); cb_frame.grid(row=0, column=7, padx=10)
            tk.Checkbutton(cb_frame, variable=cs_var, bg=BG2,
                           selectcolor=PANEL, activebackground=BG2,
                           relief="flat", bd=0).pack()

            def remove():
                rule_rows.remove((kw_var, bus_var, cs_var, src_extra_list, bus_extra_list, row_frame))
                row_frame.destroy()

            rm_btn = _ab(g, "✕", remove, preset="remove",
                         font=FONT_CODE_B, padx=6, pady=0)
            rm_btn.grid(row=0, column=8, padx=(2, 0))

            # extra_slots for OR rows
            extra_slots = {}

            def _alloc_src_slot():
                for r in sorted(extra_slots):
                    if not extra_slots[r]["src"]: return r
                r = (max(extra_slots, default=0) + 1)
                extra_slots[r] = {"src": False, "bus": False}; return r

            def _alloc_bus_slot():
                for r in sorted(extra_slots):
                    if not extra_slots[r]["bus"]: return r
                r = (max(extra_slots, default=0) + 1)
                extra_slots[r] = {"src": False, "bus": False}; return r

            def add_src_extra(val=""):
                r = _alloc_src_slot(); extra_slots[r]["src"] = True
                evar = tk.StringVar(value=val)
                lbl = tk.Label(g, text="or", bg=BG2, fg=OK_CLR, font=FONT_UIB, width=3)
                lbl.grid(row=r, column=0, sticky="e")
                e = _styled_entry(g, evar, 18)
                e.grid(row=r, column=1, padx=(0, 2), pady=2, ipady=3)
                def rm():
                    lbl.destroy(); e.destroy(); rm_b.destroy()
                    extra_slots[r]["src"] = False
                    src_extra_list[:] = [(v, x) for v, x in src_extra_list if v is not evar]
                rm_b = _ab(g, "−", rm, preset="remove", font=FONT_CODE_B, padx=6, pady=0, width=2)
                rm_b.grid(row=r, column=2, padx=2, pady=2)
                src_extra_list.append((evar, None))

            def add_bus_extra(val=""):
                r = _alloc_bus_slot(); extra_slots[r]["bus"] = True
                evar = tk.StringVar(value=val)
                lbl = tk.Label(g, text="or", bg=BG2, fg=ACCENT, font=FONT_UIB, width=3)
                lbl.grid(row=r, column=4, sticky="e")
                e = _styled_entry(g, evar, 18)
                e.grid(row=r, column=5, padx=(0, 2), pady=2, ipady=3)
                def rm():
                    lbl.destroy(); e.destroy(); rm_b.destroy()
                    extra_slots[r]["bus"] = False
                    bus_extra_list[:] = [(v, x) for v, x in bus_extra_list if v is not evar]
                rm_b = _ab(g, "−", rm, preset="remove", font=FONT_CODE_B, padx=6, pady=0, width=2)
                rm_b.grid(row=r, column=6, padx=2, pady=2)
                bus_extra_list.append((evar, None))

            rule_rows.append((kw_var, bus_var, cs_var, src_extra_list, bus_extra_list, row_frame))
            for es in (extra_src   or []): add_src_extra(es)
            for eb in (extra_buses or []): add_bus_extra(eb)

        for rule in self.config.get(rule_key, []):
            extra_src   = rule.get("extra_keywords", []) if is_name else rule.get("extra_work_unit_keywords", [])
            extra_buses = rule.get("extra_bus_keywords", [])
            if is_name:
                add_row(rule.get("keyword",""), rule.get("expected_bus_keyword",""),
                        rule.get("case_sensitive", False), extra_src, extra_buses)
            else:
                add_row(rule.get("work_unit_keyword",""), rule.get("expected_bus_keyword",""),
                        rule.get("case_sensitive", False), extra_src, extra_buses)

        # ── Rule panel footer ───────────────────────────────────────────────
        tk.Frame(rp, bg=BORDER, height=1).pack(fill="x", padx=14)
        footer = tk.Frame(rp, bg=BG2); footer.pack(fill="x", padx=14, pady=(6, 10))

        # Left: flag unset checkbox + note
        flag_var = tk.BooleanVar(value=self.config.get("flag_unset_bus", True))
        def on_flag(): self.config["flag_unset_bus"] = flag_var.get()
        cb_flag = tk.Checkbutton(footer, text=self._t("flag_unset"),
                                 variable=flag_var, command=on_flag,
                                 bg=BG2, fg=FG_DIM, font=FONT_UI,
                                 selectcolor=PANEL, activebackground=BG2)
        cb_flag.pack(side="left")
        reg.append(lambda w=cb_flag: w.config(text=self._t("flag_unset")))

        lbl_fn = tk.Label(footer, text=self._t("flag_unset_note"),
                          bg=BG2, fg=FG_MUT, font=FONT_SM)
        lbl_fn.pack(side="left", padx=(2, 0))
        reg.append(lambda w=lbl_fn: w.config(text=self._t("flag_unset_note")))

        # Right: buttons
        def save_rules():
            rules = []
            for kw_v, bus_v, cs_v, src_el, bus_el, _ in rule_rows:
                kw, bus = kw_v.get().strip(), bus_v.get().strip()
                if kw and bus:
                    rule = {"expected_bus_keyword": bus, "case_sensitive": cs_v.get()}
                    src_extras = [ev.get().strip() for ev, _ in src_el if ev.get().strip()]
                    bus_extras  = [ev.get().strip() for ev, _ in bus_el if ev.get().strip()]
                    if is_name:
                        rule["keyword"] = kw
                        if src_extras: rule["extra_keywords"] = src_extras
                    else:
                        rule["work_unit_keyword"] = kw
                        if src_extras: rule["extra_work_unit_keywords"] = src_extras
                    if bus_extras: rule["extra_bus_keywords"] = bus_extras
                    rules.append(rule)
            self.config[rule_key] = rules
            self._save_config()
            messagebox.showinfo(self._t("save_title"), self._t("rules_saved"), parent=self.root)

        btn_save = _ab(footer, self._t("save_rules"), save_rules,
                       preset="primary", font=FONT_UIB, padx=14)
        btn_save.pack(side="right")
        reg.append(lambda w=btn_save: w.config(text=self._t("save_rules")))

        def reset_rules():
            if messagebox.askyesno(self._t("error_title"),
                                   self._t("rules_reset_confirm"), parent=self.root):
                for _, _, _, _, _, rf in list(rule_rows):
                    rf.destroy()
                rule_rows.clear()
                self.config[rule_key] = []
                self._save_config()

        btn_reset = _ab(footer, self._t("rules_reset"), reset_rules,
                        preset="danger", font=FONT_UIB, padx=12)
        btn_reset.pack(side="right", padx=(0, 6))
        reg.append(lambda w=btn_reset: w.config(text=self._t("rules_reset")))

        lbl_rem = tk.Label(footer, text=self._t("save_reminder"),
                           bg=BG2, fg=WARN, font=FONT_UI)
        lbl_rem.pack(side="right", padx=(0, 12))
        reg.append(lambda w=lbl_rem: w.config(text=self._t("save_reminder")))

        btn_add = _ab(footer, self._t("add_rule"), lambda: add_row(),
                      preset="muted", font=FONT_UI, padx=12)
        btn_add.pack(side="right", padx=(0, 6))
        reg.append(lambda w=btn_add: w.config(text=self._t("add_rule")))

        # ── Filter Bar ──────────────────────────────────────────────────────
        fb = tk.Frame(parent, bg=BG3); fb.pack(fill="x", padx=12, pady=(6, 0))

        # Left accent bar
        tk.Frame(fb, bg=ACCENT, width=2).pack(side="left", fill="y", padx=(0, 10))

        lbl_srch = tk.Label(fb, text=self._t("search_lbl"), bg=BG3, fg=ACCENT,
                            font=FONT_UIB, width=4, anchor="w")
        lbl_srch.pack(side="left", padx=(0, 6), pady=7)
        reg.append(lambda w=lbl_srch: w.config(text=self._t("search_lbl")))

        field_idx_var = tk.IntVar(value=0)
        field_combo = ttk.Combobox(fb, values=[self._t(k) for k in SEARCH_FIELD_SKEYS],
                                   state="readonly", font=FONT_UI, width=16)
        field_combo.current(0); field_combo.pack(side="left", padx=(0, 6), pady=7)
        field_combo.bind("<<ComboboxSelected>>",
            lambda e, v=field_idx_var, c=field_combo, m=mode:
                (v.set(c.current()), self._apply_filter(m)))

        def _refresh_fc(c=field_combo, v=field_idx_var):
            c.config(values=[self._t(k) for k in SEARCH_FIELD_SKEYS]); c.current(v.get())
        reg.append(_refresh_fc)

        if is_name: self._search_field_idx_name = field_idx_var
        else:       self._search_field_idx_wu   = field_idx_var

        search_var = tk.StringVar()
        search_entry = tk.Entry(fb, textvariable=search_var,
                                bg=PANEL, fg=FG, insertbackground=FG,
                                font=FONT_CODE, relief="flat",
                                highlightthickness=1,
                                highlightbackground=BORDER,
                                highlightcolor=ACCENT, width=34)
        search_entry.pack(side="left", padx=(0, 4), pady=7, ipady=4)
        search_entry.bind("<FocusIn>",  lambda e: search_entry.config(highlightbackground=ACCENT))
        search_entry.bind("<FocusOut>", lambda e: search_entry.config(highlightbackground=BORDER))

        clr_btn = _ab(fb, "×",
                      lambda: search_var.set(""),
                      preset="icon", font=(_UI, 12, "bold"), padx=8, pady=0)
        clr_btn.pack(side="left", padx=(0, 10))

        lbl_hint = tk.Label(fb, text=self._t("search_hint"), bg=BG3, fg=FG_MUT, font=FONT_SM)
        lbl_hint.pack(side="left")
        reg.append(lambda w=lbl_hint: w.config(text=self._t("search_hint")))

        if is_name:
            self._search_var_name = search_var
            search_var.trace_add("write", lambda *_: self._apply_filter("name"))
            tk.Frame(fb, bg=BORDER, width=1).pack(side="left", fill="y", padx=(12, 10), pady=6)
            def _name_toggle(*_): self._apply_filter("name")
            cb_inh_n = tk.Checkbutton(fb, text=self._t("inherited"),
                                      variable=self._name_show_inherited, command=_name_toggle,
                                      bg=BG3, fg=WARN, font=FONT_UIB,
                                      selectcolor=BG2, activebackground=BG3,
                                      activeforeground=WARN)
            cb_inh_n.pack(side="left", padx=(0, 4))
            reg.append(lambda w=cb_inh_n: w.config(text=self._t("inherited")))
            cb_ovr_n = tk.Checkbutton(fb, text=self._t("overridden"),
                                      variable=self._name_show_override, command=_name_toggle,
                                      bg=BG3, fg=ERR_CLR, font=FONT_UIB,
                                      selectcolor=BG2, activebackground=BG3,
                                      activeforeground=ERR_CLR)
            cb_ovr_n.pack(side="left", padx=4)
            reg.append(lambda w=cb_ovr_n: w.config(text=self._t("overridden")))
        else:
            self._search_var_wu = search_var
            search_var.trace_add("write", lambda *_: self._apply_filter("workunit"))
            tk.Frame(fb, bg=BORDER, width=1).pack(side="left", fill="y", padx=(12, 10), pady=6)
            self._wu_show_inherited = tk.BooleanVar(value=True)
            self._wu_show_override  = tk.BooleanVar(value=True)
            def _wu_toggle(*_): self._apply_filter("workunit")
            cb_inh = tk.Checkbutton(fb, text=self._t("inherited"),
                                    variable=self._wu_show_inherited, command=_wu_toggle,
                                    bg=BG3, fg=WARN, font=FONT_UIB,
                                    selectcolor=BG2, activebackground=BG3,
                                    activeforeground=WARN)
            cb_inh.pack(side="left", padx=(0, 4))
            reg.append(lambda w=cb_inh: w.config(text=self._t("inherited")))

            cb_ovr = tk.Checkbutton(fb, text=self._t("overridden"),
                                    variable=self._wu_show_override, command=_wu_toggle,
                                    bg=BG3, fg=ERR_CLR, font=FONT_UIB,
                                    selectcolor=BG2, activebackground=BG3,
                                    activeforeground=ERR_CLR)
            cb_ovr.pack(side="left", padx=4)
            reg.append(lambda w=cb_ovr: w.config(text=self._t("overridden")))

        # ── Action Bar (먼저 bottom에 고정 — treeview보다 앞에 pack해야 항상 보임) ──
        bar = tk.Frame(parent, bg=BG3, height=48)
        bar.pack(side="bottom", fill="x", padx=12, pady=(3, 8))
        bar.pack_propagate(False)

        scan_btn = _ab(bar, self._t("scan"),
                       lambda: self._run_scan(mode),
                       preset="primary", font=FONT_UIB, padx=18)
        scan_btn.pack(side="left", padx=(0, 2), pady=8)
        reg.append(lambda w=scan_btn: w.config(text=self._t("scan")))

        tk.Frame(bar, bg=BORDER, width=1).pack(side="left", fill="y", padx=10, pady=10)

        btn_view = _ab(bar, self._t("view_wwise"),
                       lambda t=None, m=is_name: self._action_select(
                           self.tree_name if is_name else self.tree_wu, m),
                       preset="ghost", font=FONT_UI, padx=12)
        btn_view.pack(side="left", padx=2, pady=8)
        reg.append(lambda w=btn_view: w.config(text=self._t("view_wwise")))

        btn_fix = _ab(bar, self._t("reroute"),
                      lambda t=None, m=is_name: self._action_fix(
                          self.tree_name if is_name else self.tree_wu, m),
                      preset="danger", font=FONT_UIB, padx=12)
        btn_fix.pack(side="left", padx=2, pady=8)
        reg.append(lambda w=btn_fix: w.config(text=self._t("reroute")))

        btn_sel = _ab(bar, self._t("select_all"),
                      lambda: (self.tree_name if is_name else self.tree_wu).selection_set(
                          (self.tree_name if is_name else self.tree_wu).get_children()),
                      preset="ghost", font=FONT_UI, padx=12)
        btn_sel.pack(side="left", padx=2, pady=8)
        reg.append(lambda w=btn_sel: w.config(text=self._t("select_all")))

        tk.Frame(bar, bg=BORDER, width=1).pack(side="right", fill="y", padx=10, pady=10)

        btn_csv = _ab(bar, self._t("export_csv"),
                      lambda m=is_name: self._export_csv(m),
                      preset="ghost", font=FONT_UI, padx=12)
        btn_csv.pack(side="right", padx=2, pady=8)
        reg.append(lambda w=btn_csv: w.config(text=self._t("export_csv")))

        tk.Label(bar, text=VERSION, bg=BG3, fg=FG_MUT, font=FONT_SM).pack(
            side="right", padx=(0, 6))

        count_lbl = tk.Label(bar, text="—", bg=BG3, fg=FG_DIM, font=FONT_UI)
        count_lbl.pack(side="right", padx=12)

        if is_name: self.btn_scan_name = scan_btn;  self.lbl_count_name = count_lbl
        else:       self.btn_scan_wu   = scan_btn;  self.lbl_count_wu   = count_lbl

        # ── Treeview ────────────────────────────────────────────────────────
        cols     = ("name", "work_unit", "current_bus", "trigger", "expected_kw", "path")
        col_keys = ("col_name","col_work_unit","col_cur_bus","col_trigger","col_exp_kw","col_path")
        col_wids = (200, 130, 170, 240, 130, 1200)

        tbl = tk.Frame(parent, bg=BORDER, bd=0)
        tbl.pack(fill="both", expand=True, padx=12, pady=(4, 0))

        vsb = ttk.Scrollbar(tbl, orient="vertical")
        vsb.pack(side="right", fill="y")
        hsb = ttk.Scrollbar(tbl, orient="horizontal")
        hsb.pack(side="bottom", fill="x")

        tree = ttk.Treeview(tbl, columns=cols, show="headings",
                            yscrollcommand=vsb.set, xscrollcommand=hsb.set,
                            selectmode="extended")
        tree.pack(fill="both", expand=True)
        vsb.config(command=tree.yview); hsb.config(command=tree.xview)

        for col, key, w in zip(cols, col_keys, col_wids):
            tree.heading(col, text=self._t(key), command=lambda c=col, t=tree: self._sort(t, c))
            tree.column(col, width=w, minwidth=60, stretch=False)
            reg.append(lambda t=tree, c=col, k=key: t.heading(c, text=self._t(k)))

        # 단일 태그(bg+fg 통합) — 다중 태그 우선순위 충돌 방지
        _BG_E = BG2; _BG_O = "#131920"
        tree.tag_configure("inh_e", background=_BG_E, foreground=WARN)     # 상속됨 짝수행
        tree.tag_configure("inh_o", background=_BG_O, foreground=WARN)     # 상속됨 홀수행
        tree.tag_configure("ovr_e", background=_BG_E, foreground=ERR_CLR)  # 오버라이드됨 짝수
        tree.tag_configure("ovr_o", background=_BG_O, foreground=ERR_CLR)  # 오버라이드됨 홀수
        tree.tag_configure("uns_e", background=_BG_E, foreground=WARN)     # 미설정 짝수
        tree.tag_configure("uns_o", background=_BG_O, foreground=WARN)     # 미설정 홀수
        tree.tag_configure("ok_msg", foreground=OK_CLR)
        tree.tag_configure("_hover", font=FONT_CODE_B)  # hover: bold만 (fg 유지)

        # 마우스오버 행 하이라이트 (텍스트 bold)
        _hov = [None]; _hov_tags = [()]
        def _on_tree_motion(event, t=tree):
            iid = t.identify_row(event.y)
            if iid == _hov[0]: return
            if _hov[0] and t.exists(_hov[0]):
                t.item(_hov[0], tags=_hov_tags[0])
            _hov[0] = iid
            if iid and t.exists(iid):
                orig = tuple(t.item(iid, "tags"))
                _hov_tags[0] = orig
                t.item(iid, tags=orig + ("_hover",))
        def _on_tree_leave(event, t=tree):
            if _hov[0] and t.exists(_hov[0]):
                t.item(_hov[0], tags=_hov_tags[0])
            _hov[0] = None
        tree.bind("<Motion>", _on_tree_motion)
        tree.bind("<Leave>",  _on_tree_leave)

        tree.bind("<Double-1>", lambda e, t=tree, m=is_name: self._on_dbl(e, t, m))
        if is_name: self.tree_name = tree
        else:       self.tree_wu   = tree

    # ── Sort ─────────────────────────────────────────────────────────────────
    def _sort(self, tree, col):
        rev  = self._sort_reverse.get(col, False)
        data = [(tree.set(iid, col), iid) for iid in tree.get_children("")]
        data.sort(key=lambda x: x[0].lower(), reverse=rev)
        for i, (_, iid) in enumerate(data): tree.move(iid, "", i)
        self._sort_reverse[col] = not rev
        raw = tree.heading(col)["text"].rstrip(" ↑↓")
        tree.heading(col, text=raw + (" ↑" if not rev else " ↓"))

    def _set_count(self, lbl, total, n):
        if n == 0: lbl.config(text=self._t("no_violations").format(total), fg=OK_CLR)
        else:      lbl.config(text=self._t("violations").format(total, n), fg=ERR_CLR)

    def _get_filtered(self, is_name):
        return self.filtered_name if is_name else self.filtered_wu

    def _on_dbl(self, event, tree, is_name):
        sel = tree.selection()
        if not sel or not self.client: return
        results = self._get_filtered(is_name); idx = tree.index(sel[0])
        if 0 <= idx < len(results):
            threading.Thread(target=self._select_in_wwise, args=(results[idx]["id"],), daemon=True).start()

    def _action_select(self, tree, is_name):
        sel = tree.selection()
        if not sel:
            messagebox.showinfo(self._t("info_title"), self._t("select_item"), parent=self.root); return
        if not self.client:
            messagebox.showerror(self._t("error_title"), self._t("no_wwise"), parent=self.root); return
        results = self._get_filtered(is_name); idx = tree.index(sel[0])
        if 0 <= idx < len(results):
            threading.Thread(target=self._select_in_wwise, args=(results[idx]["id"],), daemon=True).start()

    def _action_fix(self, tree, is_name):
        sel = tree.selection()
        if not sel:
            messagebox.showinfo(self._t("info_title"), self._t("select_reroute"), parent=self.root); return
        if not self.client:
            messagebox.showerror(self._t("error_title"), self._t("no_wwise"), parent=self.root); return
        results = self._get_filtered(is_name)
        to_fix = [results[tree.index(iid)] for iid in sel if 0 <= tree.index(iid) < len(results)]
        if to_fix: self._show_fix_dialog(to_fix, is_name)

    # ── Reroute Dialog ───────────────────────────────────────────────────────
    def _show_fix_dialog(self, violations, is_name):
        dlg = tk.Toplevel(self.root)
        dlg.title(self._t("reroute_title"))
        dlg.geometry("580x380"); dlg.configure(bg=BG); dlg.grab_set()
        dlg.resizable(False, False)

        # Header
        dh = tk.Frame(dlg, bg=BG3); dh.pack(fill="x")
        tk.Frame(dh, bg=DANGER, height=2).pack(fill="x")
        tk.Label(dh, text=self._t("reroute_title"), bg=BG3, fg=FG,
                 font=FONT_H1).pack(side="left", padx=18, pady=12)

        # Body
        body = tk.Frame(dlg, bg=BG); body.pack(fill="both", expand=True, padx=18, pady=(12, 6))
        tk.Label(body, text=self._t("reroute_fmt").format(len(violations)),
                 bg=BG, fg=FG, font=FONT_UIB).pack(anchor="w")
        tk.Label(body, text=self._t("reroute_bus_sel"),
                 bg=BG, fg=FG_DIM, font=FONT_UI).pack(anchor="w", pady=(4, 10))

        by_kw = {}
        for v in violations: by_kw.setdefault(v["expected_bus_keyword"], []).append(v)
        bus_names = sorted(self.buses.keys()); kw_bus_vars = {}

        grid = tk.Frame(body, bg=BG); grid.pack(fill="x")
        for i, (kw, items) in enumerate(by_kw.items()):
            row_bg = BG2 if i % 2 == 0 else BG
            rf = tk.Frame(grid, bg=row_bg); rf.pack(fill="x", pady=1)
            tk.Label(rf, text=f'"{kw}"', bg=row_bg, fg=ACCENT,
                     font=FONT_CODE_B, width=24, anchor="w").pack(side="left", padx=(10, 4), pady=6)
            tk.Label(rf, text=f"({len(items)})", bg=row_bg, fg=FG_DIM,
                     font=FONT_UI).pack(side="left", padx=(0, 12))
            default = next((b for b in bus_names if kw.upper() in b.upper()), "")
            var = tk.StringVar(value=default); kw_bus_vars[kw] = var
            ttk.Combobox(rf, textvariable=var, values=bus_names,
                         width=30, font=FONT_CODE).pack(side="left", pady=6)

        def do_fix():
            fixed, errors = 0, []
            for kw, var in kw_bus_vars.items():
                bus_id = self.buses.get(var.get())
                if not bus_id: errors.append(self._t("bus_missing").format(var.get())); continue
                for v in by_kw[kw]:
                    try: self._set_output_bus(v["id"], bus_id); fixed += 1
                    except Exception as e: errors.append(f'{v["name"]}: {e}')
            dlg.destroy()
            if errors:
                messagebox.showwarning(self._t("partial_title"),
                    self._t("reroute_partial").format(fixed, len(errors), "\n".join(errors)),
                    parent=self.root)
            else:
                messagebox.showinfo(self._t("complete_title"),
                    self._t("reroute_done").format(fixed), parent=self.root)
            self._run_scan("name" if is_name else "workunit")

        # Footer
        tk.Frame(dlg, bg=BORDER, height=1).pack(fill="x")
        bbar = tk.Frame(dlg, bg=BG3); bbar.pack(fill="x", pady=0)
        _ab(bbar, self._t("cancel"), dlg.destroy,
            preset="ghost", font=FONT_UI, padx=16).pack(side="right", padx=(4, 12), pady=10)
        _ab(bbar, self._t("apply_reroute"), do_fix,
            preset="danger", font=FONT_UIB, padx=16).pack(side="right", padx=4, pady=10)

    # ── Export ───────────────────────────────────────────────────────────────
    def _export_csv(self, is_name):
        results = self._get_filtered(is_name)
        if not results:
            messagebox.showinfo(self._t("info_title"), self._t("no_export"), parent=self.root); return
        path = filedialog.asksaveasfilename(defaultextension=".csv",
            filetypes=[("CSV","*.csv"),("*","*.*")], title=self._t("csv_title"), parent=self.root)
        if not path: return
        fields = ["name","work_unit","current_bus","trigger","expected_bus_keyword","path"]
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
            w.writeheader(); w.writerows(results)
        messagebox.showinfo(self._t("complete_title"), self._t("csv_done").format(path), parent=self.root)

    # ── Tooltip ──────────────────────────────────────────────────────────────
    @staticmethod
    def _attach_tooltip(widget, text_fn):
        tip = [None]
        def _show(e):
            if tip[0]: return
            text = text_fn() if callable(text_fn) else text_fn
            x = widget.winfo_rootx() + 20
            y = widget.winfo_rooty() + widget.winfo_height() + 6
            w = tk.Toplevel(widget); w.wm_overrideredirect(True)
            w.wm_geometry(f"+{x}+{y}")
            outer = tk.Frame(w, bg=ACCENT, padx=1, pady=1); outer.pack()
            tk.Label(outer, text=text, bg=BG3, fg=FG,
                     font=FONT_CODE, justify="left",
                     padx=12, pady=8).pack()
            tip[0] = w
        def _hide(e):
            if tip[0]: tip[0].destroy(); tip[0] = None
        widget.bind("<Enter>", _show, add="+")
        widget.bind("<Leave>", _hide, add="+")

    # ── Status ───────────────────────────────────────────────────────────────
    def _set_proj_name(self, proj_name):
        """프로젝트 이름을 별도 레이블에 표시."""
        self._proj_name = proj_name

        def _update():
            if hasattr(self, '_proj_lbl'):
                self._proj_lbl.config(text=proj_name)
                self._proj_sep.config(text="  ·  " if proj_name else "")
        self.root.after(0, _update)

    def _set_status(self, msg, color=FG_DIM, pulsing=False, key=None, args=()):
        """상태 메시지 표시. key 지정 시 언어 전환 후 재번역됨."""
        if self._status_anim_id:
            try: self.root.after_cancel(self._status_anim_id)
            except Exception: pass
            self._status_anim_id = None
        if key:
            self._cur_status_key   = key
            self._cur_status_args  = args
            self._cur_status_color = color

        def _update():
            self._status_lbl.config(text=msg, fg=color)
            self._status_dot.config(fg=color)

        self.root.after(0, _update)

        if pulsing:
            pulse_colors = [color, FG_MUT]
            def _pulse(idx=0):
                try:
                    self._status_dot.config(fg=pulse_colors[idx % 2])
                    self._status_anim_id = self.root.after(600, lambda: _pulse(idx + 1))
                except Exception: pass
            self.root.after(0, _pulse)


    # ══════════════════════════════════════════════════════════════════════════
    # V2: Graph Cache
    # ══════════════════════════════════════════════════════════════════════════

    def _build_graph(self):
        """전체 프로젝트를 1회 fetch해 메모리 그래프로 구성."""
        if not self.client: return
        self._set_status(self._t("graph_building"), WARN, pulsing=True)
        try:
            # Phase 1: filePath 없이 전체 계층 fetch (multi-type에 filePath 포함 시 Wwise가 빈 결과 반환)
            r = self.client.call("ak.wwise.core.object.get", {
                "from": {"ofType": self._HIERARCHY_TYPES},
                "options": {"return": ["id","name","path","type","@OutputBus","@OverrideOutput","workunit"]},
            })
            objects = r.get("return", [])
            g = {}
            for obj in objects:
                path = obj.get("path", "")
                if not path: continue
                sep = path.rfind("\\")
                parent = path[:sep] if sep > 0 else ""
                raw_type = obj.get("type", "")
                g[path] = {
                    "id":              obj.get("id", ""),
                    "name":            obj.get("name", ""),
                    "type":            raw_type,
                    "parent":          parent,
                    "output_bus":      obj.get("@OutputBus") or {},
                    "override_output": obj.get("@OverrideOutput", False),
                    "workunit":        obj.get("workunit") or {},
                }

            # Phase 2: WorkUnit만 filePath 별도 fetch → PhysicalFolder 구분
            try:
                r_wu = self.client.call("ak.wwise.core.object.get", {
                    "from": {"ofType": ["WorkUnit"]},
                    "options": {"return": ["path", "filePath"]},
                })
                for wu in r_wu.get("return", []):
                    p  = wu.get("path", "")
                    fp = wu.get("filePath", "") or ""
                    if p in g and not fp.lower().endswith(".wwu"):
                        g[p]["type"] = "PhysicalFolder"
            except Exception:
                pass  # filePath fetch 실패 시 기본 WorkUnit 타입 유지
            with self._graph_lock:
                self._graph = g
                self._graph_ready = True
            proj_name = ""
            try:
                rp = self.client.call("ak.wwise.core.object.get",
                    {"from": {"ofType": ["Project"]}, "options": {"return": ["name"]}})
                items = rp.get("return", [])
                proj_name = items[0]["name"] if items else "—"
            except Exception: pass
            # 버스 계층 구조 fetch
            try:
                rb = self.client.call("ak.wwise.core.object.get", {
                    "from": {"ofType": ["Bus", "AuxBus"]},
                    "options": {"return": ["id", "name", "path"]},
                })
                bh = {}
                for bus in rb.get("return", []):
                    bpath = bus.get("path", "")
                    if not bpath: continue
                    sep = bpath.rfind("\\")
                    bh[bpath] = {
                        "id":          bus.get("id", ""),
                        "name":        bus.get("name", ""),
                        "parent_path": bpath[:sep] if sep > 0 else "",
                    }
                self._bus_hierarchy = bh
            except Exception:
                pass
            sub_count = self._register_subscriptions()
            self._set_proj_name(proj_name)
            sub_suffix = f"  ·  ⚡ {sub_count}" if sub_count else ""
            status_msg = (self._t("connected_fmt").format(len(self.buses)) +
                          "  ·  " + self._t("graph_ready_fmt").format(len(g)) +
                          sub_suffix)
            self._set_status(status_msg, OK_CLR,
                             key="connected_fmt", args=(len(self.buses),))
        except Exception:
            pass  # V1 fallback remains active

    def _register_subscriptions(self):
        """WAAPI 오브젝트/프로퍼티 변경 이벤트를 구독해 그래프를 자동 리빌드.
        Returns: int — 성공적으로 등록된 구독 수"""
        if not self.client:
            return 0
        # 기존 구독 해제
        for handle in self._subscriptions:
            try:
                if handle is not None:
                    self.client.unsubscribe(handle)
            except Exception:
                pass
        self._subscriptions.clear()

        topics = [
            "ak.wwise.core.object.created",
            "ak.wwise.core.object.postDeleted",
            "ak.wwise.core.object.nameChanged",
            "ak.wwise.core.object.childAdded",
            "ak.wwise.core.object.childRemoved",
            "ak.wwise.core.object.propertyChanged",
        ]
        for topic in topics:
            try:
                handle = self.client.subscribe(topic, self._on_wwise_change)
                if handle is not None:
                    self._subscriptions.append(handle)
            except Exception:
                pass
        return len(self._subscriptions)

    def _on_wwise_change(self, *args, **kwargs):
        """변경 이벤트 수신 → debounce 1.5초 후 그래프 리빌드."""
        import threading as _threading
        if self._debounce_timer is not None:
            self._debounce_timer.cancel()
        self._debounce_timer = _threading.Timer(1.5, self._debounced_rebuild)
        self._debounce_timer.daemon = True
        self._debounce_timer.start()

    def _debounced_rebuild(self):
        """백그라운드 스레드에서 그래프 리빌드 후 패널 갱신."""
        import threading as _threading
        self._debounce_timer = None
        with self._graph_lock:
            self._graph_ready = False
        _threading.Thread(target=self._rebuild_and_refresh, daemon=True).start()

    def _rebuild_and_refresh(self):
        self._build_graph()
        self.root.after(0, self._refresh_v2_panels)

    def _get_signal_chain(self, path):
        """Sound path에서 루트 방향으로 조상 노드 체인을 반환."""
        chain = []
        cur = path
        visited = set()
        with self._graph_lock:
            while cur and cur in self._graph and cur not in visited:
                visited.add(cur)
                node = dict(self._graph[cur])
                node["path"] = cur
                chain.append(node)
                parent = node.get("parent", "")
                if not parent: break
                cur = parent
        return chain  # Sound first, 루트 방향

    # ══════════════════════════════════════════════════════════════════════════
    # V2: Signal Flow Tab
    # ══════════════════════════════════════════════════════════════════════════

    def _build_signal_flow_tab(self, parent, mode='name'):
        reg = self._lang_updaters
        ctx = {'all_vios': [], 'vio_filtered': [], 'cur_path': None, 'cur_vio': None}
        self._sf_ctx[mode] = ctx

        # ── 상단 바 ──────────────────────────────────────────────────────────
        top = tk.Frame(parent, bg=BG3, height=40)
        top.pack(fill="x"); top.pack_propagate(False)
        tk.Frame(top, bg=ACCENT, height=2).pack(fill="x", side="bottom")

        _sf_hdr_key = "sf_hdr_name" if mode == 'name' else "sf_hdr_wu"
        lbl_hdr = tk.Label(top, text=self._t(_sf_hdr_key), bg=BG3, fg=FG, font=FONT_H2)
        lbl_hdr.pack(side="left", padx=16, pady=8)
        reg.append(lambda w=lbl_hdr, k=_sf_hdr_key: w.config(text=self._t(k)))

        gs = tk.Label(top, text="", bg=BG3, fg=FG_DIM, font=FONT_SM)
        gs.pack(side="left", padx=8)
        ctx['graph_status'] = gs

        btn_rebuild = _ab(top, self._t("graph_rebuild"),
                          lambda: threading.Thread(target=self._rebuild_graph, daemon=True).start(),
                          preset="ghost", font=FONT_UI, padx=12)
        btn_rebuild.pack(side="right", padx=12, pady=6)
        reg.append(lambda w=btn_rebuild: w.config(text=self._t("graph_rebuild")))

        # ── 검색 필터 바 ─────────────────────────────────────────────────────
        fb = tk.Frame(parent, bg=BG2)
        fb.pack(fill="x", padx=0)
        tk.Frame(fb, bg=BORDER, height=1).pack(fill="x")
        inner_fb = tk.Frame(fb, bg=BG2)
        inner_fb.pack(fill="x", padx=12, pady=4)

        tk.Label(inner_fb, text="검색", bg=BG2, fg=ACCENT, font=FONT_UIB).pack(side="left", padx=(0,6))
        sv = tk.StringVar()
        ctx['search_var'] = sv
        sf_entry = tk.Entry(inner_fb, textvariable=sv,
                            bg=PANEL, fg=FG, insertbackground=FG, font=FONT_CODE,
                            relief="flat", highlightthickness=1,
                            highlightbackground=BORDER, highlightcolor=ACCENT, width=28)
        sf_entry.pack(side="left", ipady=3, padx=(0,4))
        sf_entry.bind("<FocusIn>",  lambda e: sf_entry.config(highlightbackground=ACCENT))
        sf_entry.bind("<FocusOut>", lambda e: sf_entry.config(highlightbackground=BORDER))
        _ab(inner_fb, "×", lambda m=mode: self._sf_ctx[m]['search_var'].set(""),
            preset="icon", font=(_UI, 12, "bold"), padx=6, pady=0).pack(side="left", padx=(0,12))
        sv.trace_add("write", lambda *_, m=mode: self._sf_apply_filter(m))

        vio_only = tk.BooleanVar(value=False)
        ctx['vio_only'] = vio_only
        tk.Checkbutton(inner_fb, text="위반만 표시", variable=vio_only,
                       command=lambda m=mode: self._sf_apply_filter(m),
                       bg=BG2, fg=FG_DIM, font=FONT_UI,
                       selectcolor=PANEL, activebackground=BG2).pack(side="left", padx=4)

        count_lbl = tk.Label(inner_fb, text="—", bg=BG2, fg=FG_DIM, font=FONT_SM)
        count_lbl.pack(side="right", padx=8)
        ctx['count_lbl'] = count_lbl

        # ── 2패널 메인 영역 ───────────────────────────────────────────────────
        paned = tk.PanedWindow(parent, orient="horizontal",
                               bg=BORDER, sashwidth=4, sashrelief="flat", sashpad=0)
        paned.pack(fill="both", expand=True)

        # ── 좌 패널: 버스 트리 ────────────────────────────────────────────────
        left = tk.Frame(paned, bg=BG2, width=200)
        paned.add(left, minsize=140)

        tk.Frame(left, bg=ACCENT, height=2).pack(fill="x")
        lbl_bt = tk.Label(left, text=self._t("bus_tree_hdr"), bg=BG2, fg=FG_DIM, font=FONT_UIB)
        lbl_bt.pack(fill="x", padx=8, pady=(6,2))
        reg.append(lambda w=lbl_bt: w.config(text=self._t("bus_tree_hdr")))
        leg = tk.Frame(left, bg=BG2)
        leg.pack(fill="x", padx=8, pady=(0, 4))
        tk.Label(leg, text="●", fg=ERR_CLR, bg=BG2, font=FONT_SM).pack(side="left")
        tk.Label(leg, text=" 직접 위반", fg=FG_DIM, bg=BG2, font=FONT_SM).pack(side="left")
        tk.Label(leg, text="   ●", fg=WARN, bg=BG2, font=FONT_SM).pack(side="left")
        tk.Label(leg, text=" 하위에 위반 존재", fg=FG_DIM, bg=BG2, font=FONT_SM).pack(side="left")

        bt_frame = tk.Frame(left, bg=BORDER)
        bt_frame.pack(fill="both", expand=True, padx=0, pady=0)
        bt_vsb = ttk.Scrollbar(bt_frame, orient="vertical")
        bt_vsb.pack(side="right", fill="y")
        bt = ttk.Treeview(bt_frame, columns=("count",), show="tree headings",
                          yscrollcommand=bt_vsb.set, selectmode="browse")
        bt.pack(fill="both", expand=True)
        bt_vsb.config(command=bt.yview)
        bt.heading("#0",    text="버스")
        bt.heading("count", text="위반")
        bt.column("#0",    width=140, stretch=True,  minwidth=80)
        bt.column("count", width=46,  stretch=False, anchor="center")
        bt.tag_configure("ok",   foreground=OK_CLR)
        bt.tag_configure("warn", foreground=WARN)
        bt.tag_configure("err",  foreground=ERR_CLR)
        bt.tag_configure("all",  foreground=ACCENT)
        bt.tag_configure("dim",  foreground=FG_MUT)
        ctx['bus_tree'] = bt
        bt.bind("<<TreeviewSelect>>", lambda e, m=mode: self._on_sf_bus_select(m))

        # ── 우 패널: Vertical PanedWindow ────────────────────────────────────
        right = tk.Frame(paned, bg=BG)
        paned.add(right, minsize=400)

        right_paned = tk.PanedWindow(right, orient="vertical",
                                     bg=BORDER, sashwidth=4, sashrelief="flat", sashpad=0)
        right_paned.pack(fill="both", expand=True)

        # 우 상단: 위반 목록 ──────────────────────────────────────────────────
        vio_frame = tk.Frame(right_paned, bg=BG2)
        right_paned.add(vio_frame, minsize=120)

        tk.Frame(vio_frame, bg=ACCENT2 if True else ACCENT, height=2).pack(fill="x")
        vio_hdr = tk.Frame(vio_frame, bg=BG2)
        vio_hdr.pack(fill="x", padx=8, pady=(4,2))
        vio_title = tk.Label(vio_hdr, text="위반 목록", bg=BG2, fg=FG_DIM, font=FONT_UIB)
        vio_title.pack(side="left")
        ctx['vio_title'] = vio_title

        vio_cols = ("src", "name", "work_unit", "current_bus", "expected_kw", "path")
        vt_frame = tk.Frame(vio_frame, bg=BORDER)
        vt_frame.pack(fill="both", expand=True)
        vt_vsb = ttk.Scrollbar(vt_frame, orient="vertical")
        vt_vsb.pack(side="right", fill="y")
        vt_hsb = ttk.Scrollbar(vt_frame, orient="horizontal")
        vt_hsb.pack(side="bottom", fill="x")
        vt = ttk.Treeview(vt_frame, columns=vio_cols, show="headings",
                          yscrollcommand=vt_vsb.set, xscrollcommand=vt_hsb.set,
                          selectmode="browse")
        vt.pack(fill="both", expand=True)
        vt_vsb.config(command=vt.yview)
        vt_hsb.config(command=vt.xview)
        for col, hdr, w in [("src","출처",54),("name","에셋 이름",200),("work_unit","Work Unit",120),
                              ("current_bus","현재 버스",150),("expected_kw","기대 키워드",120),
                              ("path","전체 경로",800)]:
            vt.heading(col, text=hdr)
            vt.column(col, width=w, minwidth=30 if col=="src" else 60,
                      stretch=False, anchor="center" if col=="src" else "w")
        _VBE = BG2; _VBO = "#131920"
        vt.tag_configure("inh_e", background=_VBE, foreground=WARN)
        vt.tag_configure("inh_o", background=_VBO, foreground=WARN)
        vt.tag_configure("ovr_e", background=_VBE, foreground=ERR_CLR)
        vt.tag_configure("ovr_o", background=_VBO, foreground=ERR_CLR)
        vt.tag_configure("uns_e", background=_VBE, foreground=FG_MUT)
        vt.tag_configure("uns_o", background=_VBO, foreground=FG_MUT)
        vt.tag_configure("src_name", foreground=OK_CLR)
        vt.tag_configure("src_wu",   foreground=ACCENT)
        vt.tag_configure("_hover",   font=FONT_CODE_B)
        # 마우스오버
        _vhov = [None]; _vhov_tags = [()]
        def _on_vt_motion(event, t=vt):
            iid = t.identify_row(event.y)
            if iid == _vhov[0]: return
            if _vhov[0] and t.exists(_vhov[0]):
                t.item(_vhov[0], tags=_vhov_tags[0])
            _vhov[0] = iid
            if iid and t.exists(iid):
                orig = tuple(t.item(iid, "tags"))
                _vhov_tags[0] = orig
                t.item(iid, tags=orig + ("_hover",))
        def _on_vt_leave(event, t=vt):
            if _vhov[0] and t.exists(_vhov[0]):
                t.item(_vhov[0], tags=_vhov_tags[0])
            _vhov[0] = None
        vt.bind("<Motion>", _on_vt_motion)
        vt.bind("<Leave>",  _on_vt_leave)
        vt.bind("<<TreeviewSelect>>", lambda e, m=mode: self._on_sf_vio_select(m))
        vt.bind("<Double-1>",         lambda e, m=mode: self._on_sf_vio_double(m))
        ctx['vio_tree'] = vt

        # 액션 바
        ab2 = tk.Frame(vio_frame, bg=BG3, height=36)
        ab2.pack(fill="x"); ab2.pack_propagate(False)
        btn_vw = _ab(ab2, self._t("view_wwise"),
                     lambda m=mode: self._sf_action_view(m), preset="ghost", font=FONT_UI, padx=12)
        btn_vw.pack(side="left", padx=4, pady=4)
        reg.append(lambda w=btn_vw: w.config(text=self._t("view_wwise")))
        btn_rt = _ab(ab2, self._t("reroute"),
                     lambda m=mode: self._sf_action_reroute(m), preset="danger", font=FONT_UIB, padx=12)
        btn_rt.pack(side="left", padx=2, pady=4)
        reg.append(lambda w=btn_rt: w.config(text=self._t("reroute")))

        # 우 하단: Canvas 신호 흐름 ──────────────────────────────────────────
        canvas_frame = tk.Frame(right_paned, bg=BG)
        right_paned.add(canvas_frame, minsize=150)

        tk.Frame(canvas_frame, bg=BORDER, height=2).pack(fill="x")
        sf_top = tk.Frame(canvas_frame, bg=BG3, height=30)
        sf_top.pack(fill="x"); sf_top.pack_propagate(False)
        canvas_title = tk.Label(sf_top, text=self._t("sf_hdr"), bg=BG3, fg=FG_DIM, font=FONT_UIB)
        canvas_title.pack(side="left", padx=12, pady=6)
        reg.append(lambda w=canvas_title: w.config(text=self._t("sf_hdr")))
        ctx['canvas_title'] = canvas_title

        expand_all = tk.BooleanVar(value=False)
        ctx['expand_all'] = expand_all
        tk.Checkbutton(sf_top, text="전체 계층 표시", variable=expand_all,
                       command=lambda m=mode: self._redraw_sf_canvas(m),
                       bg=BG3, fg=FG_DIM, font=FONT_SM,
                       selectcolor=PANEL, activebackground=BG3).pack(side="right", padx=12)

        cv_scroll_frame = tk.Frame(canvas_frame, bg=BG)
        cv_scroll_frame.pack(fill="both", expand=True)
        cv_vsb = ttk.Scrollbar(cv_scroll_frame, orient="vertical")
        cv_vsb.pack(side="right", fill="y")
        cv_hsb = ttk.Scrollbar(cv_scroll_frame, orient="horizontal")
        cv_hsb.pack(side="bottom", fill="x")
        cv = tk.Canvas(cv_scroll_frame, bg=BG, highlightthickness=0,
                       yscrollcommand=cv_vsb.set, xscrollcommand=cv_hsb.set)
        cv.pack(fill="both", expand=True)
        cv_vsb.config(command=cv.yview)
        cv_hsb.config(command=cv.xview)
        cv.bind("<MouseWheel>", lambda e, c=cv: c.yview_scroll(int(-e.delta/120), "units"))
        cv.bind("<Button-4>",   lambda e, c=cv: c.yview_scroll(-1, "units"))
        cv.bind("<Button-5>",   lambda e, c=cv: c.yview_scroll( 1, "units"))
        ctx['canvas'] = cv
        cv.create_text(10, 20, anchor="nw", text=self._t("no_scan_result"),
                       fill=FG_DIM, font=FONT_UI, tags="hint")

    def _rebuild_graph(self):
        with self._graph_lock:
            self._graph_ready = False
        self._build_graph()
        self.root.after(0, self._refresh_v2_panels)

    def _sf_apply_filter(self, mode='name'):
        ctx = self._sf_ctx.get(mode, {})
        search = ctx.get('search_var', tk.StringVar()).get().strip().upper()
        tokens = [t for t in WORD_SEP.split(search) if t] if search else []
        vio_only = ctx.get('vio_only', tk.BooleanVar(value=False)).get()
        all_vios = ctx.get('all_vios', [])

        filtered = []
        for v in all_vios:
            if vio_only and v.get("unset"): continue
            if tokens:
                target = " ".join([v.get("name",""), v.get("work_unit",""),
                                   v.get("current_bus",""), v.get("expected_bus_keyword",""),
                                   v.get("path","")])
                hay = {t.upper() for t in WORD_SEP.split(target) if t}
                if not all(t in hay for t in tokens): continue
            filtered.append(v)

        ctx['vio_filtered'] = filtered
        self._populate_sf_vio_tree(filtered, mode)
        lbl = ctx.get('count_lbl')
        if lbl:
            lbl.config(text=f"{len(filtered)} / {len(all_vios)}",
                       fg=ERR_CLR if len(filtered) < len(all_vios) else FG_DIM)

    def _populate_sf_vio_tree(self, violations, mode='name'):
        vt = self._sf_ctx.get(mode, {}).get('vio_tree')
        if not vt: return
        vt.delete(*vt.get_children())
        for i, v in enumerate(violations):
            st = v.get("scan_type", "name")
            src_lbl = "이름" if st == "name" else "WU"
            sfx = "e" if i % 2 == 0 else "o"
            if v.get("unset"):       row_tag = f"uns_{sfx}"
            elif v.get("inherited"): row_tag = f"inh_{sfx}"
            else:                    row_tag = f"ovr_{sfx}"
            src_tag = "src_name" if st == "name" else "src_wu"
            tags = (row_tag, src_tag)
            vt.insert("", "end", values=(
                src_lbl, v["name"], v["work_unit"], v["current_bus"],
                v.get("expected_bus_keyword",""), v["path"],
            ), tags=tags)

    def _on_sf_bus_select(self, mode='name'):
        ctx = self._sf_ctx.get(mode, {})
        bt = ctx.get('bus_tree')
        if not bt: return
        sel = bt.selection()
        if not sel: return
        iid = sel[0]
        bus_name = bt.item(iid, "text")
        all_vios = list(self.results_name if mode == 'name' else self.results_wu)
        if iid == "__all__":
            ctx['all_vios'] = all_vios
        else:
            tags = bt.item(iid, "tags")
            if "warn" in tags:
                # 주황(조상 버스) → 서브트리 전체 위반 표시
                subtree_keys = {n.replace(" ","").lower() for n in self._get_bus_subtree_names(bt, iid)}
                ctx['all_vios'] = [
                    v for v in all_vios
                    if (v.get("current_bus","").replace("  ↑","").strip().replace(" ","").lower()
                        or "masteraudiobus") in subtree_keys
                ]
            else:
                # 빨강(직접 위반 버스) → 정확 매칭만
                bus_key = bus_name.replace(" ","").lower()
                ctx['all_vios'] = [
                    v for v in all_vios
                    if (v.get("current_bus","").replace("  ↑","").strip().replace(" ","").lower()
                        or "masteraudiobus") == bus_key
                ]
        title = bus_name if iid != "__all__" else "전체"
        lbl = ctx.get('vio_title')
        if lbl: lbl.config(text=f"{title}  위반 목록")
        self._sf_apply_filter(mode)
        self._clear_sf_canvas(mode)

    def _on_sf_vio_select(self, mode='name'):
        ctx = self._sf_ctx.get(mode, {})
        vt = ctx.get('vio_tree')
        if not vt: return
        sel = vt.selection()
        if not sel: return
        idx = vt.index(sel[0])
        vio_filtered = ctx.get('vio_filtered', [])
        if 0 <= idx < len(vio_filtered):
            v = vio_filtered[idx]
            ctx['cur_vio']  = v
            ctx['cur_path'] = v.get("path","")
            lbl = ctx.get('canvas_title')
            if lbl: lbl.config(text=f"{self._t('sf_hdr')}  —  {v['name']}")
            self._redraw_sf_canvas(mode)

    def _on_sf_vio_double(self, mode='name'):
        ctx = self._sf_ctx.get(mode, {})
        vt = ctx.get('vio_tree')
        if not vt: return
        sel = vt.selection()
        if not sel: return
        idx = vt.index(sel[0])
        vio_filtered = ctx.get('vio_filtered', [])
        if 0 <= idx < len(vio_filtered):
            obj_id = vio_filtered[idx].get("id", "")
            if obj_id:
                threading.Thread(target=self._select_in_wwise, args=(obj_id,), daemon=True).start()

    @staticmethod
    def _brighten_hex(color, amt=30):
        """hex 색상을 amt만큼 밝게."""
        c = color.lstrip('#')
        if len(c) != 6: return color
        r, g, b = int(c[0:2],16), int(c[2:4],16), int(c[4:6],16)
        return f"#{min(255,r+amt):02x}{min(255,g+amt):02x}{min(255,b+amt):02x}"

    @staticmethod
    def _clip_text(text, max_px, font_spec):
        """텍스트가 max_px를 초과하면 '…' 붙여 잘라냄."""
        f = tkfont.Font(font=font_spec)
        if f.measure(text) <= max_px:
            return text
        while text:
            text = text[:-1]
            if f.measure(text + "…") <= max_px:
                return text + "…"
        return "…"

    def _clear_sf_canvas(self, mode='name'):
        ctx = self._sf_ctx.get(mode, {})
        cv = ctx.get('canvas')
        if not cv: return
        cv.delete("all")
        cv.create_text(10, 20, anchor="nw", text=self._t("sf_select_item"),
                       fill=FG_DIM, font=FONT_UI, tags="hint")
        ctx['cur_path'] = None
        ctx['cur_vio']  = None

    def _redraw_sf_canvas(self, mode='name'):
        ctx = self._sf_ctx.get(mode, {})
        if not ctx.get('cur_path') or not ctx.get('cur_vio'):
            return
        cv = ctx.get('canvas')
        if not cv: return
        cv.delete("all")

        if not self._graph_ready:
            cv.create_text(10, 20, anchor="nw", text=self._t("graph_not_ready"),
                           fill=WARN, font=FONT_UI)
            return

        chain = self._get_signal_chain(ctx['cur_path'])
        expand_all = ctx.get('expand_all', tk.BooleanVar(value=False)).get()
        vio = ctx['cur_vio']

        # 결정 지점 탐색 (OverrideOutput=True인 가장 가까운 조상)
        decision_idx = None
        for i, node in enumerate(chain):
            if node.get("override_output", False):
                decision_idx = i
                break

        # 표시할 노드 구성
        # decision_idx==0: Sound 자신이 결정지점 → 전체 표시
        if expand_all or decision_idx is None or decision_idx == 0 or len(chain) <= 5:
            display_nodes = [(n, False, False) for n in chain]
        else:
            # Sound (0) + 축약 + 결정지점 이후
            visible_before  = chain[:1]                                    # Sound 자신
            collapsed_range = chain[1:decision_idx] if decision_idx > 1 else []
            visible_after   = chain[decision_idx:]                         # 결정지점 이후
            display_nodes = ([(n, False, False) for n in visible_before] +
                             ([(None, True, len(collapsed_range))] if collapsed_range else []) +
                             [(n, False, False) for n in visible_after])

        # ── 수평 좌→우 레이아웃 ─────────────────────────────────────────────
        NW    = 160   # 노드 너비
        NH    = 52    # 노드 높이
        CW    = 64    # collapsed 노드 너비
        HGAP  = 28    # 노드 간 화살표 공간
        IW    = 15    # 아이콘 너비/높이
        IP    = 5     # 아이콘 패딩
        PAD_X = 20; PAD_Y = 16
        L1    = 15    # 줄1 y offset (아이콘+타입)
        L2    = 36    # 줄2 y offset (이름)

        cur_bus = vio.get("current_bus","").replace("  ↑","").strip()
        exp_kw  = vio.get("expected_bus_keyword","")

        ny  = PAD_Y            # 노드 상단 y
        cy  = PAD_Y + NH//2    # 노드 중앙 y (화살표 y)
        x   = PAD_X

        def _draw_arrow(x1, x2, color, dashed=False):
            kw = {"dash": (4, 3)} if dashed else {}
            cv.create_line(x1, cy, x2 - 6, cy, fill=color, width=1, **kw)
            cv.create_polygon(x2-9, cy-4, x2-9, cy+4, x2, cy,
                              fill=color, outline=color)

        _node_counter = [0]

        def _draw_node(nx, nw, fill, outline, img, type_lbl, type_fg, name, name_fg,
                       is_star=False, obj_id=None):
            rect = cv.create_rectangle(nx, ny, nx+nw, ny+NH, fill=fill, outline=outline, width=1)
            # 줄1: 아이콘 + 타입 레이블
            tx1 = nx + IP + (IW + 3 if img else 0)
            if img:
                cv.create_image(nx + IP + IW//2, ny + L1, image=img)
            prefix = "★ " if is_star else ""
            cv.create_text(tx1, ny + L1,
                           text=self._clip_text(prefix + type_lbl, nw - (tx1 - nx) - IP, FONT_SM),
                           fill=type_fg, font=FONT_SM, anchor="w")
            # 줄2: 이름
            cv.create_text(nx + IP, ny + L2,
                           text=self._clip_text(name, nw - IP*2, FONT_CODE),
                           fill=name_fg, font=FONT_CODE, anchor="w")
            # hover / click 피드백
            if obj_id and self.client:
                tag = f"node_{_node_counter[0]}"
                _node_counter[0] += 1
                cv.create_rectangle(nx, ny, nx+nw, ny+NH, fill="", outline="", tags=tag)
                h_outline = self._brighten_hex(outline, 60)
                h_fill    = self._brighten_hex(fill, 20)
                cv.tag_bind(tag, "<Enter>",
                            lambda e, r=rect, ho=h_outline, of=outline:
                                (cv.itemconfig(r, outline=ho, width=2),
                                 cv.config(cursor="hand2")))
                cv.tag_bind(tag, "<Leave>",
                            lambda e, r=rect, of=outline, ff=fill:
                                (cv.itemconfig(r, outline=of, width=1, fill=ff),
                                 cv.config(cursor="")))
                cv.tag_bind(tag, "<Button-1>",
                            lambda e, r=rect, ff=fill, hf=h_fill, oid=obj_id:
                                (cv.itemconfig(r, fill=hf),
                                 cv.after(130, lambda: cv.itemconfig(r, fill=ff)),
                                 threading.Thread(target=self._select_in_wwise,
                                                  args=(oid,), daemon=True).start()))

        for item in display_nodes:
            node, is_collapsed, collapse_count = item if len(item) == 3 else (item[0], False, 0)
            nw = CW if is_collapsed else NW

            if is_collapsed:
                cv.create_rectangle(x, ny, x+CW, ny+NH,
                                    fill=BG2, outline=BORDER, width=1, dash=(4,4))
                cv.create_text(x+CW//2, cy,
                               text=f"··· {collapse_count}",
                               fill=FG_DIM, font=FONT_SM, anchor="center")
                hit = cv.create_rectangle(x, ny, x+CW, ny+NH, fill="", outline="", tags="collapsed_hit")
                cv.tag_bind("collapsed_hit", "<Button-1>",
                            lambda e, m=mode, c=ctx: (c['expand_all'].set(True), self._redraw_sf_canvas(m)))
                cv.tag_bind("collapsed_hit", "<Enter>", lambda e: cv.config(cursor="hand2"))
                cv.tag_bind("collapsed_hit", "<Leave>", lambda e: cv.config(cursor=""))
            else:
                ntype      = node.get("type","")
                is_decision= node.get("override_output", False)
                nname      = node.get("name","")
                img        = self._type_icons.get(ntype)

                if ntype == "Sound":
                    fill, outline = BG2, BORDER
                    t_fg, n_fg = FG_DIM, FG
                elif is_decision:
                    fill, outline = BG3, ACCENT
                    t_fg, n_fg = ACCENT, ACCENT
                else:
                    fill, outline = BG, BORDER
                    t_fg, n_fg = FG_MUT, FG_DIM

                _draw_node(x, NW, fill, outline, img,
                           ntype, t_fg, nname, n_fg, is_star=is_decision,
                           obj_id=node.get("id",""))

            # 화살표 (마지막 노드 제외)
            if item != display_nodes[-1]:
                _draw_arrow(x + nw, x + nw + HGAP, BORDER)

            x += nw + HGAP

        # ── 현재 버스 노드 ──────────────────────────────────────────────────────
        # 루프가 끝날 때 x = 마지막_노드_끝 + HGAP 이므로 화살표는 (x-HGAP) → (x)
        _draw_arrow(x - HGAP, x, ERR_CLR, dashed=True)
        bus_x = x
        bus_img = self._type_icons.get("Bus")
        cur_bus_display = cur_bus or "Master Audio Bus"
        cur_bus_id = vio.get("current_bus_id", "")
        cv.create_rectangle(bus_x, ny, bus_x+NW, ny+NH, fill="#2A0508", outline=ERR_CLR, width=1)
        btx1 = bus_x + IP + (IW + 3 if bus_img else 0)
        if bus_img:
            cv.create_image(bus_x + IP + IW//2, ny + L1, image=bus_img)
        cv.create_text(btx1, ny + L1,
                       text=self._clip_text(f"Bus  ✗  {self._t('cur_bus_label')}",
                                            NW-(btx1-bus_x)-IP, FONT_SM),
                       fill=ERR_CLR, font=FONT_SM, anchor="w")
        cv.create_text(bus_x + IP, ny + L2,
                       text=self._clip_text(cur_bus_display, NW - IP*2, FONT_CODE),
                       fill=ERR_CLR, font=FONT_CODE, anchor="w")
        if cur_bus_id and self.client:
            _btag = f"node_{_node_counter[0]}"; _node_counter[0] += 1
            _brect = cv.find_withtag("current")[0] if cv.find_withtag("current") else None
            # bus rect는 바로 위에서 그린 마지막 rectangle
            _bus_items = [i for i in cv.find_all()
                          if cv.type(i) == "rectangle"
                          and cv.coords(i) == [float(bus_x), float(ny), float(bus_x+NW), float(ny+NH)]]
            _brect = _bus_items[0] if _bus_items else None
            _bh_outline = self._brighten_hex(ERR_CLR, 40)
            _bh_fill    = self._brighten_hex("#2A0508", 20)
            cv.create_rectangle(bus_x, ny, bus_x+NW, ny+NH, fill="", outline="", tags=_btag)
            cv.tag_bind(_btag, "<Enter>",
                        lambda e, r=_brect, ho=_bh_outline:
                            (cv.itemconfig(r, outline=ho, width=2) if r else None,
                             cv.config(cursor="hand2")))
            cv.tag_bind(_btag, "<Leave>",
                        lambda e, r=_brect:
                            (cv.itemconfig(r, outline=ERR_CLR, width=1, fill="#2A0508") if r else None,
                             cv.config(cursor="")))
            cv.tag_bind(_btag, "<Button-1>",
                        lambda e, r=_brect, oid=cur_bus_id:
                            (cv.itemconfig(r, fill=_bh_fill) if r else None,
                             cv.after(130, lambda: cv.itemconfig(r, fill="#2A0508") if r else None),
                             threading.Thread(target=self._select_in_wwise,
                                              args=(oid,), daemon=True).start()))
        x = bus_x + NW + HGAP

        # ── 기대 버스 키워드 노드 ──────────────────────────────────────────────
        if exp_kw:
            _draw_arrow(x - HGAP, x, OK_CLR, dashed=True)
            exp_x = x
            cv.create_rectangle(exp_x, ny, exp_x+NW, ny+NH, fill="#061A0D", outline=OK_CLR, width=1)
            cv.create_text(exp_x + IP, ny + L1,
                           text=self._clip_text(f"기대 버스  ✓  {self._t('exp_bus_label')}",
                                                NW - IP*2, FONT_SM),
                           fill=OK_CLR, font=FONT_SM, anchor="w")
            cv.create_text(exp_x + IP, ny + L2,
                           text=self._clip_text(exp_kw, NW - IP*2, FONT_CODE),
                           fill=OK_CLR, font=FONT_CODE, anchor="w")
            x = exp_x + NW + PAD_X

        cv.configure(scrollregion=(0, 0, x, NH + PAD_Y * 2))

    def _sf_action_view(self, mode='name'):
        ctx = self._sf_ctx.get(mode, {})
        vt = ctx.get('vio_tree')
        if not vt: return
        sel = vt.selection()
        if not sel:
            messagebox.showinfo(self._t("info_title"), self._t("select_item"), parent=self.root); return
        if not self.client:
            messagebox.showerror(self._t("error_title"), self._t("no_wwise"), parent=self.root); return
        idx = vt.index(sel[0])
        vf = ctx.get('vio_filtered', [])
        if 0 <= idx < len(vf):
            threading.Thread(target=self._select_in_wwise, args=(vf[idx]["id"],), daemon=True).start()

    def _sf_action_reroute(self, mode='name'):
        ctx = self._sf_ctx.get(mode, {})
        vt = ctx.get('vio_tree')
        if not vt: return
        sel = vt.selection()
        if not sel:
            messagebox.showinfo(self._t("info_title"), self._t("select_reroute"), parent=self.root); return
        if not self.client:
            messagebox.showerror(self._t("error_title"), self._t("no_wwise"), parent=self.root); return
        idx = vt.index(sel[0])
        vf = ctx.get('vio_filtered', [])
        if 0 <= idx < len(vf):
            self._show_fix_dialog([vf[idx]], True)

    # ══════════════════════════════════════════════════════════════════════════
    # V2: Heatmap Tab
    # ══════════════════════════════════════════════════════════════════════════

    def _build_heatmap_tab(self, parent, mode='name'):
        reg = self._lang_updaters
        hctx = {}
        self._hm_ctx[mode] = hctx

        top = tk.Frame(parent, bg=BG3, height=40)
        top.pack(fill="x"); top.pack_propagate(False)
        tk.Frame(top, bg=ACCENT2 if True else ACCENT, height=2).pack(fill="x", side="bottom")

        _hm_hdr_key = "hm_hdr_name" if mode == 'name' else "hm_hdr_wu"
        lbl_hm = tk.Label(top, text=self._t(_hm_hdr_key), bg=BG3, fg=FG, font=FONT_H2)
        lbl_hm.pack(side="left", padx=16, pady=8)
        reg.append(lambda w=lbl_hm, k=_hm_hdr_key: w.config(text=self._t(k)))

        lbl_hint = tk.Label(top, text=self._t("heatmap_hint"), bg=BG3, fg=FG_DIM, font=FONT_SM)
        lbl_hint.pack(side="left", padx=8)
        reg.append(lambda w=lbl_hint: w.config(text=self._t("heatmap_hint")))

        # 위반율 정의 안내
        lbl_def = tk.Label(top,
                           text="위반율 = 해당 버스에 직접 라우팅된 Sound 중 위반 감지된 비율",
                           bg=BG3, fg=FG_MUT, font=FONT_SM)
        lbl_def.pack(side="right", padx=16)

        cv_frame = tk.Frame(parent, bg=BG)
        cv_frame.pack(fill="both", expand=True)
        cv_vsb = ttk.Scrollbar(cv_frame, orient="vertical")
        cv_vsb.pack(side="right", fill="y")
        cv_hsb = ttk.Scrollbar(cv_frame, orient="horizontal")
        cv_hsb.pack(side="bottom", fill="x")
        hm_cv = tk.Canvas(cv_frame, bg=BG, highlightthickness=0,
                          yscrollcommand=cv_vsb.set, xscrollcommand=cv_hsb.set)
        hm_cv.pack(fill="both", expand=True)
        cv_vsb.config(command=hm_cv.yview)
        cv_hsb.config(command=hm_cv.xview)
        hm_cv.bind("<MouseWheel>", lambda e, c=hm_cv: c.yview_scroll(int(-e.delta/120), "units"))
        hm_cv.bind("<Button-4>",   lambda e, c=hm_cv: c.yview_scroll(-1, "units"))
        hm_cv.bind("<Button-5>",   lambda e, c=hm_cv: c.yview_scroll( 1, "units"))
        hctx['canvas'] = hm_cv
        hm_cv.create_text(20, 30, anchor="nw", text=self._t("no_scan_result"),
                          fill=FG_DIM, font=FONT_UI, tags="hint")

    def _update_heatmap(self, mode='name'):
        """버스 위반 히트맵.
        룰/키워드와 무관하게 프로젝트 전체 버스를 계층 순서대로 나열.
        위반율 = 해당 버스에 직접 라우팅된 Sound 중 위반으로 감지된 Sound의 비율.
        색상: 초록(위반 없음) / 노랑(<15%) / 주황(15~35%) / 빨강(35%+)
        """
        hctx = self._hm_ctx.get(mode, {})
        cv = hctx.get('canvas')
        if not cv: return
        cv.delete("all")

        scanned = (self._scanned_name if mode == 'name' else self._scanned_wu)
        if not scanned:
            cv.create_text(20, 30, anchor="nw", text=self._t("no_scan_result"),
                           fill=FG_DIM, font=FONT_UI, tags="hint")
            return

        all_vios = list(self.results_name if mode == 'name' else self.results_wu)

        # 위반 버스 카운트 (현재 버스 이름 → 위반 수)
        bus_vio_cnt = {}
        for v in all_vios:
            bn = v.get("current_bus","").replace("  ↑","").strip() or "Master Audio Bus"
            bus_vio_cnt[bn] = bus_vio_cnt.get(bn, 0) + 1

        # 전체 Sound 수 (버스별)
        bus_total_cnt = {}
        if self._graph_ready:
            with self._graph_lock:
                for path, node in self._graph.items():
                    if node.get("type") != "Sound": continue
                    eff_bus = node.get("output_bus", {})
                    bn = (eff_bus.get("name","") if eff_bus else "") or "Master Audio Bus"
                    bus_total_cnt[bn] = bus_total_cnt.get(bn, 0) + 1

        # 버스 순서: _bus_hierarchy의 계층 순서(DFS, 루트 먼저)
        ordered_buses = []  # (display_name, depth)
        if self._bus_hierarchy:
            visited = set()
            def _dfs(bpath, depth):
                if bpath in visited: return
                visited.add(bpath)
                info = self._bus_hierarchy.get(bpath)
                if not info: return
                ordered_buses.append((info["name"], depth, bpath))
                # 자식 버스들 (부모가 bpath인 것)
                children = sorted(
                    [p for p, i in self._bus_hierarchy.items() if i["parent_path"] == bpath],
                    key=lambda p: self._bus_hierarchy[p]["name"].lower()
                )
                for child in children:
                    _dfs(child, depth + 1)
            # 루트 버스들 (parent_path가 없거나 계층 외)
            roots = sorted(
                [p for p, i in self._bus_hierarchy.items()
                 if not i["parent_path"] or i["parent_path"] not in self._bus_hierarchy],
                key=lambda p: self._bus_hierarchy[p]["name"].lower()
            )
            for r in roots:
                _dfs(r, 0)
        else:
            # 그래프 없으면 위반 있는 버스만 표시
            for bn in sorted(bus_vio_cnt.keys()):
                ordered_buses.append((bn, 0, bn))

        if not ordered_buses:
            cv.create_text(20, 30, anchor="nw", text="버스 정보 없음 — Wwise 연결 후 재시도",
                           fill=FG_DIM, font=FONT_UI, tags="hint")
            return

        # ── 레이아웃: 에셋 이름/WU 기준 모두 동일하게 가로 격자 ──────────────
        CELL_W = 130; CELL_H = 76; PAD = 14; GAP = 6
        cv.update_idletasks()
        cv_w = max(cv.winfo_width(), 800)
        COLS = max(1, (cv_w - PAD * 2 + GAP) // (CELL_W + GAP))

        # 범례
        leg_items = [
            ("✓ 위반 없음", OK_CLR), ("△ <15%", WARN),
            ("▲ 15~35%", "#E07040"), ("✗ 35%+", ERR_CLR),
        ]
        lx = PAD
        for txt, col in leg_items:
            cv.create_text(lx, 14, anchor="w", text=txt, fill=col, font=FONT_SM)
            lx += len(txt) * 6 + 28

        y_start = 32
        for i, (bus_name, depth, bpath) in enumerate(ordered_buses):
            col_i = i % COLS
            row_i = i // COLS
            cx = PAD + col_i * (CELL_W + GAP)
            cy = y_start + row_i * (CELL_H + GAP)

            vio_count = bus_vio_cnt.get(bus_name, 0)
            total     = bus_total_cnt.get(bus_name, 0)
            ratio     = vio_count / total if total > 0 else 0

            # 색상 결정
            if vio_count == 0:
                fill, outline, fg = "#061410", "#1A4020", OK_CLR
            elif ratio < 0.15:
                fill, outline, fg = "#1A1500", "#4A3A00", WARN
            elif ratio < 0.35:
                fill, outline, fg = "#1A0A00", "#5A2A00", "#E07040"
            else:
                fill, outline, fg = "#1A0305", "#6A1010", ERR_CLR

            cell_id = cv.create_rectangle(cx, cy, cx+CELL_W, cy+CELL_H,
                                          fill=fill, outline=outline, width=1)

            # 들여쓰기 인디케이터 (depth > 0)
            if depth > 0:
                indent_w = min(depth * 3, 8)
                cv.create_rectangle(cx, cy, cx + indent_w, cy + CELL_H,
                                    fill=BORDER, outline="", width=0)

            # 위반 수 / 체크
            badge_txt = f"✗ {vio_count}건" if vio_count > 0 else "✓"
            cv.create_text(cx + CELL_W // 2, cy + 16,
                           text=badge_txt, fill=fg, font=FONT_CODE_B, anchor="center")

            # 버스 이름
            short = bus_name if len(bus_name) <= 15 else bus_name[:13] + "…"
            cv.create_text(cx + CELL_W // 2, cy + 36,
                           text=short, fill=fg, font=FONT_SM, anchor="center")

            # 위반율 / 총 수
            if total > 0:
                pct = f"{vio_count}/{total}  ({ratio*100:.0f}%)" if vio_count > 0 else f"총 {total}개"
                cv.create_text(cx + CELL_W // 2, cy + 58,
                               text=pct, fill=FG_MUT, font=("Consolas", 7), anchor="center")
            elif vio_count > 0:
                cv.create_text(cx + CELL_W // 2, cy + 58,
                               text=f"{vio_count}건 (전체 수 미확인)",
                               fill=FG_MUT, font=("Consolas", 7), anchor="center")

            # 클릭 → 신호 흐름 탭
            tag = f"hm_{i}"
            cv.create_rectangle(cx, cy, cx + CELL_W, cy + CELL_H,
                                fill="", outline="", tags=tag)
            cv.tag_bind(tag, "<Button-1>",
                        lambda e, bn=bus_name, m=mode: self._hm_click_bus(bn, m))
            cv.tag_bind(tag, "<Enter>",
                        lambda e, ci=cell_id: (
                            cv.config(cursor="hand2"),
                            cv.itemconfig(ci, outline=ACCENT, width=2)))
            cv.tag_bind(tag, "<Leave>",
                        lambda e, oc=outline, ci=cell_id: (
                            cv.config(cursor=""),
                            cv.itemconfig(ci, outline=oc, width=1)))

        total_rows = (len(ordered_buses) + COLS - 1) // COLS
        total_h = y_start + total_rows * (CELL_H + GAP) + PAD
        total_w = PAD + COLS * (CELL_W + GAP)
        cv.configure(scrollregion=(0, 0, total_w, total_h))

    def _hm_click_bus(self, bus_name, mode='name'):
        """히트맵 셀 클릭 → 같은 스캔의 신호 흐름 탭으로 이동하고 해당 버스 선택."""
        if mode == 'name' and hasattr(self, '_nb1'):
            self._nb.select(0); self._nb1.select(1)
        elif mode == 'wu' and hasattr(self, '_nb2'):
            self._nb.select(1); self._nb2.select(1)
        bt = self._sf_ctx.get(mode, {}).get('bus_tree')
        if not bt: return
        def _search(children):
            for iid in children:
                if bt.item(iid, "text") == bus_name:
                    bt.selection_set(iid); bt.see(iid)
                    self._on_sf_bus_select(mode); return True
                if _search(bt.get_children(iid)): return True
            return False
        _search(bt.get_children())

    # ══════════════════════════════════════════════════════════════════════════
    # V2: Refresh
    # ══════════════════════════════════════════════════════════════════════════

    def _refresh_v2_panels(self):
        for m in ('name', 'wu'):
            self._update_sf_bus_tree(m)
            self._update_heatmap(m)

    def _get_bus_subtree_names(self, bt, iid):
        names = set()
        stack = [iid]
        while stack:
            cur = stack.pop()
            names.add(bt.item(cur, "text"))
            stack.extend(bt.get_children(cur))
        return names

    def _update_sf_bus_tree(self, mode='name'):
        ctx = self._sf_ctx.get(mode, {})
        bt = ctx.get('bus_tree')
        if not bt: return

        all_vios = list(self.results_name if mode == 'name' else self.results_wu)

        bus_vio_cnt = {}
        for v in all_vios:
            bn = v.get("current_bus","").replace("  ↑","").strip()
            key = bn.replace(" ","").lower() or "masteraudiobus"
            bus_vio_cnt[key] = bus_vio_cnt.get(key, 0) + 1

        bt.delete(*bt.get_children())

        total_cnt = len(all_vios)
        bt.insert("", "end", iid="__all__", text=self._t("all_buses"),
                  values=(total_cnt if total_cnt else "",),
                  tags=("err" if total_cnt else "ok", "all"))

        if self._bus_hierarchy:
            # 직접 위반 있는 버스 경로
            vio_paths = {bp for bp, info in self._bus_hierarchy.items()
                         if bus_vio_cnt.get(info["name"].replace(" ","").lower(), 0) > 0}
            # 조상 경로 집합
            ancestor_paths = set()
            for bp in vio_paths:
                cur = self._bus_hierarchy.get(bp, {}).get("parent_path", "")
                while cur and cur in self._bus_hierarchy:
                    ancestor_paths.add(cur)
                    cur = self._bus_hierarchy[cur]["parent_path"]

            inserted = {}
            def _insert_bus(bpath):
                if bpath in inserted: return inserted[bpath]
                info = self._bus_hierarchy.get(bpath)
                if not info: return None
                bname = info["name"]
                parent_path = info["parent_path"]
                parent_iid = ""
                if parent_path and parent_path in self._bus_hierarchy:
                    parent_iid = _insert_bus(parent_path) or ""
                cnt = bus_vio_cnt.get(bname.replace(" ","").lower(), 0)
                if cnt > 0:         tag = "err"   # 직접 위반 → 빨강
                elif bpath in ancestor_paths: tag = "warn"  # 조상 → 주황
                else:               tag = "dim"
                iid = bt.insert(parent_iid, "end", iid=bpath, text=bname,
                                values=(cnt if cnt else "",), tags=(tag,))
                inserted[bpath] = iid
                return iid
            for bpath in self._bus_hierarchy:
                _insert_bus(bpath)
            # 위반 버스까지 자동 펼치기
            for bp in vio_paths:
                cur = bp
                while cur and cur in self._bus_hierarchy:
                    try: bt.item(cur, open=True)
                    except Exception: pass
                    cur = self._bus_hierarchy[cur]["parent_path"]
        else:
            for key, cnt in sorted(bus_vio_cnt.items(), key=lambda x: -x[1]):
                tag = "err" if cnt > 10 else "warn" if cnt > 0 else "dim"
                bt.insert("", "end", text=key, values=(cnt,), tags=(tag,))

        bt.selection_set("__all__")
        self._on_sf_bus_select(mode)

        gs = ctx.get('graph_status')
        if gs:
            if self._graph_ready:
                with self._graph_lock: cnt = len(self._graph)
                gs.config(text=self._t("graph_ready_fmt").format(cnt), fg=OK_CLR)
            else:
                gs.config(text=self._t("graph_not_ready"), fg=WARN)


def main():
    import ctypes
    _TITLE = "Bus Routing Auditor  —  Wwise"
    hwnd = ctypes.windll.user32.FindWindowW(None, _TITLE)
    if hwnd:
        ctypes.windll.user32.ShowWindow(hwnd, 9)
        ctypes.windll.user32.SetForegroundWindow(hwnd)
        return
    root = tk.Tk()
    BusRoutingAuditor(root)
    root.mainloop()


if __name__ == "__main__":
    main()
