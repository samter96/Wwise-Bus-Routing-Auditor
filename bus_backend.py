#!/usr/bin/env python3
"""Tauri UI용 persistent JSON-lines WAAPI sidecar for Bus Routing Auditor."""

import csv
import json
import os
import queue
import re
import sys
import threading
from pathlib import Path

try:
    from waapi import WaapiClient
except ImportError:
    WaapiClient = None

VERSION = "V.2.0.0"
WAAPI_URL = "ws://127.0.0.1:8080/waapi"
CONFIG_FILE = "bus_routing_rules.json"
FIND_CMD_PRIMARY = [
    "FindInProjectExplorerSelectionChannel1",
    "FindInProjectExplorer",
    "FindInProjectExplorer1",
]
HIERARCHY_TYPES = [
    "Sound",
    "ActorMixer",
    "BlendContainer",
    "RandomSequenceContainer",
    "SwitchContainer",
    "WorkUnit",
    "Folder",
]
REQUEST_TIMEOUTS = {
    "connect": 25,
    "scope_children": 25,
    "scan": 60,
    "reroute": 45,
    "select_in_wwise": 20,
    "export_csv": 20,
}
CHUNK_SIZE = 500
SCOPE_TYPES = {
    "WorkUnit",
    "PhysicalFolder",
    "Folder",
    "ActorMixer",
    "BlendContainer",
    "RandomSequenceContainer",
    "SwitchContainer",
}
DEFAULT_CONFIG = {
    "name_rules": [
        {"keyword": "UI", "expected_bus_keyword": "UI", "case_sensitive": False},
        {"keyword": "Music", "expected_bus_keyword": "Music", "case_sensitive": False},
        {"keyword": "AMB", "expected_bus_keyword": "AMB", "case_sensitive": False},
        {"keyword": "VO", "expected_bus_keyword": "VO", "case_sensitive": False},
    ],
    "workunit_rules": [
        {"work_unit_keyword": "UI", "expected_bus_keyword": "UI", "case_sensitive": False},
        {"work_unit_keyword": "Music", "expected_bus_keyword": "Music", "case_sensitive": False},
        {"work_unit_keyword": "AMB", "expected_bus_keyword": "AMB", "case_sensitive": False},
        {"work_unit_keyword": "VO", "expected_bus_keyword": "VO", "case_sensitive": False},
    ],
    "flag_unset_bus": True,
}


def configure_stdio():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def _config_path():
    cwd_path = Path.cwd() / CONFIG_FILE
    if cwd_path.exists() or os.access(Path.cwd(), os.W_OK):
        return cwd_path
    return Path(__file__).resolve().parent / CONFIG_FILE


def effective_type(obj):
    obj_type = obj.get("type", "")
    if obj_type == "WorkUnit":
        file_path = str(obj.get("filePath") or "")
        if file_path and not file_path.lower().endswith(".wwu"):
            return "PhysicalFolder"
    return obj_type


def word_match(text, keyword, case_sensitive):
    if not keyword:
        return False
    flags = 0 if case_sensitive else re.IGNORECASE
    sep = r"[ _\-\./\\()\[\]{},;:\s]"
    pattern = r"(?:^|" + sep + r")" + re.escape(keyword) + r"(?:$|" + sep + r")"
    return bool(re.search(pattern, text or "", flags))


