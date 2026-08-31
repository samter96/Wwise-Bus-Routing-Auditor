import { useCallback, useEffect, useMemo, useState } from "react";
import { save } from "@tauri-apps/plugin-dialog";
import { AlertTriangle, Check, CircleHelp, LoaderCircle, Route, ScanSearch, X } from "lucide-react";
import { backendRequest, isTauri } from "./bridge";
import { copy } from "./i18n";
import type { AuditResult, AuditState, ConnectionState, Language, Rule, RuleConfig, ScanMode, ScanResponse, ScopeNode } from "./types";
import RoutingOrbit from "./components/RoutingOrbit";
import ResultsTable from "./components/ResultsTable";
import ScopeTree from "./components/ScopeTree";
import WindowChrome from "./components/WindowChrome";
import PrecisionCheck from "./components/PrecisionCheck";

const emptyConfig: RuleConfig = { name_rules: [], workunit_rules: [], flag_unset_bus: true };
const SCAN_UI_TIMEOUT_MS = 75_000;

function updateNode(nodes: ScopeNode[], path: string, updater: (node: ScopeNode) => ScopeNode): ScopeNode[] {
  return nodes.map((node) => {
    if (node.path === path) return updater(node);
    if (!node.children) return node;
    return { ...node, children: updateNode(node.children, path, updater) };
  });
}

function ruleSource(rule: Rule, mode: ScanMode) {
  const primary = mode === "name" ? rule.keyword : rule.work_unit_keyword;
  const extras = mode === "name" ? rule.extra_keywords : rule.extra_work_unit_keywords;
  return [primary, ...(extras ?? [])].filter(Boolean).join(" | ");
}

function ruleBus(rule: Rule) {
  return [rule.expected_bus_keyword, ...(rule.extra_bus_keywords ?? [])].filter(Boolean).join(" | ");
}

function withTimeout<T>(promise: Promise<T>, timeoutMs: number, message: string): Promise<T> {
  return new Promise((resolve, reject) => {
    const timer = window.setTimeout(() => reject(new Error(message)), timeoutMs);
    promise.then(
      (value) => {
        window.clearTimeout(timer);
        resolve(value);
      },
      (error) => {
        window.clearTimeout(timer);
        reject(error);
      },
    );
  });
}

