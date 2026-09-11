import React from "react";
import { CalendarDays, ChevronRight } from "lucide-react";
import Card from "./Card.jsx";
import StatusBadge from "./StatusBadge.jsx";

function formatDate(value) {
  if (!value) return "—";
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

function formatPeriod(start, end) {
  const startDate = new Date(`${start}T00:00:00`);
  const endDate = new Date(`${end}T00:00:00`);
  return `${startDate.toLocaleDateString(undefined, { month: "short", year: "numeric" })}`;
}

export default function InvoiceCard({ invoice }) {
  return (
    <Card className="invoice-row">
      <div className="invoice-row__period">
        <div className="invoice-row__icon"><CalendarDays size={18} /></div>
        <div>
          <strong>{formatPeriod(invoice.billing_period_start, invoice.billing_period_end)}</strong>
          <span>{invoice.id.slice(0, 8).toUpperCase()}</span>
        </div>
      </div>
      <div className="invoice-row__amount">
        <span className="invoice-row__label">Amount</span>
        <strong>{formatCurrency(invoice.amount)}</strong>
      </div>
      <div className="invoice-row__due">
        <span className="invoice-row__label">Due date</span>
        <strong>{formatDate(invoice.due_date)}</strong>
      </div>
      <StatusBadge status={invoice.payment_status} />
      <ChevronRight className="invoice-row__chevron" size={18} />
    </Card>
  );
}
