import React from "react";

export default function StatusBadge({ status = "active" }) {
  const label = status.replaceAll("_", " ");

  return (
    <span className={`status-badge ${status}`}>
      <span className="status-dot" />
      {label.charAt(0).toUpperCase() + label.slice(1)}
    </span>
  );
}