import React, { useEffect } from "react";
import { CheckCircle2, X } from "lucide-react";

export default function Toast({ open, onClose, title, message, autoDismissMs = 6000 }) {
  useEffect(() => {
    if (!open || !autoDismissMs) return undefined;
    const timer = setTimeout(onClose, autoDismissMs);
    return () => clearTimeout(timer);
  }, [open, onClose, autoDismissMs]);

  if (!open) return null;

  return (
    <div className="toast" role="status">
      <div className="toast-icon">
        <CheckCircle2 size={18} />
      </div>
      <div className="toast-content">
        <strong>{title}</strong>
        <span>{message}</span>
      </div>
      <button className="toast-close" aria-label="Dismiss" onClick={onClose}>
        <X size={14} />
      </button>
    </div>
  );
}
