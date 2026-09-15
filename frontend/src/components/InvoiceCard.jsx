import React from "react";
import { CalendarDays, ChevronRight, Download } from "lucide-react";
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

export default function InvoiceCard({ invoice, onDownload, isStaff, isSelected, onSelect, onPay, onExtendDueDate }) {
  const canSelect = isStaff && ["pending", "payment_submitted"].includes(invoice.payment_status);
  const canPay = !isStaff && ["pending", "overdue", "due_extended"].includes(invoice.payment_status);

  return (
    <Card className="invoice-row">
      <label className={`invoice-row__select${isStaff ? "" : " invoice-row__select--empty"}`} title={isStaff ? "Select invoice" : undefined}>
        {isStaff && (
          <input
            type="checkbox"
            checked={Boolean(isSelected)}
            disabled={!canSelect}
            onChange={() => onSelect(invoice.id)}
          />
        )}
        </label>
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
      <div className="invoice-row__status"><StatusBadge status={invoice.payment_status} /></div>
      <div className="invoice-row__actions">
        {canPay && (
          <button type="button" className="invoice-row__pay" onClick={() => onPay(invoice)}>
            Pay amount
          </button>
        )}
        {invoice.payment_status === "payment_submitted" && (
          <span className="invoice-row__awaiting">Awaiting approval</span>
        )}
        {isStaff && onExtendDueDate && invoice.payment_status !== "paid" && (
          <button type="button" className="invoice-row__extend" onClick={() => onExtendDueDate(invoice)}>
            Extend due date
          </button>
        )}
        {onDownload && (
          <button
            type="button"
            className="invoice-row__download"
            title="Download invoice PDF"
            onClick={(event) => {
              event.stopPropagation();
              onDownload(invoice.id);
            }}
          >
            <Download size={16} />
          </button>
        )}
        <ChevronRight className="invoice-row__chevron" size={18} />
      </div>
    </Card>
  );
}