class BusRoutingBackend:
    RETURN_FIELDS = ["id", "name", "path", "type", "@OutputBus", "@OverrideOutput", "workunit"]

    def __init__(self):
        self.client = None
        self.project_name = ""
        self.find_command = None
        self.config_path = _config_path()
        self.config = self._load_config()
        self.buses = {}
        self.results = []
        self.total_checked = 0

    def _load_config(self):
        try:
            if self.config_path.exists():
                data = json.loads(self.config_path.read_text(encoding="utf-8"))
                return {**DEFAULT_CONFIG, **data}
        except Exception:
            pass
        return json.loads(json.dumps(DEFAULT_CONFIG))

    def _save_config(self):
        self.config_path.write_text(
            json.dumps(self.config, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _require_client(self):
        if self.client is None:
            raise RuntimeError("Wwise에 연결되지 않았습니다.")
        return self.client

    def ping(self, _payload):
        return {"version": VERSION, "backend": "python", "ready": True}

    def get_config(self, _payload=None):
        self.config = self._load_config()
        return {"config": self.config}

    def save_config(self, payload):
        incoming = payload.get("config") or {}
        self.config = {
            "name_rules": incoming.get("name_rules") or [],
            "workunit_rules": incoming.get("workunit_rules") or [],
            "flag_unset_bus": bool(incoming.get("flag_unset_bus", True)),
        }
        self._save_config()
        return {"config": self.config}

    def connect(self, _payload=None):
        if WaapiClient is None:
            raise RuntimeError("waapi-client가 설치되지 않았습니다. install.bat을 실행하세요.")
        if self.client:
            try:
                self.client.disconnect()
            except Exception:
                pass
        self.client = WaapiClient(url=WAAPI_URL)
        self.find_command = None
        self._fetch_buses()
        response = self.client.call(
            "ak.wwise.core.object.get",
            {"from": {"ofType": ["Project"]}, "options": {"return": ["name"]}},
        )
        projects = (response or {}).get("return", [])
        self.project_name = projects[0].get("name", "—") if projects else "—"
        return {
            "connected": True,
            "projectName": self.project_name,
            "buses": sorted(self.buses.keys(), key=str.lower),
        }

    def _fetch_buses(self):
        client = self._require_client()
        response = client.call(
            "ak.wwise.core.object.get",
            {"from": {"ofType": ["Bus", "AuxBus"]}, "options": {"return": ["id", "name", "path"]}},
        )
        self.buses = {obj.get("name", ""): obj.get("id", "") for obj in (response or {}).get("return", []) if obj.get("name")}

    def scope_children(self, payload):
        client = self._require_client()
        path = payload.get("path") or "\\Actor-Mixer Hierarchy"
        response = client.call(
            "ak.wwise.core.object.get",
            {
                "from": {"path": [path]},
                "transform": [{"select": ["children"]}],
                "options": {"return": ["id", "name", "path", "type", "filePath"]},
            },
        )
        children = []
        for obj in (response or {}).get("return", []):
            obj_type = effective_type(obj)
            if obj_type not in SCOPE_TYPES:
                continue
            children.append(
                {
                    "id": obj.get("id", ""),
                    "name": obj.get("name", ""),
                    "path": obj.get("path", ""),
                    "type": obj_type,
                    "expandable": True,
                }
            )
        return {"path": path, "children": children}

    def _get_all_sounds(self):
        client = self._require_client()
        response = client.call(
            "ak.wwise.core.object.get",
            {
                "from": {"ofType": ["Sound"]},
                "options": {"return": self.RETURN_FIELDS},
            },
        )
        sounds_raw = (response or {}).get("return", [])
        all_objects_by_path = {obj.get("path", ""): obj for obj in sounds_raw if obj.get("path")}

        ancestor_paths = set()
        for sound in sounds_raw:
            cur = sound.get("path", "")
            while True:
                sep = cur.rfind("\\")
                if sep <= 0:
                    break
                cur = cur[:sep]
                ancestor_paths.add(cur)

        ancestor_list = sorted(ancestor_paths)
        for offset in range(0, len(ancestor_list), CHUNK_SIZE):
            chunk = ancestor_list[offset:offset + CHUNK_SIZE]
            if not chunk:
                continue
            response = client.call(
                "ak.wwise.core.object.get",
                {
                    "from": {"path": chunk},
                    "options": {"return": self.RETURN_FIELDS},
                },
            )
            for obj in (response or {}).get("return", []):
                path = obj.get("path", "")
                if path:
                    all_objects_by_path[path] = obj

        all_objects = list(all_objects_by_path.values())
        effective = self._resolve_effective_buses(all_objects)
        default_key = "masteraudiobus"
        sounds = []
        for obj in sounds_raw:
            if obj.get("type") != "Sound":
                continue
            path = obj.get("path", "")
            eff = effective.get(path) or {"name": "Master Audio Bus", "id": ""}
            if eff.get("name", "").replace(" ", "").lower() == default_key:
                own = obj.get("@OutputBus") or {}
                own_name = own.get("name", "")
                if own_name and own_name.replace(" ", "").lower() != default_key:
                    eff = own
            obj["_effective_bus_name"] = eff.get("name", "")
            obj["_effective_bus_id"] = eff.get("id", "")
            obj["_bus_inherited"] = not obj.get("@OverrideOutput", False)
            sounds.append(obj)
        return sounds

    def _resolve_effective_buses(self, all_objects):
        default_key = "masteraudiobus"
        overrides = {}
        stale = {}
        for obj in all_objects:
            bus = obj.get("@OutputBus") or {}
            bus_name = bus.get("name", "")
            if not bus_name:
                continue
            path = obj.get("path", "")
            if obj.get("@OverrideOutput", False):
                overrides[path] = bus
            elif bus_name.replace(" ", "").lower() != default_key and obj.get("type") != "Sound":
                stale[path] = bus

        override_cache = {}

        def find_override(path):
            chain = []
            cur = path
            while True:
                if cur in overrides:
                    val = overrides[cur]
                    override_cache[cur] = val
                    for p in chain:
                        override_cache[p] = val
                    return val
                if cur in override_cache:
                    val = override_cache[cur]
                    for p in chain:
                        override_cache[p] = val
                    return val
                chain.append(cur)
                sep = cur.rfind("\\")
                if sep <= 0:
                    break
                cur = cur[:sep]
            for p in chain:
                override_cache[p] = {}
            return {}

        def find_stale_highest(path):
            cur = path
            last_val = {}
            while True:
                if cur in stale:
                    last_val = stale[cur]
                sep = cur.rfind("\\")
                if sep <= 0:
                    break
                cur = cur[:sep]
            return last_val

        final = {}
        for obj in all_objects:
            path = obj.get("path", "")
            bus = find_override(path)
            if not bus:
                bus = find_stale_highest(path)
            final[path] = bus
        return final

    @staticmethod
    def _bus_display(bus_name, inherited):
        return (bus_name + "  ↑") if (bus_name and inherited) else bus_name

    def _matches_scope(self, path, scope_paths):
        if not scope_paths:
            return True
        return any(path == scope or path.startswith(scope + "\\") for scope in scope_paths)

    def _check_name_rules(self, sounds, scope_paths):
        rules = self.config.get("name_rules", [])
        flag_unset = self.config.get("flag_unset_bus", True)
        violations = []
        for sound in sounds:
            name = sound.get("name", "")
            path = sound.get("path", "")
            if not self._matches_scope(path, scope_paths):
                continue
            bus_name = sound.get("_effective_bus_name", "")
            bus_id = sound.get("_effective_bus_id", "")
            inherited = sound.get("_bus_inherited", False)
            wu_obj = sound.get("workunit") or {}
            wu_name = wu_obj.get("name", "")
            no_bus = not bus_name
            matching = []
            for rule in rules:
                case_sensitive = rule.get("case_sensitive", False)
                source_keywords = [rule.get("keyword", "")] + rule.get("extra_keywords", [])
                if any(word_match(name, keyword, case_sensitive) for keyword in source_keywords):
                    matching.append(rule)
            if not matching:
                continue
            failed = []
            for rule in matching:
                case_sensitive = rule.get("case_sensitive", False)
                bus_keywords = [rule.get("expected_bus_keyword", "")] + rule.get("extra_bus_keywords", [])
                mismatch = (not no_bus) and not any(word_match(bus_name, keyword, case_sensitive) for keyword in bus_keywords)
                if mismatch or (no_bus and flag_unset):
                    failed.append((rule, bus_keywords))
            if len(failed) < len(matching) or not failed:
                continue
            trigger_parts = [f'이름에 "{" | ".join([r.get("keyword", "")] + r.get("extra_keywords", []))}" 포함' for r, _ in failed]
            expected_parts = [" | ".join(keywords) for _, keywords in failed]
            violations.append(
                {
                    "id": sound.get("id", ""),
                    "name": name,
                    "path": path,
                    "work_unit": wu_name,
                    "current_bus": self._bus_display(bus_name, inherited),
                    "current_bus_id": bus_id,
                    "trigger": " or ".join(trigger_parts) if len(trigger_parts) > 1 else trigger_parts[0],
                    "expected_bus_keyword": " or ".join(expected_parts) if len(expected_parts) > 1 else expected_parts[0],
                    "unset": no_bus,
                    "inherited": inherited,
                    "scan_type": "name",
                }
            )
        return violations

    def _check_workunit_rules(self, sounds, scope_paths):
        rules = self.config.get("workunit_rules", [])
        flag_unset = self.config.get("flag_unset_bus", True)
        violations = []
        for sound in sounds:
            name = sound.get("name", "")
            path = sound.get("path", "")
            if not self._matches_scope(path, scope_paths):
                continue
            bus_name = sound.get("_effective_bus_name", "")
            bus_id = sound.get("_effective_bus_id", "")
            inherited = sound.get("_bus_inherited", False)
            wu_obj = sound.get("workunit") or {}
            wu_name = wu_obj.get("name", "")
            wu_path = wu_obj.get("path", "")
            search = f"{wu_name} {wu_path}"
            no_bus = not bus_name
            matching = []
            for rule in rules:
                case_sensitive = rule.get("case_sensitive", False)
                source_keywords = [rule.get("work_unit_keyword", "")] + rule.get("extra_work_unit_keywords", [])
                if any(word_match(search, keyword, case_sensitive) for keyword in source_keywords):
                    matching.append(rule)
            if not matching:
                continue
            failed = []
            for rule in matching:
                case_sensitive = rule.get("case_sensitive", False)
                bus_keywords = [rule.get("expected_bus_keyword", "")] + rule.get("extra_bus_keywords", [])
                mismatch = (not no_bus) and not any(word_match(bus_name, keyword, case_sensitive) for keyword in bus_keywords)
                if mismatch or (no_bus and flag_unset):
                    failed.append((rule, bus_keywords))
            if len(failed) < len(matching) or not failed:
                continue
            trigger_parts = [f'경로에 "{" | ".join([r.get("work_unit_keyword", "")] + r.get("extra_work_unit_keywords", []))}" 포함' for r, _ in failed]
            expected_parts = [" | ".join(keywords) for _, keywords in failed]
            violations.append(
                {
                    "id": sound.get("id", ""),
                    "name": name,
                    "path": path,
                    "work_unit": wu_name,
                    "current_bus": self._bus_display(bus_name, inherited),
                    "current_bus_id": bus_id,
                    "trigger": " or ".join(trigger_parts) if len(trigger_parts) > 1 else trigger_parts[0],
                    "expected_bus_keyword": " or ".join(expected_parts) if len(expected_parts) > 1 else expected_parts[0],
                    "unset": no_bus,
                    "inherited": inherited,
                    "scan_type": "workunit",
                }
            )
        return violations

    def scan(self, payload):
        mode = payload.get("mode") or "name"
        scope_paths = payload.get("scopePaths") or []
        sounds = self._get_all_sounds()
        scoped_sounds = [sound for sound in sounds if self._matches_scope(sound.get("path", ""), scope_paths)]
        if mode == "workunit":
            results = self._check_workunit_rules(sounds, scope_paths)
        else:
            mode = "name"
            results = self._check_name_rules(sounds, scope_paths)
        self.results = results
        self.total_checked = len(scoped_sounds)
        return {"mode": mode, "results": results, "totalChecked": self.total_checked}

    def select_in_wwise(self, payload):
        client = self._require_client()
        object_ids = payload.get("ids") or []
        if not object_ids:
            raise ValueError("선택된 오브젝트가 없습니다.")
        if self.find_command:
            try:
                client.call("ak.wwise.ui.commands.execute", {"command": self.find_command, "objects": object_ids})
            except Exception:
                self.find_command = None
        if not self.find_command:
            for command in FIND_CMD_PRIMARY:
                try:
                    client.call("ak.wwise.ui.commands.execute", {"command": command, "objects": object_ids})
                    self.find_command = command
                    break
                except Exception:
                    continue
            else:
                raise RuntimeError("Wwise에서 오브젝트를 선택할 수 없었습니다.")
        try:
            client.call("ak.wwise.ui.commands.execute", {"command": "Inspect", "objects": object_ids})
        except Exception:
            pass
        return {"selected": object_ids}

    def reroute(self, payload):
        client = self._require_client()
        object_ids = payload.get("ids") or []
        bus_name = payload.get("busName") or ""
        bus_id = self.buses.get(bus_name)
        if not object_ids:
            raise ValueError("선택된 오브젝트가 없습니다.")
        if not bus_id:
            raise ValueError(f'버스 "{bus_name}"를 찾을 수 없습니다.')
        errors = []
        fixed = 0
        for object_id in object_ids:
            try:
                client.call("ak.wwise.core.object.setReference", {"object": object_id, "reference": "OutputBus", "value": bus_id})
                fixed += 1
            except Exception as error:
                errors.append(f"{object_id}: {error}")
        if errors:
            raise RuntimeError(f"{fixed}개 완료 / {len(errors)}개 실패\n" + "\n".join(errors[:8]))
        return {"fixed": fixed}

    def export_csv(self, payload):
        raw_path = str(payload.get("path") or "").strip()
        if not raw_path:
            raise ValueError("저장 경로가 없습니다.")
        rows = payload.get("rows") or self.results
        path = Path(raw_path)
        fields = ["name", "work_unit", "current_bus", "trigger", "expected_bus_keyword", "path"]
        with path.open("w", newline="", encoding="utf-8-sig") as file:
            writer = csv.DictWriter(file, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        return {"path": str(path), "count": len(rows)}

    def dispatch(self, command, payload):
        handler = getattr(self, command, None)
        if handler is None or command.startswith("_"):
            raise ValueError(f"알 수 없는 명령: {command}")
        return handler(payload or {})


def dispatch_with_timeout(backend, command, payload):
    timeout = REQUEST_TIMEOUTS.get(command)
    if not timeout:
        return True, backend.dispatch(command, payload), False

    result_queue = queue.Queue(maxsize=1)

    def worker():
        try:
            result_queue.put((True, backend.dispatch(command, payload)))
        except Exception as error:
            result_queue.put((False, str(error)))

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    try:
        ok, value = result_queue.get(timeout=timeout)
    except queue.Empty:
        return False, f"{command} 응답 시간이 {timeout}초를 초과했습니다. Wwise WAAPI가 멈췄거나 프로젝트 조회가 너무 오래 걸립니다.", True
    if ok:
        return True, value, False
    return False, value, False


def run_protocol():
    configure_stdio()
    backend = BusRoutingBackend()
    for raw_line in sys.stdin:
        should_exit = False
        try:
            request = json.loads(raw_line)
            ok, value, should_exit = dispatch_with_timeout(
                backend,
                request.get("command", ""),
                request.get("payload"),
            )
            if not ok:
                raise RuntimeError(value)
            response = {
                "id": request.get("id"),
                "ok": True,
                "data": value,
            }
        except Exception as error:
            response = {
                "id": locals().get("request", {}).get("id"),
                "ok": False,
                "error": str(error),
            }
        sys.stdout.write(json.dumps(response, ensure_ascii=True) + "\n")
        sys.stdout.flush()
        if should_exit:
            os._exit(124)


if __name__ == "__main__":
    run_protocol()
