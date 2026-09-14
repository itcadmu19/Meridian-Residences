import React from "react";
import { AlertTriangle, X } from "lucide-react";

export default function EscalationBanner({ message, onDismiss }) {
  return (
    <div className="escalation-banner" role="alert">
      <AlertTriangle size={18} />
      <span>{message}</span>
      <button type="button" className="escalation-banner__close" onClick={onDismiss} aria-label="Dismiss">
        <X size={16} />
      </button>
    </div>
  );
}
