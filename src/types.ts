export type Language = "ko" | "en";
export type ConnectionState = "connecting" | "connected" | "error";
export type AuditState = "idle" | "scanning" | "complete" | "error";
export type ScanMode = "name" | "workunit";

export interface Rule {
  keyword?: string;
  work_unit_keyword?: string;
  expected_bus_keyword: string;
  case_sensitive?: boolean;
  extra_keywords?: string[];
  extra_work_unit_keywords?: string[];
  extra_bus_keywords?: string[];
}

export interface RuleConfig {
  name_rules: Rule[];
  workunit_rules: Rule[];
  flag_unset_bus: boolean;
}

export interface AuditResult {
  id: string;
  name: string;
  work_unit: string;
  current_bus: string;
  current_bus_id: string;
  trigger: string;
  expected_bus_keyword: string;
  path: string;
  unset: boolean;
  inherited: boolean;
  scan_type: ScanMode;
}

export interface ScopeNode {
  id: string;
  name: string;
  path: string;
  type: string;
  expandable: boolean;
  loaded?: boolean;
  loading?: boolean;
  expanded?: boolean;
  children?: ScopeNode[];
}

export interface ScanResponse {
  mode: ScanMode;
  results: AuditResult[];
  totalChecked: number;
}
