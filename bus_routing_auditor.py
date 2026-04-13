#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json, os, csv, threading, time, re, socket

try:
    from waapi import WaapiClient, CannotConnectToWaapiException
    WAAPI_AVAILABLE = True
except ImportError:
    WAAPI_AVAILABLE = False

VERSION     = "V.1.0.0"
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
        "view_wwise":     "⊙ Wwise에서 보기",
        "reroute":        "⟲ 일괄 재라우팅",
        "select_all":     "전체 선택",
        "export_csv":     "↓ CSV 내보내기",
        "connecting":     "Wwise 연결 중...",
        "connected_fmt":  "연결됨  ·  {}  ·  버스 {}개",
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
            "┌─ Work Unit / 경로 키워드 — 매칭 방식 ────────────────────\n"
            "│  입력한 키워드가 아래 항목 중 하나라도 포함되면 매칭됩니다:\n"
            "│    · Work Unit 이름\n"
            "│    · Work Unit 전체 경로\n"
            "│    · Sound의 상위 계층 경로 (Sound 이름 자신 제외)\n"
            "│\n"
            "│  ⚠ 부분 이름도 매칭됩니다 (단어 경계 기준)\n"
            "│  예) 키워드: VIDEO\n"
            "│      → VIDEO_Main ✓  /  VIDEO_Dialogue ✓  /  VIDEO ✓\n"
            "│      → VIDEOGAME ✗  (단어 경계 없음)\n"
            "│\n"
            "│  특정 Work Unit만 검색하려면 이름 전체를 키워드로 입력하세요.\n"
            "│  예) 'VIDEO_Main' 만 검색 → 키워드: VIDEO_Main\n"
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
    },
    "en": {
        "reconnect":      "⟳  Reconnect",
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
        "view_wwise":     "⊙ View in Wwise",
        "reroute":        "⟲ Bulk Reroute",
        "select_all":     "Select All",
        "export_csv":     "↓ Export CSV",
        "connecting":     "Connecting to Wwise...",
        "connected_fmt":  "Connected  ·  {}  ·  {} buses",
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
            "┌─ Work Unit / Path Keyword — How matching works ─────────\n"
            "│  A keyword matches if it appears in any of the following:\n"
            "│    · Work Unit name\n"
            "│    · Work Unit full path\n"
            "│    · Sound's parent hierarchy path (Sound's own name excluded)\n"
            "│\n"
            "│  ⚠ Partial names also match (at word boundaries)\n"
            "│  e.g. keyword: VIDEO\n"
            "│      → VIDEO_Main ✓  /  VIDEO_Dialogue ✓  /  VIDEO ✓\n"
            "│      → VIDEOGAME ✗  (no word boundary)\n"
            "│\n"
            "│  To target a specific Work Unit, enter its full name.\n"
            "│  e.g. search only 'VIDEO_Main' → keyword: VIDEO_Main\n"
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
    },
}

BG="#1E1E1E"; BG2="#252526"; BG3="#2D2D30"; PANEL="#333337"; ACCENT="#0078D4"
DANGER="#C1121F"; OK_CLR="#6BCB77"; WARN="#FFD93D"; ERR_CLR="#FF6B6B"
FG="#DCDCDC"; FG_DIM="#888888"
MONO=("Consolas",9); MONO_B=("Consolas",9,"bold"); MONO_LG=("Consolas",10,"bold")

FIND_CMD_PRIMARY = ["FindInProjectExplorerSelectionChannel1","FindInProjectExplorer","FindInProjectExplorer1"]
SEARCH_FIELDS      = ["", "name", "work_unit", "current_bus", "expected_bus_keyword"]
SEARCH_FIELD_SKEYS = ["search_all", "col_name", "col_work_unit", "col_cur_bus", "col_exp_kw"]


class BusRoutingAuditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Bus Routing Auditor  —  Wwise")
        self.root.geometry("1200x780")
        self.root.minsize(900, 600)
        self.root.configure(bg=BG)
        self.client = None
        self._was_connected = False
        self.results_name = []; self.results_wu = []
        self.filtered_name = []; self.filtered_wu = []
        self._scanned_name = False; self._scanned_wu = False
        self.buses = {}
        self._find_cmd = None
        self._sort_reverse = {}
        self.config = self._load_config()
        self._lang = "ko"
        self._lang_updaters = []
        self._nb = None; self._lang_btn = None
        self._search_field_idx_name = None; self._search_field_idx_wu = None
        self._apply_styles()
        self._build_ui()
        self._start_wwise_watchdog()
        self.root.after(200, lambda: threading.Thread(target=self._connect_waapi, daemon=True).start())

    def _t(self, key):
        return STRINGS[self._lang].get(key, STRINGS["ko"].get(key, key))

    def _toggle_lang(self):
        self._lang = "en" if self._lang == "ko" else "ko"
        self._refresh_lang()

    def _refresh_lang(self):
        for fn in self._lang_updaters:
            try: fn()
            except Exception: pass

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

    def _start_wwise_watchdog(self):
        def _watch():
            while True:
                time.sleep(3)
                if not self._was_connected:
                    continue
                try:
                    s = socket.create_connection(("127.0.0.1", 8080), timeout=2)
                    s.close()
                except Exception:
                    self.root.after(0, self.root.destroy)
                    return
        threading.Thread(target=_watch, daemon=True).start()

    def _connect_waapi(self):
        self._set_status(self._t("connecting"), WARN)
        if not WAAPI_AVAILABLE:
            self._set_status(self._t("no_waapi"), ERR_CLR); return
        try:
            if self.client:
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
            self._set_status(self._t("connected_fmt").format(proj_name, len(self.buses)), OK_CLR)
        except Exception as e:
            self.client = None
            self._set_status(self._t("connect_fail").format(e), ERR_CLR)

    def _fetch_buses(self):
        r = self.client.call("ak.wwise.core.object.get",
            {"from": {"ofType": ["Bus","AuxBus"]}, "options": {"return": ["id","name","path"]}})
        self.buses = {obj["name"]: obj["id"] for obj in r.get("return", [])}

    _HIERARCHY_TYPES = ["Sound","ActorMixer","BlendContainer","RandomSequenceContainer","SwitchContainer","WorkUnit","Folder"]

    def _get_all_sounds(self):
        r = self.client.call("ak.wwise.core.object.get", {
            "from": {"ofType": self._HIERARCHY_TYPES},
            "options": {"return": ["id","name","path","type","@OutputBus","@OverrideOutput","workunit"]},
        })
        all_objects = r.get("return", [])
        effective = self._resolve_effective_buses(all_objects)
        _DEFAULT = "masteraudiobus"
        sounds = []
        for obj in all_objects:
            if obj.get("type") != "Sound": continue
            path = obj.get("path", "")
            eff = effective.get(path) or {"name": "Master Audio Bus", "id": ""}
            # Phase 3 — Sound's own stale value as last resort.
            # Only fires when Phase 1+2 both returned nothing (eff = Master Audio Bus).
            # Handles synthesized SFX (Silence, ToneGenerator) whose parent containers
            # carry no stale bus entry but the Sound itself has @OutputBus set.
            # Safe against the ADM File3 regression: that Sound's ancestor DOES have
            # a stale entry, so Phase 2 returns non-default → this block is skipped.
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
            # Phase 2: walk to root, return the ROOT-NEAREST stale entry.
            # Intermediate containers may hold stale leftover values (e.g. a
            # moved sound's old bus still set on a subfolder).  Taking the
            # highest ancestor avoids those false positives while still
            # resolving WU-level bus assignments (Objects, Ambience, UI …).
            cur = path; last_val = {}
            while True:
                if cur in stale:
                    last_val = stale[cur]
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
            for rule in rules:
                cs = rule.get("case_sensitive", False)
                all_src = [rule["keyword"]] + rule.get("extra_keywords", [])
                all_bus = [rule["expected_bus_keyword"]] + rule.get("extra_bus_keywords", [])
                if not any(self._word_match(name, sk, cs) for sk in all_src): continue
                no_bus = not bus_name
                mismatch = (not no_bus) and not any(self._word_match(bus_name, bk, cs) for bk in all_bus)
                if mismatch or (no_bus and flag_unset):
                    violations.append({"id": sound.get("id",""), "name": name, "path": path,
                        "work_unit": wu_name, "current_bus": self._bus_display(bus_name, inherited),
                        "current_bus_id": bus_id, "trigger": f'이름에 "{" | ".join(all_src)}" 포함',
                        "expected_bus_keyword": " | ".join(all_bus), "unset": no_bus, "inherited": inherited})
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
            parent_path = path[:path.rfind("\\")] if "\\" in path else ""
            search = f"{wu_name} {wu_path} {parent_path}"
            for rule in rules:
                cs = rule.get("case_sensitive", False)
                all_src = [rule["work_unit_keyword"]] + rule.get("extra_work_unit_keywords", [])
                all_kws = [rule["expected_bus_keyword"]] + rule.get("extra_bus_keywords", [])
                if not any(self._word_match(search, sk, cs) for sk in all_src): continue
                no_bus = not bus_name
                mismatch = (not no_bus) and not any(self._word_match(bus_name, ek, cs) for ek in all_kws)
                if mismatch or (no_bus and flag_unset):
                    violations.append({"id": sound.get("id",""), "name": name, "path": path,
                        "work_unit": wu_name, "current_bus": self._bus_display(bus_name, inherited),
                        "current_bus_id": bus_id, "trigger": f'경로에 "{" | ".join(all_src)}" 포함',
                        "expected_bus_keyword": " | ".join(all_kws), "unset": no_bus, "inherited": inherited})
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
                    self.root.after(0, lambda: self._set_status(
                        self._t("scan_done_name").format(len(sounds), len(results)), ERR_CLR if results else OK_CLR))
                else:
                    self.results_wu = self._check_workunit_rules(sounds)
                    self._scanned_wu = True
                    results = self.results_wu
                    self.root.after(0, lambda: self._apply_filter("workunit"))
                    self.root.after(0, lambda: self._set_count(self.lbl_count_wu, len(sounds), len(results)))
                    self.root.after(0, lambda: self._set_status(
                        self._t("scan_done_wu").format(len(sounds), len(results)), ERR_CLR if results else OK_CLR))
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
            if not is_name:
                is_inh = r.get("inherited", True)
                if is_inh  and not self._wu_show_inherited.get(): continue
                if not is_inh and not self._wu_show_override.get(): continue
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
        for r in filtered:
            tree.insert("", "end", values=(
                r["name"], r["work_unit"], r["current_bus"],
                r["trigger"], r["expected_bus_keyword"], r["path"],
            ), tags=("unset" if r.get("unset") else "violation",))
        total = len(src); shown = len(filtered)
        scanned = self._scanned_name if is_name else self._scanned_wu
        lbl = self.lbl_count_name if is_name else self.lbl_count_wu
        if search_tokens or (not is_name and not (self._wu_show_inherited.get() and self._wu_show_override.get())):
            lbl.config(text=self._t("filter_applied").format(shown, total), fg=WARN if shown < total else FG_DIM)
        else:
            if not scanned: lbl.config(text="—", fg=FG_DIM)
            elif shown == 0:
                lbl.config(text=self._t("no_violations").format(total), fg=OK_CLR)
                tree.insert("", "end", values=("✓  " + self._t("no_violations").format(total), "", "", "", "", ""), tags=("ok_msg",))
            else:            lbl.config(text=self._t("violations").format(total, shown), fg=ERR_CLR)

    def _apply_styles(self):
        s = ttk.Style(); s.theme_use("clam")
        s.configure("TNotebook", background=BG, borderwidth=0)
        s.configure("TNotebook.Tab", background=BG3, foreground=FG_DIM, padding=[16,6], font=MONO_B)
        s.map("TNotebook.Tab", background=[("selected", PANEL)], foreground=[("selected", FG)])
        s.configure("Treeview", background=BG2, foreground=FG, fieldbackground=BG2, rowheight=24, font=MONO)
        s.configure("Treeview.Heading", background="#3A3A3F", foreground=FG, font=MONO_B, relief="flat", padding=[6,5])
        s.map("Treeview", background=[("selected","#1E5799")], foreground=[("selected","#FFFFFF")])
        s.configure("Vertical.TScrollbar",   background=BG3, troughcolor=BG2, width=10)
        s.configure("Horizontal.TScrollbar", background=BG3, troughcolor=BG2, width=10)
        s.configure("TCombobox", fieldbackground=BG3, background=PANEL, foreground=FG,
                    selectbackground=BG3, selectforeground=FG, insertcolor=FG)
        s.map("TCombobox",
              fieldbackground=[("readonly", BG3), ("readonly !focus", BG3)],
              foreground=[("readonly", FG), ("readonly !focus", FG)],
              selectbackground=[("readonly", BG3), ("readonly !focus", BG3)],
              selectforeground=[("readonly", FG), ("readonly !focus", FG)])

    def _build_ui(self):
        top = tk.Frame(self.root, bg="#141414", height=38)
        top.pack(fill="x"); top.pack_propagate(False)
        self._status_dot = tk.Label(top, text="●", bg="#141414", fg=FG_DIM, font=("Consolas",11))
        self._status_dot.pack(side="left", padx=(14,2), pady=10)
        self._status_lbl = tk.Label(top, text="초기화 중...", bg="#141414", fg=FG_DIM, font=("Consolas",9), anchor="w")
        self._status_lbl.pack(side="left", pady=10, fill="x", expand=True)
        btn_reconnect = tk.Button(top, text=self._t("reconnect"),
            command=lambda: threading.Thread(target=self._connect_waapi, daemon=True).start(),
            bg="#2A2A2E", fg=FG, relief="flat", font=("Consolas",9), padx=12, cursor="hand2",
            activebackground=PANEL, activeforeground=FG)
        btn_reconnect.pack(side="right", padx=(4,10), pady=7)
        self._lang_updaters.append(lambda w=btn_reconnect: w.config(text=self._t("reconnect")))
        self._lang_btn = tk.Button(top, text=self._t("lang_toggle"), command=self._toggle_lang,
            bg="#303040", fg=ACCENT, relief="flat", font=("Consolas",9,"bold"), padx=10, cursor="hand2",
            activebackground="#404060", activeforeground=ACCENT)
        self._lang_btn.pack(side="right", padx=(0,2), pady=7)
        self._lang_updaters.append(lambda: self._lang_btn.config(text=self._t("lang_toggle")))
        tk.Frame(self.root, bg=ACCENT, height=2).pack(fill="x")
        nb = ttk.Notebook(self.root); nb.pack(fill="both", expand=True); self._nb = nb
        tab1 = tk.Frame(nb, bg=BG); nb.add(tab1, text=self._t("tab1")); self._build_tab(tab1, "name")
        self._lang_updaters.append(lambda: self._nb.tab(0, text=self._t("tab1")))
        tab2 = tk.Frame(nb, bg=BG); nb.add(tab2, text=self._t("tab2")); self._build_tab(tab2, "workunit")
        self._lang_updaters.append(lambda: self._nb.tab(1, text=self._t("tab2")))

    def _build_tab(self, parent, mode):
        is_name  = (mode == "name")
        rule_key = "name_rules" if is_name else "workunit_rules"
        reg = self._lang_updaters

        rule_outer = tk.Frame(parent, bg=ACCENT); rule_outer.pack(fill="x", padx=10, pady=(10,0))
        rule_frame = tk.Frame(rule_outer, bg=BG3); rule_frame.pack(fill="both", padx=2, pady=(0,2))
        title_bar = tk.Frame(rule_frame, bg=BG3); title_bar.pack(fill="x", padx=10, pady=(8,0))

        lbl_rule_title = tk.Label(title_bar, text=self._t("rule_title"), bg=BG3, fg=FG, font=MONO_LG)
        lbl_rule_title.pack(side="left")
        reg.append(lambda w=lbl_rule_title: w.config(text=self._t("rule_title")))

        desc_key = "desc_name" if is_name else "desc_wu"
        desc_lbl = tk.Label(title_bar, text=self._t(desc_key), bg=BG3, fg=FG_DIM, font=MONO)
        desc_lbl.pack(side="left", padx=12)
        reg.append(lambda w=desc_lbl, k=desc_key: w.config(text=self._t(k)))

        tip_key = "tip_name" if is_name else "tip_wu"
        help_btn = tk.Label(title_bar, text=" ？ ", bg=PANEL, fg=ACCENT, font=MONO_B, cursor="question_arrow", relief="flat")
        help_btn.pack(side="left", padx=(0,4))
        self._attach_tooltip(help_btn, lambda k=tip_key: self._t(k))

        hdr = tk.Frame(rule_frame, bg=BG3); hdr.pack(fill="x", padx=10, pady=(6,2))
        kw_key = "kw_name" if is_name else "kw_wu"
        lbl_kw = tk.Label(hdr, text=self._t(kw_key), bg=BG3, fg=FG_DIM, font=MONO, width=26, anchor="w")
        lbl_kw.grid(row=0, column=0, padx=4)
        reg.append(lambda w=lbl_kw, k=kw_key: w.config(text=self._t(k)))
        if not is_name:
            kw_tip_btn = tk.Label(hdr, text=" ？ ", bg=PANEL, fg=ACCENT, font=MONO_B, cursor="question_arrow", relief="flat")
            kw_tip_btn.grid(row=0, column=1, padx=(0,4))
            self._attach_tooltip(kw_tip_btn, lambda: self._t("tip_kw_wu"))
        lbl_bus_kw = tk.Label(hdr, text=self._t("bus_kw_hdr"), bg=BG3, fg=FG_DIM, font=MONO, width=22, anchor="w")
        lbl_bus_kw.grid(row=0, column=2, padx=4)
        reg.append(lambda w=lbl_bus_kw: w.config(text=self._t("bus_kw_hdr")))
        lbl_case = tk.Label(hdr, text=self._t("case_hdr"), bg=BG3, fg=FG_DIM, font=MONO, width=8, anchor="w")
        lbl_case.grid(row=0, column=3, padx=4)
        reg.append(lambda w=lbl_case: w.config(text=self._t("case_hdr")))

        rows_frame = tk.Frame(rule_frame, bg=BG3); rows_frame.pack(fill="x", padx=10, pady=2)
        rule_rows = []

        def add_row(kw="", bus="", cs=False, extra_src=None, extra_buses=None):
            row_frame = tk.Frame(rows_frame, bg=BG3); row_frame.pack(fill="x", pady=1)
            kw_var  = tk.StringVar(value=kw); bus_var = tk.StringVar(value=bus); cs_var = tk.BooleanVar(value=cs)
            src_extra_list = []; bus_extra_list = []

            # Single grid for BOTH main row and all OR extra rows so columns auto-align.
            # Column layout:
            #  0: "or" label (src side, empty placeholder in main row)
            #  1: source entry
            #  2: source action btn (green+ in main, − in extras)
            #  3: → / spacer
            #  4: "or" label (bus side, empty placeholder in main row)
            #  5: bus entry
            #  6: bus action btn (blue+ in main, − in extras)
            #  7: checkbox (main row only)
            #  8: × button (main row only)
            g = tk.Frame(row_frame, bg=BG3); g.pack(fill="x")

            def _entry(parent, var, w):
                return tk.Entry(parent, textvariable=var, bg=BG2, fg=FG, insertbackground=FG,
                    width=w, font=MONO, relief="flat", highlightthickness=1,
                    highlightbackground=PANEL, highlightcolor=ACCENT)

            # Main row (grid row 0) — col0/col4 placeholders keep column widths consistent
            tk.Label(g, bg=BG3, width=3).grid(row=0, column=0)
            _entry(g, kw_var, 16).grid(row=0, column=1, padx=(0,2), pady=1)
            tk.Button(g, text="+", bg=BG3, fg=OK_CLR, relief="flat",
                font=("Consolas",10,"bold"), cursor="hand2", activebackground=PANEL,
                width=2, command=lambda: add_src_extra()).grid(row=0, column=2, padx=2)
            tk.Label(g, text="→", bg=BG3, fg=FG_DIM, font=MONO).grid(row=0, column=3, padx=(20,20))
            tk.Label(g, bg=BG3, width=3).grid(row=0, column=4)
            _entry(g, bus_var, 16).grid(row=0, column=5, padx=(0,2), pady=1)
            tk.Button(g, text="+", bg=BG3, fg=ACCENT, relief="flat",
                font=("Consolas",10,"bold"), cursor="hand2", activebackground=PANEL,
                width=2, command=lambda: add_bus_extra()).grid(row=0, column=6, padx=2)
            tk.Checkbutton(g, variable=cs_var, bg=BG3, selectcolor=BG2,
                activebackground=BG3).grid(row=0, column=7, padx=8)
            def remove():
                rule_rows.remove((kw_var, bus_var, cs_var, src_extra_list, bus_extra_list, row_frame))
                row_frame.destroy()
            tk.Button(g, text="✕", command=remove, bg=BG3, fg=ERR_CLR, relief="flat",
                font=("Consolas",10), cursor="hand2", activebackground=PANEL).grid(row=0, column=8)

            # extra_slots: grid_row -> {'src': bool, 'bus': bool}
            extra_slots = {}

            def _alloc_src_slot():
                for r in sorted(extra_slots):
                    if not extra_slots[r]['src']: return r
                r = (max(extra_slots, default=0) + 1); extra_slots[r] = {'src': False, 'bus': False}; return r

            def _alloc_bus_slot():
                for r in sorted(extra_slots):
                    if not extra_slots[r]['bus']: return r
                r = (max(extra_slots, default=0) + 1); extra_slots[r] = {'src': False, 'bus': False}; return r

            def add_src_extra(val=""):
                r = _alloc_src_slot(); extra_slots[r]['src'] = True
                evar = tk.StringVar(value=val)
                lbl = tk.Label(g, text="or", bg=BG3, fg=OK_CLR, font=MONO_B, width=3)
                lbl.grid(row=r, column=0, sticky="e")
                e = _entry(g, evar, 16); e.grid(row=r, column=1, padx=(0,2), pady=1)
                def rm():
                    lbl.destroy(); e.destroy(); rm_btn.destroy()
                    extra_slots[r]['src'] = False
                    src_extra_list[:] = [(v,x) for v,x in src_extra_list if v is not evar]
                rm_btn = tk.Button(g, text="−", command=rm, bg=BG3, fg=FG_DIM, relief="flat",
                    font=("Consolas",10), cursor="hand2", activebackground=PANEL)
                rm_btn.grid(row=r, column=2, padx=2, pady=1)
                src_extra_list.append((evar, None))

            def add_bus_extra(val=""):
                r = _alloc_bus_slot(); extra_slots[r]['bus'] = True
                evar = tk.StringVar(value=val)
                lbl = tk.Label(g, text="or", bg=BG3, fg=ACCENT, font=MONO_B, width=3)
                lbl.grid(row=r, column=4, sticky="e")
                e = _entry(g, evar, 16); e.grid(row=r, column=5, padx=(0,2), pady=1)
                def rm():
                    lbl.destroy(); e.destroy(); rm_btn.destroy()
                    extra_slots[r]['bus'] = False
                    bus_extra_list[:] = [(v,x) for v,x in bus_extra_list if v is not evar]
                rm_btn = tk.Button(g, text="−", command=rm, bg=BG3, fg=FG_DIM, relief="flat",
                    font=("Consolas",10), cursor="hand2", activebackground=PANEL)
                rm_btn.grid(row=r, column=6, padx=2, pady=1)
                bus_extra_list.append((evar, None))

            rule_rows.append((kw_var, bus_var, cs_var, src_extra_list, bus_extra_list, row_frame))
            for es in (extra_src   or []): add_src_extra(es)
            for eb in (extra_buses or []): add_bus_extra(eb)

        for rule in self.config.get(rule_key, []):
            extra_src   = rule.get("extra_keywords", []) if is_name else rule.get("extra_work_unit_keywords", [])
            extra_buses = rule.get("extra_bus_keywords", [])
            if is_name: add_row(rule.get("keyword",""), rule.get("expected_bus_keyword",""), rule.get("case_sensitive",False), extra_src, extra_buses)
            else:       add_row(rule.get("work_unit_keyword",""), rule.get("expected_bus_keyword",""), rule.get("case_sensitive",False), extra_src, extra_buses)

        btn_row = tk.Frame(rule_frame, bg=BG3); btn_row.pack(fill="x", padx=10, pady=(4,10))
        flag_var = tk.BooleanVar(value=self.config.get("flag_unset_bus", True))
        def on_flag(): self.config["flag_unset_bus"] = flag_var.get()
        cb_flag = tk.Checkbutton(btn_row, text=self._t("flag_unset"), variable=flag_var, command=on_flag,
            bg=BG3, fg=FG_DIM, font=MONO, selectcolor=BG2, activebackground=BG3)
        cb_flag.pack(side="left")
        reg.append(lambda w=cb_flag: w.config(text=self._t("flag_unset")))
        lbl_flag_note = tk.Label(btn_row, text=self._t("flag_unset_note"), bg=BG3, fg=FG_DIM, font=MONO)
        lbl_flag_note.pack(side="left", padx=(2, 0))
        reg.append(lambda w=lbl_flag_note: w.config(text=self._t("flag_unset_note")))

        def save_rules():
            rules = []
            for kw_v, bus_v, cs_v, src_el, bus_el, _ in rule_rows:
                kw, bus = kw_v.get().strip(), bus_v.get().strip()
                if kw and bus:
                    rule = {"expected_bus_keyword": bus, "case_sensitive": cs_v.get()}
                    src_extras = [ev.get().strip() for ev, _ in src_el if ev.get().strip()]
                    bus_extras = [ev.get().strip() for ev, _ in bus_el if ev.get().strip()]
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

        btn_save = tk.Button(btn_row, text=self._t("save_rules"), command=save_rules,
            bg=ACCENT, fg="#FFFFFF", relief="flat", font=MONO_B, padx=12, cursor="hand2")
        btn_save.pack(side="right")
        reg.append(lambda w=btn_save: w.config(text=self._t("save_rules")))
        lbl_reminder = tk.Label(btn_row, text=self._t("save_reminder"), bg=BG3, fg=WARN, font=MONO)
        lbl_reminder.pack(side="right", padx=(0, 10))
        reg.append(lambda w=lbl_reminder: w.config(text=self._t("save_reminder")))
        btn_add = tk.Button(btn_row, text=self._t("add_rule"), command=lambda: add_row(),
            bg=PANEL, fg=FG, relief="flat", font=MONO, padx=10, cursor="hand2")
        btn_add.pack(side="right", padx=(6,0))
        reg.append(lambda w=btn_add: w.config(text=self._t("add_rule")))

        filter_bar = tk.Frame(parent, bg="#1A1A1E", relief="flat")
        filter_bar.pack(fill="x", padx=10, pady=(5,0))
        tk.Frame(filter_bar, bg="#4A9EFF", width=3).pack(side="left", fill="y", padx=(0,8))
        lbl_search = tk.Label(filter_bar, text=self._t("search_lbl"), bg="#1A1A1E", fg=ACCENT,
            font=MONO_B, width=4, anchor="w")
        lbl_search.pack(side="left", padx=(0,4))
        reg.append(lambda w=lbl_search: w.config(text=self._t("search_lbl")))

        field_idx_var = tk.IntVar(value=0)
        field_combo = ttk.Combobox(filter_bar, values=[self._t(k) for k in SEARCH_FIELD_SKEYS],
            state="readonly", font=MONO, width=16)
        field_combo.current(0); field_combo.pack(side="left", padx=(0,4), pady=6)
        field_combo.bind("<<ComboboxSelected>>",
            lambda e, v=field_idx_var, c=field_combo, m=mode: (v.set(c.current()), self._apply_filter(m)))

        def _refresh_field_combo(c=field_combo, v=field_idx_var):
            c.config(values=[self._t(k) for k in SEARCH_FIELD_SKEYS]); c.current(v.get())
        reg.append(_refresh_field_combo)

        if is_name: self._search_field_idx_name = field_idx_var
        else:       self._search_field_idx_wu   = field_idx_var

        search_var = tk.StringVar()
        search_entry = tk.Entry(filter_bar, textvariable=search_var, bg=BG3, fg=FG,
            insertbackground=FG, font=MONO, relief="flat",
            highlightthickness=1, highlightbackground="#4A4A50", highlightcolor=ACCENT, width=32)
        search_entry.pack(side="left", padx=(0,3), pady=6, ipady=4)
        tk.Button(filter_bar, text="×", command=lambda: search_var.set(""),
            bg="#2A2A30", fg=FG_DIM, relief="flat", font=("Consolas",11,"bold"),
            cursor="hand2", activebackground=PANEL, activeforeground=ERR_CLR).pack(side="left", padx=(0,8))
        lbl_hint = tk.Label(filter_bar, text=self._t("search_hint"), bg="#1A1A1E", fg="#606070", font=MONO)
        lbl_hint.pack(side="left")
        reg.append(lambda w=lbl_hint: w.config(text=self._t("search_hint")))

        if is_name:
            self._search_var_name = search_var
            search_var.trace_add("write", lambda *_: self._apply_filter("name"))
        else:
            self._search_var_wu = search_var
            search_var.trace_add("write", lambda *_: self._apply_filter("workunit"))
            tk.Frame(filter_bar, bg="#404048", width=1).pack(side="left", fill="y", padx=(10,8), pady=5)
            self._wu_show_inherited = tk.BooleanVar(value=True)
            self._wu_show_override  = tk.BooleanVar(value=True)
            def _wu_toggle(*_): self._apply_filter("workunit")
            cb_inh = tk.Checkbutton(filter_bar, text=self._t("inherited"), variable=self._wu_show_inherited,
                command=_wu_toggle, bg="#1A1A1E", fg=WARN, font=MONO_B, selectcolor="#2A2A20",
                activebackground="#1A1A1E", activeforeground=WARN)
            cb_inh.pack(side="left", padx=(0,4))
            reg.append(lambda w=cb_inh: w.config(text=self._t("inherited")))
            cb_ovr = tk.Checkbutton(filter_bar, text=self._t("overridden"), variable=self._wu_show_override,
                command=_wu_toggle, bg="#1A1A1E", fg=ERR_CLR, font=MONO_B, selectcolor="#2A1A1A",
                activebackground="#1A1A1E", activeforeground=ERR_CLR)
            cb_ovr.pack(side="left", padx=4)
            reg.append(lambda w=cb_ovr: w.config(text=self._t("overridden")))

        cols     = ("name",      "work_unit",     "current_bus",  "trigger",     "expected_kw", "path")
        col_keys = ("col_name",  "col_work_unit", "col_cur_bus",  "col_trigger", "col_exp_kw",  "col_path")
        col_wids = (200,          130,             170,            240,           130,            1200)

        tbl = tk.Frame(parent, bg="#404048", bd=0); tbl.pack(fill="both", expand=True, padx=10, pady=(4,0))
        vsb = ttk.Scrollbar(tbl, orient="vertical");   vsb.pack(side="right", fill="y")
        hsb = ttk.Scrollbar(tbl, orient="horizontal"); hsb.pack(side="bottom", fill="x")
        tree = ttk.Treeview(tbl, columns=cols, show="headings",
            yscrollcommand=vsb.set, xscrollcommand=hsb.set, selectmode="extended")
        tree.pack(fill="both", expand=True)
        vsb.config(command=tree.yview); hsb.config(command=tree.xview)

        for col, key, w in zip(cols, col_keys, col_wids):
            tree.heading(col, text=self._t(key), command=lambda c=col, t=tree: self._sort(t, c))
            tree.column(col, width=w, minwidth=60, stretch=False)
            reg.append(lambda t=tree, c=col, k=key: t.heading(c, text=self._t(k)))
        tree.tag_configure("violation", foreground=ERR_CLR)
        tree.tag_configure("unset",     foreground=WARN)
        tree.tag_configure("ok_msg",    foreground=OK_CLR)
        tree.bind("<Double-1>", lambda e, t=tree, m=is_name: self._on_dbl(e, t, m))
        if is_name: self.tree_name = tree
        else:       self.tree_wu   = tree

        bar = tk.Frame(parent, bg="#141414", height=44); bar.pack(fill="x", padx=10, pady=(2,8))
        bar.pack_propagate(False)
        def _btn(par, text, cmd, bg=PANEL, fg=FG, bold=False):
            return tk.Button(par, text=text, command=cmd, bg=bg, fg=fg, relief="flat",
                font=MONO_B if bold else MONO, padx=12, cursor="hand2",
                activebackground="#444448", activeforeground=FG)

        scan_btn = _btn(bar, self._t("scan"), lambda: self._run_scan(mode), bg=ACCENT, fg="#FFFFFF", bold=True)
        scan_btn.pack(side="left", padx=(0,2), pady=6)
        reg.append(lambda w=scan_btn: w.config(text=self._t("scan")))
        tk.Frame(bar, bg="#404048", width=1).pack(side="left", fill="y", padx=8, pady=8)

        btn_view = _btn(bar, self._t("view_wwise"), lambda t=tree, m=is_name: self._action_select(t, m))
        btn_view.pack(side="left", padx=2, pady=6)
        reg.append(lambda w=btn_view: w.config(text=self._t("view_wwise")))

        btn_fix = _btn(bar, self._t("reroute"), lambda t=tree, m=is_name: self._action_fix(t, m),
                       bg="#6B0F1A", fg="#FFAAAA", bold=True)
        btn_fix.pack(side="left", padx=2, pady=6)
        reg.append(lambda w=btn_fix: w.config(text=self._t("reroute")))

        btn_sel = _btn(bar, self._t("select_all"), lambda t=tree: t.selection_set(t.get_children()))
        btn_sel.pack(side="left", padx=2, pady=6)
        reg.append(lambda w=btn_sel: w.config(text=self._t("select_all")))

        tk.Frame(bar, bg="#404048", width=1).pack(side="right", fill="y", padx=8, pady=8)
        btn_csv = _btn(bar, self._t("export_csv"), lambda m=is_name: self._export_csv(m))
        btn_csv.pack(side="right", padx=2, pady=6)
        reg.append(lambda w=btn_csv: w.config(text=self._t("export_csv")))
        tk.Label(bar, text=VERSION, bg="#141414", fg="#505060", font=MONO).pack(side="right", padx=(0,4))

        count_lbl = tk.Label(bar, text="—", bg="#141414", fg=FG_DIM, font=MONO)
        count_lbl.pack(side="right", padx=10)
        if is_name: self.btn_scan_name = scan_btn;  self.lbl_count_name = count_lbl
        else:       self.btn_scan_wu   = scan_btn;  self.lbl_count_wu   = count_lbl

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

    def _show_fix_dialog(self, violations, is_name):
        dlg = tk.Toplevel(self.root); dlg.title(self._t("reroute_title"))
        dlg.geometry("560x360"); dlg.configure(bg=BG); dlg.grab_set()
        tk.Label(dlg, text=self._t("reroute_fmt").format(len(violations)), bg=BG, fg=FG, font=MONO_LG).pack(pady=(16,4), padx=16, anchor="w")
        tk.Label(dlg, text=self._t("reroute_bus_sel"), bg=BG, fg=FG_DIM, font=MONO).pack(pady=(0,8), padx=16, anchor="w")
        by_kw = {}
        for v in violations: by_kw.setdefault(v["expected_bus_keyword"], []).append(v)
        bus_names = sorted(self.buses.keys()); kw_bus_vars = {}
        grid = tk.Frame(dlg, bg=BG); grid.pack(fill="x", padx=16, pady=4)
        for i, (kw, items) in enumerate(by_kw.items()):
            tk.Label(grid, text=f'"{kw}"  ({len(items)})', bg=BG, fg=FG_DIM, font=MONO, width=26, anchor="w",
                ).grid(row=i, column=0, padx=(0,8), pady=3, sticky="w")
            default = next((b for b in bus_names if kw.upper() in b.upper()), "")
            var = tk.StringVar(value=default); kw_bus_vars[kw] = var
            ttk.Combobox(grid, textvariable=var, values=bus_names, width=30, font=MONO).grid(row=i, column=1, pady=3, sticky="w")

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
                    self._t("reroute_partial").format(fixed, len(errors), "\n".join(errors)), parent=self.root)
            else:
                messagebox.showinfo(self._t("complete_title"), self._t("reroute_done").format(fixed), parent=self.root)
            self._run_scan("name" if is_name else "workunit")

        bbar = tk.Frame(dlg, bg=BG); bbar.pack(side="bottom", pady=16)
        tk.Button(bbar, text=self._t("cancel"), command=dlg.destroy,
            bg=PANEL, fg=FG, relief="flat", font=MONO, padx=14).pack(side="left", padx=8)
        tk.Button(bbar, text=self._t("apply_reroute"), command=do_fix,
            bg=DANGER, fg="#FFFFFF", relief="flat", font=MONO_B, padx=14, cursor="hand2").pack(side="left", padx=8)

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

    @staticmethod
    def _attach_tooltip(widget, text_fn):
        tip = [None]
        def _show(e):
            if tip[0]: return
            text = text_fn() if callable(text_fn) else text_fn
            x = widget.winfo_rootx() + 20; y = widget.winfo_rooty() + widget.winfo_height() + 6
            w = tk.Toplevel(widget); w.wm_overrideredirect(True); w.wm_geometry(f"+{x}+{y}")
            tk.Label(w, text=text, bg="#2D2D30", fg="#DCDCDC", font=("Consolas",9),
                relief="solid", bd=1, wraplength=440, justify="left", padx=10, pady=7).pack()
            tip[0] = w
        def _hide(e):
            if tip[0]: tip[0].destroy(); tip[0] = None
        widget.bind("<Enter>", _show, add="+"); widget.bind("<Leave>", _hide, add="+")

    def _set_status(self, msg, color=FG_DIM):
        def _update():
            self._status_lbl.config(text=msg, fg=color)
            self._status_dot.config(fg=color)
        self.root.after(0, _update)


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
