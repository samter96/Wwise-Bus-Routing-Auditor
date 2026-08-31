import { ArrowDownToLine, ExternalLink, FileSearch, GitBranch, ShieldCheck } from "lucide-react";
import type { AuditResult, Language } from "../types";
import { copy } from "../i18n";

interface Props {
  language: Language;
  results: AuditResult[];
  selectedIds: Set<string>;
  scanned: boolean;
  buses: string[];
  targetBus: string;
  onTargetBusChange: (bus: string) => void;
  onSelect: (id: string, additive: boolean) => void;
  onView: () => void;
  onExport: () => void;
  onReroute: () => void;
}

export default function ResultsTable({
  language,
  results,
  selectedIds,
  scanned,
  buses,
  targetBus,
  onTargetBusChange,
  onSelect,
  onView,
  onExport,
  onReroute,
}: Props) {
  const t = copy(language);
  const emptyTitle = scanned ? t.noViolations : t.noResults;
  const emptyBody = !scanned ? t.noResultsBody : "";

  return (
    <section className="results-panel panel">
      <div className="results-tabs">
        <button className="active">{t.violationsTab}<span>{results.length}</span></button>
      </div>
      <div className="table-shell">
        <table>
          <thead>
            <tr>
              <th>{t.name}</th>
              <th>{t.workunit}</th>
              <th>{t.currentBus}</th>
              <th>{t.trigger}</th>
              <th>{t.expectedBus}</th>
              <th>{t.path}</th>
            </tr>
          </thead>
          <tbody>
            {results.map((row) => (
              <tr
                key={row.id}
                className={`${row.inherited ? "extra" : "miss"} ${selectedIds.has(row.id) ? "selected" : ""}`}
                onClick={(event) => onSelect(row.id, event.ctrlKey || event.metaKey)}
                onDoubleClick={onView}
                title={row.path}
              >
                <td><span className="asset-name">{row.name}</span><span className="asset-path">{row.path}</span></td>
                <td>{row.work_unit}</td>
                <td><span className={`issue-badge ${row.unset ? "extra" : row.inherited ? "extra" : "miss"}`}><i />{row.unset ? t.unsetBus : row.inherited ? t.inheritedBus : t.overriddenBus}</span>{row.current_bus}</td>
                <td>{row.trigger}</td>
                <td>{row.expected_bus_keyword}</td>
                <td>{row.path}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {results.length === 0 && (
          <div className="empty-results">
            {scanned ? <ShieldCheck size={26} /> : <FileSearch size={26} />}
            <strong>{emptyTitle}</strong>
            {emptyBody && <span>{emptyBody}</span>}
          </div>
        )}
      </div>
      <footer className="results-actions">
        <div>
          <button className="secondary-button" onClick={onView}><ExternalLink size={13} />{t.viewWwise}</button>
          <button className="secondary-button" onClick={onExport} disabled={!results.length}><ArrowDownToLine size={13} />{t.exportCsv}</button>
        </div>
        <div className="reroute-controls">
          <label>
            <span>{t.targetBus}</span>
            <select value={targetBus} onChange={(event) => onTargetBusChange(event.target.value)}>
              <option value=""></option>
              {buses.map((bus) => <option value={bus} key={bus}>{bus}</option>)}
            </select>
          </label>
          <button className="exception-button" onClick={onReroute} disabled={!results.length}><GitBranch size={13} />{t.reroute}</button>
        </div>
      </footer>
    </section>
  );
}
