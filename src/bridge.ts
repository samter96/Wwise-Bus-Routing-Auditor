import { invoke } from "@tauri-apps/api/core";
import type { AuditResult, RuleConfig, ScopeNode } from "./types";

const isTauri = () => "__TAURI_INTERNALS__" in window;

const demoConfig: RuleConfig = {
  name_rules: [
    { keyword: "UI", expected_bus_keyword: "UI", case_sensitive: false },
    { keyword: "AMB", expected_bus_keyword: "AMB", case_sensitive: false },
  ],
  workunit_rules: [
    { work_unit_keyword: "Music", expected_bus_keyword: "Music", case_sensitive: false },
    { work_unit_keyword: "VO", expected_bus_keyword: "VO", case_sensitive: false },
  ],
  flag_unset_bus: true,
};

const demoResults: AuditResult[] = [
  {
    id: "demo-ui-click",
    name: "UI_Click_Confirm",
    work_unit: "UI",
    current_bus: "SFX_Main",
    current_bus_id: "bus-sfx",
    trigger: '이름에 "UI" 포함',
    expected_bus_keyword: "UI",
    path: "\\Actor-Mixer Hierarchy\\Default Work Unit\\UI\\UI_Click_Confirm",
    unset: false,
    inherited: false,
    scan_type: "name",
  },
  {
    id: "demo-amb-wind",
    name: "AMB_Wind_Loop",
    work_unit: "Ambience",
    current_bus: "Master Audio Bus  ↑",
    current_bus_id: "",
    trigger: '이름에 "AMB" 포함',
    expected_bus_keyword: "AMB",
    path: "\\Actor-Mixer Hierarchy\\Default Work Unit\\Ambience\\AMB_Wind_Loop",
    unset: true,
    inherited: true,
    scan_type: "name",
  },
];

const demoScope: ScopeNode[] = [
  { id: "wu-default", name: "Default Work Unit", path: "\\Actor-Mixer Hierarchy\\Default Work Unit", type: "WorkUnit", expandable: true },
  { id: "wu-ui", name: "UI", path: "\\Actor-Mixer Hierarchy\\Default Work Unit\\UI", type: "Folder", expandable: true },
  { id: "wu-amb", name: "Ambience", path: "\\Actor-Mixer Hierarchy\\Default Work Unit\\Ambience", type: "Folder", expandable: true },
];

let demoCurrentConfig = demoConfig;
let demoCurrentResults = [...demoResults];

async function demoRequest<T>(command: string, payload: Record<string, unknown>): Promise<T> {
  await new Promise((resolve) => setTimeout(resolve, command === "scan" ? 900 : 140));
  switch (command) {
    case "ping":
      return { version: "V.2.0.1", ready: true } as T;
    case "connect":
      return { connected: true, projectName: "DX_Wwise", buses: ["AMB_Main", "Music_Main", "SFX_Main", "UI_Main", "VO_Main"] } as T;
    case "get_config":
      return { config: demoCurrentConfig } as T;
    case "save_config":
      demoCurrentConfig = payload.config as RuleConfig;
      return { config: demoCurrentConfig } as T;
    case "scope_children":
      return { path: payload.path, children: demoScope } as T;
    case "scan":
      demoCurrentResults = demoResults.map((row) => ({ ...row, scan_type: payload.mode === "workunit" ? "workunit" : "name" }));
      return { mode: payload.mode ?? "name", results: demoCurrentResults, totalChecked: 284 } as T;
    case "select_in_wwise":
      return { selected: payload.ids } as T;
    case "reroute":
      demoCurrentResults = demoCurrentResults.filter((row) => !(payload.ids as string[]).includes(row.id));
      return { fixed: (payload.ids as string[])?.length ?? 0 } as T;
    case "export_csv":
      return { path: payload.path, count: demoCurrentResults.length } as T;
    default:
      throw new Error(`Unknown demo command: ${command}`);
  }
}

export async function backendRequest<T>(
  command: string,
  payload: Record<string, unknown> = {},
): Promise<T> {
  if (!isTauri()) return demoRequest<T>(command, payload);
  return invoke<T>("backend_request", { command, payload });
}

export { isTauri };
