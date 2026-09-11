import React from "react";
import Card from "./Card.jsx";

export default function StatCard({ icon: Icon, label, value }) {
  return (
    <Card className="stat-card">
      {Icon && (
        <div className="stat-card__icon">
          <Icon size={20} />
        </div>
      )}
      <div>
        <div className="stat-card__label">{label}</div>
        <div className="stat-card__value">{value}</div>
      </div>
    </Card>
  );
}
