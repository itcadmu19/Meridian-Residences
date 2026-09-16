import React, { useEffect, useMemo, useState } from "react";
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  Building2,
  CalendarClock,
  CheckCircle2,
  Clock3,
  FileWarning,
  X,
} from "lucide-react";
import {
  activateLease,
  getStaffLeases,
  renewLease,
  terminateLease,
  updateLease,
} from "../services/staffLeaseService";
import SummaryCard from "../components/SummaryCard";
import StatusBadge from "../components/StatusBadge";
import ConfirmDialog from "../components/ConfirmDialog";
import LeaseEditDrawer from "../components/LeaseEditDrawer";
import AgreementDrawer from "../components/AgreementDrawer";
import Toast from "../components/Toast";

const EXPIRING_SOON_DAYS = 30;

const DEMO_LEASES = [
  {
    id: "lease-demo-001",
    guest: { id: "g1", name: "Demo Resident", email: "demo.resident@example.com" },
    unit: { unit_number: "101", unit_type: "2BHK" },
    property: { name: "Meridian Residences", address: "Premium Residential Community" },
    start_date: "2026-01-01",
    end_date: "2026-12-31",
    monthly_rate: 45000,
    renewal_date: "2026-12-01",
    status: "active",
    created_at: "2026-01-01T09:00:00Z",
  },
  {
    id: "lease-demo-002",
    guest: { id: "g2", name: "Other Resident", email: "other.resident@example.com" },
    unit: { unit_number: "101", unit_type: "2BHK" },
    property: { name: "Meridian Residences", address: "Premium Residential Community" },
    start_date: "2027-01-01",
    end_date: "2027-12-31",
    monthly_rate: 47000,
    renewal_date: null,
    status: "pending",
    created_at: "2026-09-10T09:00:00Z",
  },
  {
    id: "lease-demo-003",
    guest: { id: "g1", name: "Demo Resident", email: "demo.resident@example.com" },
    unit: { unit_number: "101", unit_type: "2BHK" },
    property: { name: "Meridian Residences", address: "Premium Residential Community" },
    start_date: "2025-01-01",
    end_date: "2025-12-31",
    monthly_rate: 43000,
    renewal_date: null,
    status: "expired",
    created_at: "2025-01-01T09:00:00Z",
  },
  {
    id: "lease-demo-004",
    guest: { id: "g2", name: "Other Resident", email: "other.resident@example.com" },
    unit: { unit_number: "101", unit_type: "2BHK" },
    property: { name: "Meridian Residences", address: "Premium Residential Community" },
    start_date: "2024-06-01",
    end_date: "2025-05-31",
    monthly_rate: 42000,
    renewal_date: null,
    status: "terminated",
    created_at: "2024-06-01T09:00:00Z",
  },
];

const SORT_COLUMNS = [
  { key: "guest.name", label: "Tenant" },
  { key: "property.name", label: "Residence" },
  { key: "start_date", label: "Start" },
  { key: "end_date", label: "End" },
  { key: "monthly_rate", label: "Rent" },
  { key: "status", label: "Status" },
  { key: "created_at", label: "Added" },
];

function getSortValue(lease, key) {
  return key.split(".").reduce((value, part) => (value == null ? value : value[part]), lease);
}

function compareLeases(a, b, key) {
  const valueA = getSortValue(a, key);
  const valueB = getSortValue(b, key);
  if (valueA == null && valueB == null) return 0;
  if (valueA == null) return -1;
  if (valueB == null) return 1;
  if (typeof valueA === "number" && typeof valueB === "number") return valueA - valueB;
  return String(valueA).localeCompare(String(valueB));
}

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

function isExpiringSoon(lease) {
  if (lease.status !== "active") return false;
  const end = new Date(`${lease.end_date}T00:00:00`);
  const days = (end - new Date()) / (1000 * 60 * 60 * 24);
  return days >= 0 && days <= EXPIRING_SOON_DAYS;
}

