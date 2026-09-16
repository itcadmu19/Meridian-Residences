import React from "react";

export default function PlaceholderPage({ title }) {
  return (
    <div className="placeholder-page">
      <span className="section-kicker">MERIDIAN RESIDENCES</span>
      <h1>{title}</h1>
      <p>This module is ready to be connected to its backend API.</p>
    </div>
  );
}