export default function App() {
  const [language, setLanguage] = useState<Language>("ko");
  const [connection, setConnection] = useState<ConnectionState>("connecting");
  const [projectName, setProjectName] = useState("");
  const [auditState, setAuditState] = useState<AuditState>("idle");
  const [mode, setMode] = useState<ScanMode>("name");
  const [config, setConfig] = useState<RuleConfig>(emptyConfig);
  const [results, setResults] = useState<AuditResult[]>([]);
  const [totalChecked, setTotalChecked] = useState(0);
  const [scopeNodes, setScopeNodes] = useState<ScopeNode[]>([]);
  const [selectedPaths, setSelectedPaths] = useState<Set<string>>(new Set());
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [buses, setBuses] = useState<string[]>([]);
  const [targetBus, setTargetBus] = useState("");
  const [message, setMessage] = useState<{ tone: "error" | "success"; text: string } | null>(null);
  const [helpOpen, setHelpOpen] = useState(false);
  const t = copy(language);

  const showMessage = useCallback((tone: "error" | "success", text: string) => {
    setMessage({ tone, text });
    window.setTimeout(() => setMessage(null), 3600);
  }, []);

  const loadConfig = useCallback(async () => {
    const data = await backendRequest<{ config: RuleConfig }>("get_config");
    setConfig(data.config);
  }, []);

  const loadRootScope = useCallback(async () => {
    const data = await backendRequest<{ children: ScopeNode[] }>("scope_children", { path: "\\Actor-Mixer Hierarchy" });
    setScopeNodes(data.children);
  }, []);

  const connect = useCallback(async () => {
    setConnection("connecting");
    try {
      const data = await backendRequest<{ connected: boolean; projectName: string; buses: string[] }>("connect");
      setConnection(data.connected ? "connected" : "error");
      setProjectName(data.projectName);
      setBuses(data.buses);
      await Promise.all([loadConfig(), loadRootScope()]);
    } catch (error) {
      setConnection("error");
      setProjectName("");
      showMessage("error", error instanceof Error ? error.message : String(error));
      try { await loadConfig(); } catch { /* keep defaults */ }
    }
  }, [loadConfig, loadRootScope, showMessage]);

  useEffect(() => { void connect(); }, [connect]);

  const currentRules = mode === "name" ? config.name_rules : config.workunit_rules;

  const updateRules = (rules: Rule[]) => {
    setConfig((current) => mode === "name"
      ? { ...current, name_rules: rules }
      : { ...current, workunit_rules: rules });
  };

  const saveRules = async () => {
    try {
      await backendRequest("save_config", { config });
      showMessage("success", t.savedRules);
    } catch (error) {
      showMessage("error", error instanceof Error ? error.message : String(error));
    }
  };

  const addRule = () => {
    const next: Rule = mode === "name"
      ? { keyword: "", expected_bus_keyword: "", case_sensitive: false }
      : { work_unit_keyword: "", expected_bus_keyword: "", case_sensitive: false };
    updateRules([...currentRules, next]);
  };

  const patchRule = (index: number, patch: Partial<Rule>) => {
    updateRules(currentRules.map((rule, i) => i === index ? { ...rule, ...patch } : rule));
  };

  const removeRule = (index: number) => {
    updateRules(currentRules.filter((_, i) => i !== index));
  };

  const toggleScope = async (node: ScopeNode) => {
    if (node.expanded) {
      setScopeNodes((current) => updateNode(current, node.path, (item) => ({ ...item, expanded: false })));
      return;
    }
    if (node.loaded) {
      setScopeNodes((current) => updateNode(current, node.path, (item) => ({ ...item, expanded: true })));
      return;
    }
    setScopeNodes((current) => updateNode(current, node.path, (item) => ({ ...item, loading: true })));
    try {
      const data = await backendRequest<{ children: ScopeNode[] }>("scope_children", { path: node.path });
      setScopeNodes((current) => updateNode(current, node.path, (item) => ({ ...item, loading: false, loaded: true, expanded: true, children: data.children })));
    } catch (error) {
      setScopeNodes((current) => updateNode(current, node.path, (item) => ({ ...item, loading: false })));
      showMessage("error", error instanceof Error ? error.message : String(error));
    }
  };

  const selectScope = (path: string) => {
    if (!path) {
      setSelectedPaths(new Set());
      return;
    }
    setSelectedPaths((current) => {
      const next = new Set(current);
      if (next.has(path)) next.delete(path); else next.add(path);
      return next;
    });
  };

  const runScan = async () => {
    if (connection !== "connected") {
      showMessage("error", t.disconnected);
      return;
    }
    setAuditState("scanning");
    setSelectedIds(new Set());
    try {
      await backendRequest("save_config", { config });
      const data = await withTimeout(
        backendRequest<ScanResponse>("scan", { mode, scopePaths: Array.from(selectedPaths) }),
        SCAN_UI_TIMEOUT_MS,
        language === "ko"
          ? "스캔 응답이 75초를 초과했습니다. Wwise 연결을 재확인한 뒤 범위를 좁혀 다시 실행하세요."
          : "The scan took more than 75 seconds. Check the Wwise connection and retry with a narrower scope.",
      );
      setResults(data.results);
      setTotalChecked(data.totalChecked);
      setAuditState("complete");
    } catch (error) {
      setAuditState("error");
      showMessage("error", `${t.scanFailed} ${error instanceof Error ? error.message : String(error)}`);
    }
  };

  const selectRow = (id: string, additive: boolean) => {
    setSelectedIds((current) => {
      if (!additive) return new Set([id]);
      const next = new Set(current);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const requireSelection = () => {
    const ids = Array.from(selectedIds).filter((id) => results.some((row) => row.id === id));
    if (!ids.length) showMessage("error", t.selectionNeeded);
    return ids;
  };

  const viewInWwise = async () => {
    const ids = requireSelection();
    if (!ids.length) return;
    try { await backendRequest("select_in_wwise", { ids }); }
    catch (error) { showMessage("error", error instanceof Error ? error.message : String(error)); }
  };

  const reroute = async () => {
    const ids = requireSelection();
    if (!ids.length) return;
    if (!targetBus) {
      showMessage("error", t.busNeeded);
      return;
    }
    try {
      await backendRequest("reroute", { ids, busName: targetBus });
      showMessage("success", t.rerouteDone);
      await runScan();
    } catch (error) {
      showMessage("error", error instanceof Error ? error.message : String(error));
    }
  };

  const exportCsv = async () => {
    if (!results.length) return;
    const path = isTauri() ? await save({ defaultPath: "bus_routing_audit.csv", filters: [{ name: "CSV", extensions: ["csv"] }] }) : "bus_routing_audit.csv";
    if (!path) return;
    try {
      await backendRequest("export_csv", { path, language, rows: results });
      showMessage("success", t.exportDone);
    } catch (error) { showMessage("error", error instanceof Error ? error.message : String(error)); }
  };

  const inheritedCount = results.filter((row) => row.inherited || row.unset).length;
  const routingScore = totalChecked ? Math.max(0, ((totalChecked - results.length) / totalChecked) * 100) : 100;
  const scoreDisplay = routingScore < 100 && routingScore >= 99 ? routingScore.toFixed(1) : Math.round(routingScore).toString();
  const hero = useMemo(() => {
    if (auditState === "scanning") return { body: t.scanBody };
    if (auditState === "complete") return { body: t.resultBody };
    if (auditState === "error") return { body: t.scanFailed };
    return { body: t.idleBody };
  }, [auditState, results.length, t]);

  return (
    <main className="app-shell bus-routing">
      <WindowChrome language={language} onLanguageChange={setLanguage} onReconnect={connect} onHelp={() => setHelpOpen(true)} />

      <section className="project-bar">
        <div className={`connection-badge ${connection}`}><i />{connection === "connecting" ? t.connecting : connection === "connected" ? t.connected : t.disconnected}</div>
        {projectName && <><span className="project-name">{projectName}</span><span className="project-separator">/</span><span className="project-location">Actor-Mixer Hierarchy</span></>}
        <span className="local-note">{t.local}</span>
      </section>

      <section className="hero-section">
        <div className="hero-copy">
          <span className="eyebrow">{t.eyebrow}</span>
          <h1>{t.product}</h1>
          <p>{hero.body}</p>
          <button className="criteria-button" onClick={() => setHelpOpen(true)}><CircleHelp size={13} />{t.confidence}</button>
        </div>
        <RoutingOrbit state={auditState} issueCount={results.length} />
        <div className="score-block">
          <span>{t.score}</span>
          <strong>{auditState === "complete" ? scoreDisplay : "—"}<small>{auditState === "complete" ? "/100" : ""}</small></strong>
          <div className="score-track"><i style={{ width: auditState === "complete" ? `${routingScore}%` : "0%" }} /></div>
          <div className="score-axis"><span>0</span><span>100</span></div>
        </div>
      </section>

      <section className="control-strip panel">
        <div className="control-group object-options">
          <span className="section-label">{t.scanMode}</span>
          <label><input type="radio" checked={mode === "name"} onChange={() => { setMode("name"); setResults([]); setAuditState("idle"); }} /><i><PrecisionCheck /></i><Route size={14} />{t.nameMode}</label>
          <label><input type="radio" checked={mode === "workunit"} onChange={() => { setMode("workunit"); setResults([]); setAuditState("idle"); }} /><i><PrecisionCheck /></i><Route size={14} />{t.workunitMode}</label>
          <label><input type="checkbox" checked={config.flag_unset_bus} onChange={(event) => setConfig((current) => ({ ...current, flag_unset_bus: event.target.checked }))} /><i><PrecisionCheck /></i>{t.flagUnset}</label>
        </div>
        <div className="legend-group"><span><i className="miss" />{t.overriddenBus}</span><span><i className="extra" />{t.inheritedBus}</span></div>
        <button className="scan-button" onClick={runScan} disabled={auditState === "scanning" || connection !== "connected"}>
          {auditState === "scanning" ? <LoaderCircle className="spin" size={15} /> : <ScanSearch size={15} />}
          {auditState === "scanning" ? t.scanning : t.runScan}
        </button>
      </section>

      <section className="metrics-strip">
        <div><span>{t.checked}</span><strong>{auditState === "complete" ? totalChecked.toLocaleString() : "—"}</strong><small>{mode === "name" ? t.nameMode : t.workunitMode}</small></div>
        <div className={results.length ? "danger" : auditState === "complete" ? "clean" : ""}><span>{t.violations}</span><strong>{auditState === "complete" ? results.length : "—"}</strong><small>{auditState === "complete" ? (results.length ? t.issueTitle(results.length) : t.noViolations) : t.expectedBus}</small></div>
        <div className="violet"><span>{t.inherited}</span><strong>{auditState === "complete" ? inheritedCount : "—"}</strong><small>{t.inheritedBus} / {t.unsetBus}</small></div>
      </section>

      <section className="workspace">
        <ScopeTree nodes={scopeNodes} selectedPaths={selectedPaths} allLabel={t.scopeAll} hint={t.scopeHint} onToggle={toggleScope} onSelect={selectScope} onRefresh={loadRootScope} />
        <div className="workspace-stack">
          <section className="rules-panel panel">
            <div className="rules-heading"><span className="section-label">{t.rules}</span><button className="secondary-button" onClick={addRule}>{t.addRule}</button><button className="secondary-button" onClick={saveRules}>{t.saveRules}</button></div>
            <div className="rules-list">
              {currentRules.map((rule, index) => (
                <div className="rule-row" key={`${mode}-${index}`}>
                  <input value={ruleSource(rule, mode)} onChange={(event) => patchRule(index, mode === "name" ? { keyword: event.target.value } : { work_unit_keyword: event.target.value })} placeholder={t.sourceKeyword} />
                  <span>→</span>
                  <input value={ruleBus(rule)} onChange={(event) => patchRule(index, { expected_bus_keyword: event.target.value })} placeholder={t.busKeyword} />
                  <label><input type="checkbox" checked={Boolean(rule.case_sensitive)} onChange={(event) => patchRule(index, { case_sensitive: event.target.checked })} />{t.caseSensitive}</label>
                  <button className="modal-close inline" onClick={() => removeRule(index)}><X size={14} /></button>
                </div>
              ))}
            </div>
          </section>
          <ResultsTable language={language} results={results} selectedIds={selectedIds} scanned={auditState === "complete"} buses={buses} targetBus={targetBus} onTargetBusChange={setTargetBus} onSelect={selectRow} onView={viewInWwise} onExport={exportCsv} onReroute={reroute} />
        </div>
      </section>

      {message && <div className={`toast ${message.tone}`}>{message.tone === "error" ? <AlertTriangle size={15} /> : <Check size={15} />}{message.text}</div>}
      {helpOpen && (
        <div className="modal-backdrop" onMouseDown={() => setHelpOpen(false)}>
          <section className="criteria-modal" onMouseDown={(event) => event.stopPropagation()}>
            <button className="modal-close" onClick={() => setHelpOpen(false)}><X size={15} /></button>
            <span className="eyebrow">BUS ROUTING CONTRACT</span>
            <h2>{t.helpTitle}</h2>
            <p>{t.helpBody}</p>
            <div className="criteria-grid">
              <div><span className="criteria-index">SCAN 1</span><strong>{t.nameMode}</strong><code>Sound.name contains source keyword</code><code>OutputBus.name contains expected keyword</code></div>
              <div><span className="criteria-index">SCAN 2</span><strong>{t.workunitMode}</strong><code>WorkUnit name/path contains source keyword</code><code>OutputBus.name contains expected keyword</code></div>
              <div className="miss"><span className="criteria-index">OVERRIDE</span><strong>{t.overriddenBus}</strong><p>{t.trigger}</p></div>
              <div className="extra"><span className="criteria-index">INHERITED</span><strong>{t.inheritedBus}</strong><p>{t.flagUnset}</p></div>
            </div>
          </section>
        </div>
      )}
    </main>
  );
}
