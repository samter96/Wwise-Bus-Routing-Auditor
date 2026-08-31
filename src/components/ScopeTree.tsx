import { ChevronRight, Folder, FolderOpen, Layers3, LoaderCircle, RefreshCw, Volume2 } from "lucide-react";
import type { ScopeNode } from "../types";
import PrecisionCheck from "./PrecisionCheck";

interface Props {
  nodes: ScopeNode[];
  selectedPaths: Set<string>;
  allLabel: string;
  hint: string;
  onToggle: (node: ScopeNode) => void;
  onSelect: (path: string) => void;
  onRefresh: () => void;
}

function NodeIcon({ node }: { node: ScopeNode }) {
  if (node.type === "Sound") return <Volume2 size={14} />;
  if (node.type.includes("Container") || node.type === "ActorMixer") return <Layers3 size={14} />;
  return node.expanded ? <FolderOpen size={14} /> : <Folder size={14} />;
}

function TreeNode({ node, depth, selectedPaths, onToggle, onSelect }: {
  node: ScopeNode;
  depth: number;
  selectedPaths: Set<string>;
  onToggle: (node: ScopeNode) => void;
  onSelect: (path: string) => void;
}) {
  const selected = selectedPaths.has(node.path);
  return (
    <>
      <div className={`tree-node ${selected ? "selected" : ""}`} style={{ "--depth": depth } as React.CSSProperties}>
        <button className="tree-expander" aria-label="Expand" onClick={() => onToggle(node)} disabled={!node.expandable}>
          {node.loading ? <LoaderCircle className="spin" size={13} /> : <ChevronRight className={node.expanded ? "expanded" : ""} size={13} />}
        </button>
        <button className="tree-label" onClick={() => onSelect(node.path)} title={node.path}>
          <NodeIcon node={node} />
          <span>{node.name}</span>
        </button>
        <button className={`tree-check ${selected ? "checked" : ""}`} aria-label="Select scope" onClick={() => onSelect(node.path)}>{selected && <PrecisionCheck />}</button>
      </div>
      {node.expanded && node.children?.map((child) => (
        <TreeNode key={child.path} node={child} depth={depth + 1} selectedPaths={selectedPaths} onToggle={onToggle} onSelect={onSelect} />
      ))}
    </>
  );
}

export default function ScopeTree({ nodes, selectedPaths, allLabel, hint, onToggle, onSelect, onRefresh }: Props) {
  return (
    <aside className="scope-panel panel">
      <div className="panel-heading">
        <div>
          <span className="section-label">SCAN SCOPE</span>
          <strong>{selectedPaths.size ? `${selectedPaths.size} selected` : allLabel}</strong>
        </div>
        <button className="square-button" aria-label="Refresh scope" onClick={onRefresh}><RefreshCw size={14} /></button>
      </div>
      <p className="scope-hint">{hint}</p>
      <div className={`tree-node tree-root ${selectedPaths.size === 0 ? "selected" : ""}`}>
        <span className="tree-expander"><ChevronRight className="expanded" size={13} /></span>
        <button className="tree-label" onClick={() => onSelect("")}><Layers3 size={14} /><span>{allLabel}</span></button>
        <button className={`tree-check ${selectedPaths.size === 0 ? "checked" : ""}`} aria-label="Select all scopes" onClick={() => onSelect("")}>{selectedPaths.size === 0 && <PrecisionCheck />}</button>
      </div>
      <div className="tree-scroll">
        {nodes.map((node) => <TreeNode key={node.path} node={node} depth={0} selectedPaths={selectedPaths} onToggle={onToggle} onSelect={onSelect} />)}
      </div>
    </aside>
  );
}
