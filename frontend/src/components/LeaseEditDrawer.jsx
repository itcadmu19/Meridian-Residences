import React, { useEffect, useState } from "react";
import { X } from "lucide-react";
import StatusBadge from "./StatusBadge";

function formatCurrency(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatDate(value) {
  if (!value) return "—";
  return new Date(`${value}T00:00:00`).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

export default function LeaseEditDrawer({ open, mode, lease, saving, error, onClose, onSave }) {
  const [monthlyRate, setMonthlyRate] = useState("");
  const [endDate, setEndDate] = useState("");
  const [renewalDate, setRenewalDate] = useState("");

  useEffect(() => {
    if (lease) {
      setMonthlyRate(String(lease.monthly_rate ?? ""));
      setEndDate(lease.end_date ?? "");
      setRenewalDate(lease.renewal_date ?? "");
    }
  }, [lease]);

  if (!open || !lease) return null;

  const isEdit = mode === "edit";

  function handleSubmit(event) {
    event.preventDefault();
    onSave({
      monthly_rate: monthlyRate === "" ? undefined : Number(monthlyRate),
      end_date: endDate || undefined,
      renewal_date: renewalDate || undefined,
    });
  }

  return (
    <div className="drawer-overlay" role="presentation" onClick={onClose}>
      <aside
        className="drawer-panel"
        role="dialog"
        aria-modal="true"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="drawer-heading">
          <div>
            <span className="section-kicker">{isEdit ? "EDIT LEASE" : "LEASE DETAILS"}</span>
            <h3>{lease.unit?.unit_number ? `Apartment ${lease.unit.unit_number}` : "Lease"}</h3>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close">
            <X size={18} />
          </button>
        </div>

        <div className="drawer-body">
          <div className="drawer-summary-row">
            <div>
              <span>Tenant</span>
              <strong>{lease.guest?.name || "—"}</strong>
              <small>{lease.guest?.email}</small>
            </div>
            <div>
              <span>Residence</span>
              <strong>{lease.property?.name || "—"}</strong>
              <small>{lease.unit?.unit_number ? `Apartment ${lease.unit.unit_number}` : ""}</small>
            </div>
            <div>
              <span>Status</span>
              <StatusBadge status={lease.status} />
            </div>
          </div>

          {isEdit ? (
            <form className="drawer-form" onSubmit={handleSubmit}>
              <label>
                Monthly rent
                <input
                  type="number"
                  min="1"
                  step="1"
                  value={monthlyRate}
                  onChange={(event) => setMonthlyRate(event.target.value)}
                  required
                />
              </label>
              <label>
                End date
                <input
                  type="date"
                  value={endDate}
                  onChange={(event) => setEndDate(event.target.value)}
                  required
                />
              </label>
              <label>
                Renewal date
                <input
                  type="date"
                  value={renewalDate}
                  onChange={(event) => setRenewalDate(event.target.value)}
                />
              </label>

              {error && <div className="demo-notice demo-notice--error">{error}</div>}

              <div className="drawer-form-actions">
                <button type="button" className="secondary-button" onClick={onClose} disabled={saving}>
                  Cancel
                </button>
                <button type="submit" className="primary-button" disabled={saving}>
                  {saving ? "Saving…" : "Save changes"}
                </button>
              </div>
            </form>
          ) : (
            <div className="summary-list">
              <div>
                <span>Start date</span>
                <strong>{formatDate(lease.start_date)}</strong>
              </div>
              <div>
                <span>End date</span>
                <strong>{formatDate(lease.end_date)}</strong>
              </div>
              <div>
                <span>Renewal date</span>
                <strong>{formatDate(lease.renewal_date)}</strong>
              </div>
              <div>
                <span>Monthly rent</span>
                <strong>{formatCurrency(lease.monthly_rate)}</strong>
              </div>
            </div>
          )}
        </div>
      </aside>
    </div>
  );
}
