import React from "react";

// Shared semantic status display. Do not create per-story status badge variants.
const STATUS_STYLES = {
  // Lease
  active: "success",
  pending: "warning",
  expired: "error",
  terminated: "error",
  // Invoice
  paid: "success",
  overdue: "error",
  due_extended: "info",
  cancelled: "neutral",
  // Maintenance ticket
  open: "info",
  assigned: "info",
  in_progress: "warning",
  resolved: "success",
};

function formatLabel(status) {
  return String(status).replace(/_/g, " ").toUpperCase();
}

export default function StatusBadge({ status }) {
  const variant = STATUS_STYLES[status] || "neutral";
  return <span className={`badge badge--${variant}`}>{formatLabel(status)}</span>;
}
