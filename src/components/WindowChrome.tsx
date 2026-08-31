import { getCurrentWindow } from "@tauri-apps/api/window";
import { HelpCircle, Minus, RotateCcw, Square, X } from "lucide-react";
import type { Language } from "../types";
import { isTauri } from "../bridge";
import BrandMark from "./BrandMark";

interface Props {
  language: Language;
  onLanguageChange: (language: Language) => void;
  onReconnect: () => void;
  onHelp: () => void;
}

export default function WindowChrome({ language, onLanguageChange, onReconnect, onHelp }: Props) {
  const windowAction = async (action: "minimize" | "toggleMaximize" | "close") => {
    if (!isTauri()) return;
    const appWindow = getCurrentWindow();
    await appWindow[action]();
  };

  return (
    <header className="window-chrome" data-tauri-drag-region onDoubleClick={() => windowAction("toggleMaximize")}>
      <div className="window-brand" data-tauri-drag-region>
        <BrandMark />
        <span data-tauri-drag-region>Bus Routing Auditor</span>
        <span className="build-tag" data-tauri-drag-region>V.2.0.0</span>
      </div>
      <div className="chrome-actions">
        <button className="icon-text-button" onClick={onHelp}><HelpCircle size={13} />{language === "ko" ? "도움말" : "Help"}</button>
        <button className="icon-text-button" onClick={onReconnect}><RotateCcw size={13} />{language === "ko" ? "재연결" : "Reconnect"}</button>
        <div className="language-switch" aria-label="Language">
          <button className={language === "ko" ? "active" : ""} onClick={() => onLanguageChange("ko")}>한</button>
          <button className={language === "en" ? "active" : ""} onClick={() => onLanguageChange("en")}>EN</button>
        </div>
        <button className="window-button" aria-label="Minimize" onClick={() => windowAction("minimize")}><Minus size={14} /></button>
        <button className="window-button" aria-label="Maximize" onClick={() => windowAction("toggleMaximize")}><Square size={11} /></button>
        <button className="window-button close" aria-label="Close" onClick={() => windowAction("close")}><X size={14} /></button>
      </div>
    </header>
  );
}
