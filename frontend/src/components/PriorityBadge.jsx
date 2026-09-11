import React from "react";

// Maintenance priority mapping — frozen: LOW=neutral, MEDIUM=info, HIGH=warning, URGENT=error.
const PRIORITY_STYLES = {
  low: "neutral",
  medium: "info",
  high: "warning",
  urgent: "error",
};

export default function PriorityBadge({ priority }) {
  const variant = PRIORITY_STYLES[priority] || "neutral";
  return <span className={`badge badge--${variant}`}>{String(priority).toUpperCase()}</span>;
}
