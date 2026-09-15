import { getCurrentWindow } from "@tauri-apps/api/window";
import { openUrl } from "@tauri-apps/plugin-opener";
import { HelpCircle, Minus, RotateCcw, Square, X } from "lucide-react";
import type { Language } from "../types";
import { isTauri } from "../bridge";
import { appBrand, hubLink, productBrand } from "../branding";

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

  const openHub = async () => {
    if (!isTauri()) {
      window.open(hubLink.url, "_blank", "noopener");
      return;
    }
    await openUrl(hubLink.url);
  };

  return (
    <header className="window-chrome" data-tauri-drag-region onDoubleClick={() => windowAction("toggleMaximize")}>
      <div className="studio-row" data-tauri-drag-region>
        <div className="suite-brand" data-tauri-drag-region aria-label={appBrand.name}>
          <span className="suite-mark" data-tauri-drag-region aria-hidden="true" />
          <span className="suite-wordmark" data-tauri-drag-region>
            <strong>{appBrand.eyebrow}</strong>
            <span>{appBrand.wordmark}</span>
          </span>
        </div>
        <div className="brand-chrome-right">
          <button
            className="hub-badge"
            onClick={openHub}
            title={language === "ko" ? "YSG Audio Labs 허브 열기" : "Open the YSG Audio Labs hub"}
            aria-label={language === "ko" ? "YSG Audio Labs 허브 열기" : "Open the YSG Audio Labs hub"}
          >
            <img src={hubLink.logoUrl} alt="" draggable={false} />
            <span>{hubLink.label}</span>
          </button>
          <div className="window-controls">
            <button className="window-button" aria-label="Minimize" onClick={() => windowAction("minimize")}><Minus size={14} /></button>
            <button className="window-button" aria-label="Maximize" onClick={() => windowAction("toggleMaximize")}><Square size={11} /></button>
            <button className="window-button close" aria-label="Close" onClick={() => windowAction("close")}><X size={14} /></button>
          </div>
        </div>
      </div>
      <div className="product-row" data-tauri-drag-region>
        <div className="window-brand" data-tauri-drag-region>
          <img className="product-logo" src={productBrand.logoUrl} alt="" draggable={false} data-tauri-drag-region />
          <span data-tauri-drag-region>{productBrand.name}</span>
          <span className="build-tag" data-tauri-drag-region>V.2.0.1</span>
        </div>
        <div className="chrome-actions">
          <button className="icon-text-button" onClick={onHelp}><HelpCircle size={13} />{language === "ko" ? "도움말" : "Help"}</button>
          <button className="icon-text-button" onClick={onReconnect}><RotateCcw size={13} />{language === "ko" ? "재연결" : "Reconnect"}</button>
          <div className="language-switch" aria-label="Language">
            <button className={language === "ko" ? "active" : ""} onClick={() => onLanguageChange("ko")}>한</button>
            <button className={language === "en" ? "active" : ""} onClick={() => onLanguageChange("en")}>EN</button>
          </div>
        </div>
      </div>
    </header>
  );
}