const FILTERS = [
  { key: "all", label: "All" },
  { key: "active", label: "Active" },
  { key: "pending", label: "Pending" },
  { key: "expiring", label: "Expiring Soon" },
  { key: "expired", label: "Expired" },
  { key: "terminated", label: "Terminated" },
];

function RenewDialog({ open, lease, busy, error, onConfirm, onCancel }) {
  const [newEndDate, setNewEndDate] = useState("");

  useEffect(() => {
    if (lease) setNewEndDate("");
  }, [lease]);

  if (!open || !lease) return null;

  return (
    <div className="confirm-dialog-overlay" role="presentation" onClick={onCancel}>
      <div className="confirm-dialog" role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
        <div className="confirm-dialog-icon">
          <CalendarClock size={20} />
        </div>
        <h3>Renew lease</h3>
        <p>
          Choose a new end date for {lease.guest?.name}'s lease at{" "}
          {lease.property?.name} (Apartment {lease.unit?.unit_number}). Current end date is{" "}
          {formatDate(lease.end_date)}.
        </p>
        <label className="renew-date-field">
          New end date
          <input
            type="date"
            value={newEndDate}
            min={lease.end_date}
            onChange={(event) => setNewEndDate(event.target.value)}
          />
        </label>
        {error && <div className="demo-notice demo-notice--error">{error}</div>}
        <div className="confirm-dialog-actions">
          <button className="secondary-button" onClick={onCancel} disabled={busy}>
            Cancel
          </button>
          <button
            className="primary-button"
            onClick={() => onConfirm(newEndDate)}
            disabled={busy || !newEndDate}
          >
            {busy ? "Renewing…" : "Renew"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function StaffLeaseManagement() {
  const [leases, setLeases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [usingDemoData, setUsingDemoData] = useState(false);
  const [activeFilter, setActiveFilter] = useState("all");
  const [toast, setToast] = useState(null);
  const [actionError, setActionError] = useState(null);

  const [viewLease, setViewLease] = useState(null);
  const [editLease, setEditLease] = useState(null);
  const [renewTarget, setRenewTarget] = useState(null);
  const [terminateTarget, setTerminateTarget] = useState(null);
  const [agreementLease, setAgreementLease] = useState(null);
  const [busyLeaseId, setBusyLeaseId] = useState(null);
  // Newest-added lease first by default - the backend already returns
  // leases in this order, but sorting client-side too means re-sorting by
  // another column and clicking back to "Added" both work without a
  // re-fetch.
  const [sortKey, setSortKey] = useState("created_at");
  const [sortDirection, setSortDirection] = useState("desc");

  async function loadLeases() {
    try {
      const data = await getStaffLeases();
      setLeases(Array.isArray(data) ? data : []);
      setUsingDemoData(false);
    } catch {
      setLeases(DEMO_LEASES);
      setUsingDemoData(true);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    setLoading(true);
    loadLeases();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const counts = useMemo(() => {
    return {
      active: leases.filter((l) => l.status === "active").length,
      pending: leases.filter((l) => l.status === "pending").length,
      expiring: leases.filter(isExpiringSoon).length,
      expired: leases.filter((l) => l.status === "expired").length,
    };
  }, [leases]);

  const visibleLeases = useMemo(() => {
    const filtered =
      activeFilter === "all"
        ? leases
        : activeFilter === "expiring"
        ? leases.filter(isExpiringSoon)
        : leases.filter((l) => l.status === activeFilter);

    const sorted = [...filtered].sort((a, b) => compareLeases(a, b, sortKey));
    return sortDirection === "desc" ? sorted.reverse() : sorted;
  }, [leases, activeFilter, sortKey, sortDirection]);

  function handleSort(key) {
    if (key === sortKey) {
      setSortDirection((prev) => (prev === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDirection("asc");
    }
  }

  function withDemoGuard(action) {
    return async (...args) => {
      if (usingDemoData) {
        setActionError("Backend is not connected - actions are disabled while showing demo data.");
        return;
      }
      return action(...args);
    };
  }

  const handleActivate = withDemoGuard(async (lease) => {
    setBusyLeaseId(lease.id);
    setActionError(null);
    try {
      await activateLease(lease.id);
      setToast({ title: "Lease activated", message: `${lease.guest?.name}'s lease is now active.` });
      await loadLeases();
    } catch {
      setActionError("Could not activate this lease. Please try again.");
    } finally {
      setBusyLeaseId(null);
    }
  });

  const handleTerminateConfirm = withDemoGuard(async () => {
    const lease = terminateTarget;
    setBusyLeaseId(lease.id);
    setActionError(null);
    try {
      await terminateLease(lease.id);
      setToast({ title: "Lease terminated", message: `${lease.guest?.name}'s lease has been terminated.` });
      setTerminateTarget(null);
      await loadLeases();
    } catch {
      setActionError("Could not terminate this lease. Please try again.");
    } finally {
      setBusyLeaseId(null);
    }
  });

  const handleRenewConfirm = withDemoGuard(async (newEndDate) => {
    const lease = renewTarget;
    setBusyLeaseId(lease.id);
    setActionError(null);
    try {
      await renewLease(lease.id, newEndDate);
      setToast({ title: "Lease renewed", message: `${lease.guest?.name}'s lease now ends ${formatDate(newEndDate)}.` });
      setRenewTarget(null);
      await loadLeases();
    } catch {
      setActionError("Could not renew this lease. Check the date and try again.");
    } finally {
      setBusyLeaseId(null);
    }
  });

  const handleOpenAgreement = withDemoGuard(async (lease) => {
    setAgreementLease(lease);
  });

  const handleSaveEdit = withDemoGuard(async (payload) => {
    const lease = editLease;
    setBusyLeaseId(lease.id);
    setActionError(null);
    try {
      await updateLease(lease.id, payload);
      setToast({ title: "Lease updated", message: `Changes to ${lease.guest?.name}'s lease were saved.` });
      setEditLease(null);
      await loadLeases();
    } catch {
      setActionError("Could not save changes. Please check the values and try again.");
    } finally {
      setBusyLeaseId(null);
    }
  });

  if (loading) {
    return (
      <div className="staff-page">
        <div className="skeleton lease-header-skeleton" />
        <div className="skeleton-card-grid">
          <div className="skeleton" />
          <div className="skeleton" />
          <div className="skeleton" />
          <div className="skeleton" />
        </div>
      </div>
    );
  }

  return (
    <div className="staff-page">
      {usingDemoData && (
        <div className="demo-notice">
          <Clock3 size={16} />
          <span>Backend is not connected, so demo lease data is being shown.</span>
        </div>
      )}

      <section className="page-heading lease-heading">
        <div>
          <span className="section-kicker">STAFF TOOLS</span>
          <h1>Lease Management</h1>
          <p>Review and manage leases across all properties.</p>
        </div>
      </section>

      <section className="summary-grid">
        <SummaryCard icon={<CheckCircle2 size={21} />} label="Active Leases" value={counts.active} accent="green" />
        <SummaryCard icon={<Clock3 size={21} />} label="Pending Leases" value={counts.pending} accent="gold" />
        <SummaryCard icon={<CalendarClock size={21} />} label="Expiring Soon" value={counts.expiring} accent="olive" />
        <SummaryCard icon={<FileWarning size={21} />} label="Expired Leases" value={counts.expired} accent="cream" />
      </section>

      {actionError && (
        <div className="demo-notice demo-notice--error">
          <span>{actionError}</span>
          <button className="icon-button" onClick={() => setActionError(null)} aria-label="Dismiss">
            <X size={14} />
          </button>
        </div>
      )}

      <section className="content-card">
        <div className="card-heading">
          <div>
            <span className="section-kicker">ALL LEASES</span>
            <h3>Lease directory</h3>
          </div>
        </div>

        <div className="filter-tabs">
          {FILTERS.map((filter) => (
            <button
              key={filter.key}
              className={`filter-tab ${activeFilter === filter.key ? "active" : ""}`}
              onClick={() => setActiveFilter(filter.key)}
            >
              {filter.label}
            </button>
          ))}
        </div>

        <div className="lease-table-wrapper">
          <table className="lease-table">
            <thead>
              <tr>
                {SORT_COLUMNS.map((column) => (
                  <th key={column.key}>
                    <button
                      type="button"
                      className="sortable-column-header"
                      onClick={() => handleSort(column.key)}
                    >
                      {column.label}
                      {sortKey === column.key ? (
                        sortDirection === "asc" ? (
                          <ArrowUp size={12} />
                        ) : (
                          <ArrowDown size={12} />
                        )
                      ) : (
                        <ArrowUpDown size={12} className="sortable-column-header-idle" />
                      )}
                    </button>
                  </th>
                ))}
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {visibleLeases.map((lease) => (
                <tr key={lease.id}>
                  <td>
                    <strong>{lease.guest?.name}</strong>
                    <small>{lease.guest?.email}</small>
                  </td>
                  <td>
                    <div className="residence-cell">
                      <Building2 size={14} />
                      <span>
                        {lease.property?.name} · Apt {lease.unit?.unit_number}
                      </span>
                    </div>
                  </td>
                  <td>{formatDate(lease.start_date)}</td>
                  <td>{formatDate(lease.end_date)}</td>
                  <td>{formatCurrency(lease.monthly_rate)}</td>
                  <td>
                    <StatusBadge status={lease.status} />
                  </td>
                  <td>{formatDate(lease.created_at?.slice(0, 10))}</td>
                  <td>
                    <div className="lease-table-actions">
                      <button className="text-button" onClick={() => setViewLease(lease)}>
                        View
                      </button>
                      <button className="text-button" onClick={() => handleOpenAgreement(lease)}>
                        Agreement
                      </button>
                      {(lease.status === "pending" || lease.status === "active") && (
                        <button className="text-button" onClick={() => setEditLease(lease)}>
                          Edit
                        </button>
                      )}
                      {lease.status === "pending" && (
                        <button
                          className="text-button"
                          disabled={busyLeaseId === lease.id}
                          onClick={() => handleActivate(lease)}
                        >
                          Activate
                        </button>
                      )}
                      {(lease.status === "active" || lease.status === "expired") && (
                        <button className="text-button" onClick={() => setRenewTarget(lease)}>
                          Renew
                        </button>
                      )}
                      {lease.status === "active" && (
                        <button
                          className="text-button text-button--danger"
                          onClick={() => setTerminateTarget(lease)}
                        >
                          Terminate
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {visibleLeases.length === 0 && (
                <tr>
                  <td colSpan={8} className="lease-table-empty">
                    No leases match this filter.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <LeaseEditDrawer
        open={Boolean(viewLease)}
        mode="view"
        lease={viewLease}
        onClose={() => setViewLease(null)}
      />
      <LeaseEditDrawer
        open={Boolean(editLease)}
        mode="edit"
        lease={editLease}
        saving={busyLeaseId === editLease?.id}
        error={actionError}
        onClose={() => setEditLease(null)}
        onSave={handleSaveEdit}
      />
      <AgreementDrawer
        open={Boolean(agreementLease)}
        lease={agreementLease}
        onClose={() => setAgreementLease(null)}
      />
      <RenewDialog
        open={Boolean(renewTarget)}
        lease={renewTarget}
        busy={busyLeaseId === renewTarget?.id}
        error={actionError}
        onConfirm={handleRenewConfirm}
        onCancel={() => setRenewTarget(null)}
      />
      <ConfirmDialog
        open={Boolean(terminateTarget)}
        title="Terminate this lease?"
        message={
          terminateTarget
            ? `This will end ${terminateTarget.guest?.name}'s lease at ${terminateTarget.property?.name} immediately. This cannot be undone.`
            : ""
        }
        confirmLabel="Terminate lease"
        busy={busyLeaseId === terminateTarget?.id}
        onConfirm={handleTerminateConfirm}
        onCancel={() => setTerminateTarget(null)}
      />

      <Toast
        open={Boolean(toast)}
        onClose={() => setToast(null)}
        title={toast?.title}
        message={toast?.message}
      />
    </div>
  );
}
