import React from "react";

export default function SummaryCard({ icon, label, value, detail, accent = "" }) {
  return (
    <article className={`summary-card ${accent}`}>
      <div className="summary-card-top">
        <div className="summary-icon">{icon}</div>
        <span>{label}</span>
      </div>
      <strong>{value}</strong>
      {detail && <small>{detail}</small>}
    </article>
  );
}