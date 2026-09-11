import React from "react";
import { Building2, CalendarDays, Home, Wallet } from "lucide-react";
import Card from "./Card.jsx";
import StatusBadge from "./StatusBadge.jsx";

function formatDate(value) {
  if (!value) return "Not set";
  return new Date(`${value}T00:00:00`).toLocaleDateString(undefined, {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function formatCurrency(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(Number(value));
}

export default function LeaseCard({ lease }) {
  return (
    <Card className="lease-card">
      <div className="lease-card__header">
        <div>
          <span className="eyebrow">CURRENT LEASE</span>
          <h2 className="lease-card__title">Apartment {lease.unit_number}</h2>
          <p className="lease-card__subtitle">{lease.property_name}</p>
        </div>
        <StatusBadge status={lease.status} />
      </div>

      <div className="lease-card__details">
        <div className="detail-item">
          <CalendarDays size={17} />
          <div>
            <span className="detail-item__label">Lease period</span>
            <strong>{formatDate(lease.start_date)} — {formatDate(lease.end_date)}</strong>
          </div>
        </div>
        <div className="detail-item">
          <Wallet size={17} />
          <div>
            <span className="detail-item__label">Monthly rent</span>
            <strong>{formatCurrency(lease.monthly_rate)}</strong>
          </div>
        </div>
        <div className="detail-item">
          <Home size={17} />
          <div>
            <span className="detail-item__label">Unit type</span>
            <strong>{lease.unit_type || "Residence"}</strong>
          </div>
        </div>
        <div className="detail-item">
          <Building2 size={17} />
          <div>
            <span className="detail-item__label">Renewal date</span>
            <strong>{formatDate(lease.renewal_date)}</strong>
          </div>
        </div>
      </div>
    </Card>
  );
}
