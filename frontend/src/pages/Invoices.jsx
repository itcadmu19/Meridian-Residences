import React, { useEffect, useMemo, useState } from "react";
import {
  ArrowDown,
  ArrowUp,
  ArrowUpDown,
  CalendarClock,
  CheckCircle2,
  Clock3,
  Download,
  FileSpreadsheet,
  FileWarning,
  Plus,
  Receipt,
  Sparkles,
} from "lucide-react";
import {
  downloadInvoicePdf,
  exportInvoicesPdf,
  extendDueDate,
  generateBatch,
  generateInvoice,
  getInsights,
  getInvoices,
  submitPayment,
  updatePaymentStatus,
} from "../services/invoiceService";
import { getStaffLeases } from "../services/staffLeaseService";
import { getLease } from "../services/leaseService";
import { useAuth } from "../context/AuthContext";
import SummaryCard from "../components/SummaryCard";
import StatusBadge from "../components/StatusBadge";
import Toast from "../components/Toast";

function residentOptionLabel(lease) {
  const statusLabel = lease.status.charAt(0).toUpperCase() + lease.status.slice(1);
  return `${lease.guest?.name || "Unknown resident"} — Apt ${lease.unit?.unit_number || "—"} (${statusLabel})`;
}

const RESIDENT_SORT_COLUMNS = [
  { key: "billing_period_start", label: "Billing period" },
  { key: "amount", label: "Amount" },
  { key: "due_date", label: "Due date" },
  { key: "payment_status", label: "Status" },
];
const STAFF_SORT_COLUMNS = [{ key: "guest.name", label: "Resident" }, ...RESIDENT_SORT_COLUMNS];

function getSortValue(invoice, key) {
  return key.split(".").reduce((value, part) => (value == null ? value : value[part]), invoice);
}

function compareInvoices(a, b, key) {
  const valueA = getSortValue(a, key);
  const valueB = getSortValue(b, key);
  if (valueA == null && valueB == null) return 0;
  if (valueA == null) return -1;
  if (valueB == null) return 1;
  if (typeof valueA === "number" && typeof valueB === "number") return valueA - valueB;
  return String(valueA).localeCompare(String(valueB));
}

const FILTERS = [
  { key: "all", label: "All" },
  { key: "pending", label: "Pending" },
  { key: "payment_submitted", label: "Awaiting approval" },
  { key: "due_extended", label: "Due extended" },
  { key: "paid", label: "Paid" },
  { key: "overdue", label: "Overdue" },
];

const DEMO_INVOICES = [
  {
    id: "invoice-demo-001",
    lease_id: "lease-demo-001",
    billing_period_start: "2026-09-01",
    billing_period_end: "2026-09-30",
    amount: 45000,
    due_date: "2026-09-25",
    payment_status: "pending",
  },
  {
    id: "invoice-demo-002",
    lease_id: "lease-demo-001",
    billing_period_start: "2026-08-01",
    billing_period_end: "2026-08-31",
    amount: 45000,
    due_date: "2026-08-25",
    payment_status: "paid",
    paid_at: "2026-08-20T00:00:00Z",
  },
];

function formatCurrency(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

function toMonthInput(dateString) {
  // "YYYY-MM-DD" -> "YYYY-MM", matching <input type="month">'s value format.
  return dateString ? dateString.slice(0, 7) : "";
}

function formatDate(value) {
  if (!value) return "—";
  return new Date(`${value}T00:00:00`).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function triggerBlobDownload(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

function downloadCsv(invoices) {
  const headers = [
    "Invoice ID",
    "Lease ID",
    "Resident",
    "Unit",
    "Billing Period Start",
    "Billing Period End",
    "Amount",
    "Due Date",
    "Payment Status",
  ];
  const rows = invoices.map((invoice) => [
    invoice.id,
    invoice.lease_id,
    invoice.guest?.name || "",
    invoice.unit?.unit_number || "",
    invoice.billing_period_start,
    invoice.billing_period_end,
    invoice.amount,
    invoice.due_date,
    invoice.payment_status,
  ]);
  const csv = [headers, ...rows]
    .map((row) => row.map((value) => `"${String(value ?? "").replaceAll('"', '""')}"`).join(","))
    .join("\n");
  triggerBlobDownload(new Blob([csv], { type: "text/csv;charset=utf-8" }), "meridian-invoice-portfolio.csv");
}

function PayInvoiceDialog({ open, invoice, busy, error, onConfirm, onCancel }) {
  if (!open || !invoice) return null;

  function handleSubmit(event) {
    event.preventDefault();
    onConfirm();
  }

  return (
    <div className="confirm-dialog-overlay" role="presentation" onClick={onCancel}>
      <div className="confirm-dialog" role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
        <div className="confirm-dialog-icon">
          <Receipt size={20} />
        </div>
        <h3>Pay invoice</h3>
        <form className="drawer-form" onSubmit={handleSubmit}>
          <div className="payment-summary-row">
            <span>Amount due</span>
            <strong>{formatCurrency(invoice.amount)}</strong>
          </div>
          <label>
            Dummy card number
            <input type="text" placeholder="4242 4242 4242 4242" required />
          </label>
          <div className="drawer-form-grid-2">
            <label>
              Expiry
              <input type="text" placeholder="12/30" required />
            </label>
            <label>
              CVV
              <input type="text" placeholder="123" required />
            </label>
          </div>
          <p className="payment-helper">Demo gateway only - no real payment is processed.</p>
          {error && <div className="demo-notice demo-notice--error">{error}</div>}
          <div className="confirm-dialog-actions">
            <button type="button" className="secondary-button" onClick={onCancel} disabled={busy}>
              Cancel
            </button>
            <button type="submit" className="primary-button" disabled={busy}>
              {busy ? "Submitting…" : "Pay & notify staff"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function ExtendDueDateDialog({ open, invoice, busy, error, onConfirm, onCancel }) {
  const [newDueDate, setNewDueDate] = useState("");

  useEffect(() => {
    if (invoice) setNewDueDate(invoice.due_date);
  }, [invoice]);

  if (!open || !invoice) return null;

  return (
    <div className="confirm-dialog-overlay" role="presentation" onClick={onCancel}>
      <div className="confirm-dialog" role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
        <div className="confirm-dialog-icon">
          <CalendarClock size={20} />
        </div>
        <h3>Extend due date</h3>
        <p>
          Current due date is {formatDate(invoice.due_date)}. The billing period will end the day
          before the new due date.
        </p>
        <label className="renew-date-field">
          New due date
          <input
            type="date"
            value={newDueDate}
            min={invoice.due_date}
            onChange={(event) => setNewDueDate(event.target.value)}
          />
        </label>
        {error && <div className="demo-notice demo-notice--error">{error}</div>}
        <div className="confirm-dialog-actions">
          <button className="secondary-button" onClick={onCancel} disabled={busy}>
            Cancel
          </button>
          <button
            className="primary-button"
            onClick={() => onConfirm(newDueDate)}
            disabled={busy || !newDueDate}
          >
            {busy ? "Updating…" : "Extend"}
          </button>
        </div>
      </div>
    </div>
  );
}

function GenerateInvoiceDialog({ open, busy, error, minMonth, maxMonth, onConfirm, onCancel }) {
  const [month, setMonth] = useState("");

  useEffect(() => {
    if (open) {
      const today = new Date();
      const currentMonth = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}`;
      // Default to the current month, clamped into the lease's own window
      // so the dialog never opens on a pre-selected, already-invalid month.
      const clamped = minMonth && currentMonth < minMonth ? minMonth : maxMonth && currentMonth > maxMonth ? maxMonth : currentMonth;
      setMonth(clamped);
    }
  }, [open, minMonth, maxMonth]);

  if (!open) return null;

  const outOfRange = Boolean(month) && ((minMonth && month < minMonth) || (maxMonth && month > maxMonth));

  function handleSubmit(event) {
    event.preventDefault();
    if (!month || outOfRange) return;
    onConfirm(month);
  }

  return (
    <div className="confirm-dialog-overlay" role="presentation" onClick={onCancel}>
      <div className="confirm-dialog" role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
        <div className="confirm-dialog-icon">
          <Plus size={20} />
        </div>
        <h3>Generate invoice</h3>
        <form className="drawer-form" onSubmit={handleSubmit}>
          <label>
            Select invoice month
            <input
              type="month"
              value={month}
              min={minMonth || undefined}
              max={maxMonth || undefined}
              onChange={(event) => setMonth(event.target.value)}
              required
            />
          </label>
          <p className="payment-helper">
            Covers the full month you pick; payment is due on the 10th of the following month.
            {minMonth && maxMonth && ` Your lease only covers ${minMonth} through ${maxMonth}.`}
          </p>
          {outOfRange && (
            <div className="demo-notice demo-notice--error">
              Pick a month within your lease term ({minMonth} to {maxMonth}).
            </div>
          )}
          {error && <div className="demo-notice demo-notice--error">{error}</div>}
          <div className="confirm-dialog-actions">
            <button type="button" className="secondary-button" onClick={onCancel} disabled={busy}>
              Cancel
            </button>
            <button type="submit" className="primary-button" disabled={busy || !month || outOfRange}>
              {busy ? "Generating…" : "Generate invoice"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default function Invoices() {
  const { currentUser } = useAuth();
  const isStaff = currentUser?.role === "staff" || currentUser?.role === "admin";

  const [invoices, setInvoices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [usingDemoData, setUsingDemoData] = useState(false);
  const [activeFilter, setActiveFilter] = useState("all");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [residentLeases, setResidentLeases] = useState([]);
  const [selectedResidentLeaseId, setSelectedResidentLeaseId] = useState("");
  // Resident-only: their own lease's start/end dates, used to restrict which
  // months "Generate invoice" allows - not fetched at all for staff.
  const [ownLease, setOwnLease] = useState(null);
  // Matches the backend's own default order (due_date desc) so nothing
  // visually jumps on load - clicking a header re-sorts from there.
  const [sortKey, setSortKey] = useState("due_date");
  const [sortDirection, setSortDirection] = useState("desc");
  const [busyInvoiceId, setBusyInvoiceId] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [processingBatch, setProcessingBatch] = useState(false);
  const [selectedIds, setSelectedIds] = useState([]);
  const [invoiceToPay, setInvoiceToPay] = useState(null);
  const [invoiceToExtend, setInvoiceToExtend] = useState(null);
  const [isGenerateOpen, setIsGenerateOpen] = useState(false);
  const [insights, setInsights] = useState(null);
  const [insightsError, setInsightsError] = useState(null);
  const [toast, setToast] = useState(null);
  const [actionError, setActionError] = useState(null);

  async function loadInvoices() {
    try {
      const data = await getInvoices({
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        lease_id: selectedResidentLeaseId || undefined,
      });
      setInvoices(Array.isArray(data) ? data : []);
      setUsingDemoData(false);
    } catch {
      setInvoices(DEMO_INVOICES);
      setUsingDemoData(true);
    } finally {
      setLoading(false);
    }
  }

  // Staff-only: the resident picker's own options - fetched once, not
  // affected by which resident is currently selected.
  useEffect(() => {
    if (!isStaff) return undefined;

    let mounted = true;
    getStaffLeases()
      .then((data) => {
        if (mounted) setResidentLeases(Array.isArray(data) ? data : []);
      })
      .catch(() => {
        // ignore - the picker just won't render, same graceful-degrade
        // pattern as the rest of this page's demo-data fallbacks
      });

    return () => {
      mounted = false;
    };
  }, [isStaff]);

  // Resident-only: load their own lease's start/end dates once so the
  // "Generate invoice" dialog can be restricted to the lease term.
  useEffect(() => {
    if (isStaff) return undefined;
    const leaseId = localStorage.getItem("selected_lease_id");
    if (!leaseId) return undefined;

    let mounted = true;
    getLease(leaseId)
      .then((data) => {
        if (mounted) setOwnLease(data);
      })
      .catch(() => {
        // ignore - the picker just won't be date-restricted client-side;
        // the backend still enforces the lease-term check either way.
      });

    return () => {
      mounted = false;
    };
  }, [isStaff]);

  async function loadInsights() {
    try {
      const data = await getInsights({ lease_id: selectedResidentLeaseId || undefined });
      setInsights(data);
      setInsightsError(null);
    } catch (err) {
      setInsights(null);
      // Surfaced in the UI (not just swallowed) so a real failure is
      // visible instead of the card just silently not appearing.
      const detail = err?.response?.status
        ? `HTTP ${err.response.status}${err.response.data?.message ? `: ${err.response.data.message}` : ""}`
        : err?.message || "network error";
      setInsightsError(`Could not load AI insights (${detail}).`);
      // eslint-disable-next-line no-console
      console.error("Failed to load invoice insights:", err);
    }
  }

  useEffect(() => {
    setLoading(true);
    setSelectedIds([]);
    loadInvoices();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dateFrom, dateTo, selectedResidentLeaseId]);

  useEffect(() => {
    if (!usingDemoData) loadInsights();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [usingDemoData, invoices.length, selectedResidentLeaseId]);

  const counts = useMemo(
    () => ({
      pending: invoices.filter((i) => i.payment_status === "pending").length,
      paid: invoices.filter((i) => i.payment_status === "paid").length,
      overdue: invoices.filter((i) => i.payment_status === "overdue").length,
    }),
    [invoices]
  );

  const totalOutstanding = invoices
    .filter((i) => ["pending", "payment_submitted", "overdue", "due_extended"].includes(i.payment_status))
    .reduce((total, i) => total + Number(i.amount), 0);
  const nextInvoice = invoices
    .filter((i) => i.payment_status === "pending")
    .sort((a, b) => a.due_date.localeCompare(b.due_date))[0];
  const lastPayment = invoices
    .filter((i) => i.payment_status === "paid")
    .sort((a, b) => (b.paid_at || "").localeCompare(a.paid_at || ""))[0];
  const totalCollected = invoices
    .filter((i) => i.payment_status === "paid")
    .reduce((total, i) => total + Number(i.amount), 0);
  const overdueAmount = invoices
    .filter((i) => i.payment_status === "overdue")
    .reduce((total, i) => total + Number(i.amount), 0);
  const collectionRate = invoices.length
    ? Math.round((invoices.filter((i) => i.payment_status === "paid").length / invoices.length) * 100)
    : 0;

  const selectedResident = selectedResidentLeaseId
    ? residentLeases.find((lease) => lease.id === selectedResidentLeaseId)
    : null;

  const generateMinMonth = toMonthInput(ownLease?.start_date);
  const generateMaxMonth = toMonthInput(ownLease?.end_date);

  const visibleInvoices = useMemo(() => {
    const filtered = activeFilter === "all" ? invoices : invoices.filter((i) => i.payment_status === activeFilter);
    const sorted = [...filtered].sort((a, b) => compareInvoices(a, b, sortKey));
    return sortDirection === "desc" ? sorted.reverse() : sorted;
  }, [invoices, activeFilter, sortKey, sortDirection]);

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

  function toggleSelection(invoiceId) {
    setSelectedIds((current) =>
      current.includes(invoiceId) ? current.filter((id) => id !== invoiceId) : [...current, invoiceId]
    );
  }

  const handlePayConfirm = withDemoGuard(async () => {
    const invoice = invoiceToPay;
    setBusyInvoiceId(invoice.id);
    setActionError(null);
    try {
      const updated = await submitPayment(invoice.id);
      setInvoices((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
      setInvoiceToPay(null);
      setToast({ title: "Payment submitted", message: "Staff will approve it before it's marked paid." });
    } catch {
      setActionError("Could not submit payment. Please try again.");
    } finally {
      setBusyInvoiceId(null);
    }
  });

  const handleExtendConfirm = withDemoGuard(async (newDueDate) => {
    const invoice = invoiceToExtend;
    setBusyInvoiceId(invoice.id);
    setActionError(null);
    try {
      const updated = await extendDueDate(invoice.id, newDueDate);
      setInvoices((prev) => prev.map((item) => (item.id === updated.id ? updated : item)));
      setInvoiceToExtend(null);
      setToast({ title: "Due date extended", message: `New due date: ${formatDate(newDueDate)}.` });
    } catch {
      setActionError("Could not extend the due date. Please try again.");
    } finally {
      setBusyInvoiceId(null);
    }
  });

  const handleBulkUpdate = withDemoGuard(async (paymentStatus) => {
    if (!selectedIds.length) {
      setActionError("Select at least one invoice first.");
      return;
    }
    setProcessingBatch(true);
    setActionError(null);
    try {
      await Promise.all(selectedIds.map((id) => updatePaymentStatus(id, paymentStatus)));
      setToast({ title: "Invoices updated", message: `${selectedIds.length} invoice(s) marked ${paymentStatus}.` });
      setSelectedIds([]);
      await loadInvoices();
    } catch {
      setActionError("Could not update the selected invoices.");
    } finally {
      setProcessingBatch(false);
    }
  });

  const handleGenerateBatch = withDemoGuard(async () => {
    setGenerating(true);
    setActionError(null);
    const today = new Date();
    const start = new Date(today.getFullYear(), today.getMonth(), 1);
    const iso = (d) => d.toISOString().slice(0, 10);
    try {
      // billing_period_end/due_date are derived server-side (full calendar
      // month, due the 10th of the following month) - see
      // invoice_service._billing_period_bounds. Only billing_period_start
      // is meaningful here.
      const result = await generateBatch({ billing_period_start: iso(start) });
      setToast({
        title: "Invoices generated",
        message: `${result.generated_count} new, ${result.duplicate_count} already existed.`,
      });
      await loadInvoices();
    } catch {
      setActionError("Could not generate invoices. Please try again.");
    } finally {
      setGenerating(false);
    }
  });

  const handleGenerateInvoice = withDemoGuard(async (month) => {
    const leaseId = localStorage.getItem("selected_lease_id");
    if (!leaseId) {
      setActionError("No active lease found for your account.");
      return;
    }
    // Same check the backend enforces (billing period must fall within the
    // lease term) done client-side first, so an out-of-range pick gets an
    // immediate, clear answer instead of a round trip.
    if ((generateMinMonth && month < generateMinMonth) || (generateMaxMonth && month > generateMaxMonth)) {
      setActionError(
        `Your lease runs ${generateMinMonth} to ${generateMaxMonth} - pick a month within that range.`
      );
      return;
    }

    const [year, monthNumber] = month.split("-").map(Number);
    const start = new Date(year, monthNumber - 1, 1);
    const iso = (d) => d.toISOString().slice(0, 10);
    const startIso = iso(start);

    // Same check the backend enforces (one invoice per lease per calendar
    // month) done client-side first, so a duplicate attempt gets an
    // immediate, clear answer instead of a round trip.
    const alreadyExists = invoices.some((invoice) => invoice.billing_period_start === startIso);
    if (alreadyExists) {
      setActionError(`An invoice for ${month} has already been generated.`);
      return;
    }

    setGenerating(true);
    setActionError(null);
    try {
      const result = await generateInvoice({ lease_id: leaseId, billing_period_start: startIso });
      const wasExisting = result.message === "Existing invoice returned";
      setToast({
        title: wasExisting ? "Invoice already existed" : "Invoice generated",
        message: wasExisting
          ? `An invoice for ${month} was already on file.`
          : `Invoice for ${month} is ready.`,
      });
      setIsGenerateOpen(false);
      setInvoices((prev) => [result.data, ...prev.filter((item) => item.id !== result.data.id)]);
    } catch {
      setActionError("Could not generate the invoice. Please try again.");
    } finally {
      setGenerating(false);
    }
  });

  async function handleDownloadPdf(invoiceId) {
    try {
      const blob = await downloadInvoicePdf(invoiceId);
      triggerBlobDownload(blob, `invoice-${invoiceId.slice(0, 8)}.pdf`);
    } catch {
      setActionError("Could not download the invoice PDF.");
    }
  }

  async function handleExportPdf() {
    setExporting(true);
    try {
      const blob = await exportInvoicesPdf({
        payment_status: activeFilter === "all" ? undefined : activeFilter,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
        lease_id: selectedResidentLeaseId || undefined,
      });
      triggerBlobDownload(blob, "meridian-invoice-statement.pdf");
    } catch {
      setActionError("Could not export invoices as PDF.");
    } finally {
      setExporting(false);
    }
  }

  function handleExportCsv() {
    downloadCsv(visibleInvoices);
    setToast({ title: "CSV exported", message: `${visibleInvoices.length} invoice(s) exported.` });
  }

  if (loading) {
    return (
      <div className="dashboard-skeleton">
        <div className="skeleton lease-header-skeleton" />
        <div className="skeleton-card-grid">
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
          <span>Backend is not connected, so demo invoice data is being shown.</span>
        </div>
      )}

      <section className="page-heading lease-heading">
        <div>
          <span className="section-kicker">RESIDENT SERVICES</span>
          <h1>Invoices</h1>
          <p>
            {isStaff
              ? "Manage recurring billing across all properties."
              : "View your recurring billing and payment status."}
          </p>
        </div>
        {isStaff ? (
          <button className="primary-button" onClick={handleGenerateBatch} disabled={generating}>
            <Receipt size={17} />
            {generating ? "Generating…" : "Generate monthly batch"}
          </button>
        ) : (
          <button
            className="primary-button"
            onClick={() => {
              setActionError(null);
              setIsGenerateOpen(true);
            }}
            disabled={usingDemoData}
          >
            <Plus size={17} />
            Generate invoice
          </button>
        )}
      </section>

      {isStaff && residentLeases.length > 0 && (
        <section className="lease-switcher">
          <label htmlFor="invoice-resident-select">Resident:</label>
          <select
            id="invoice-resident-select"
            value={selectedResidentLeaseId}
            onChange={(event) => setSelectedResidentLeaseId(event.target.value)}
          >
            <option value="">All residents</option>
            {residentLeases.map((lease) => (
              <option key={lease.id} value={lease.id}>
                {residentOptionLabel(lease)}
              </option>
            ))}
          </select>
          {selectedResidentLeaseId && (
            <button className="text-button" onClick={() => setSelectedResidentLeaseId("")}>
              Clear
            </button>
          )}
        </section>
      )}

      <section className="summary-grid">
        <SummaryCard icon={<Clock3 size={21} />} label="Total outstanding" value={formatCurrency(totalOutstanding)} accent="gold" />
        <SummaryCard
          icon={<CalendarClock size={21} />}
          label="Next due"
          value={nextInvoice ? formatDate(nextInvoice.due_date) : "No pending payment"}
          accent="olive"
        />
        <SummaryCard
          icon={<CheckCircle2 size={21} />}
          label="Last payment"
          value={lastPayment ? formatCurrency(lastPayment.amount) : "No payment recorded"}
          accent="green"
        />
      </section>

      {isStaff && (
        <section className="summary-grid">
          <SummaryCard icon={<CheckCircle2 size={21} />} label="Total collected" value={formatCurrency(totalCollected)} accent="green" />
          <SummaryCard icon={<FileWarning size={21} />} label="Overdue exposure" value={formatCurrency(overdueAmount)} accent="cream" />
          <SummaryCard icon={<Receipt size={21} />} label="Collection rate" value={`${collectionRate}%`} accent="gold" />
        </section>
      )}

      {insightsError && !usingDemoData && (
        <div className="demo-notice demo-notice--error">
          <span>{insightsError}</span>
        </div>
      )}

      {insights && (
        <section className="ai-insights-section">
          <div className="content-card ai-insights-card">
            <div className="card-heading">
              <div>
                <span className="section-kicker">AI PAYMENT INSIGHT</span>
                <h3>
                  {isStaff
                    ? selectedResident
                      ? `${selectedResident.guest?.name}'s billing insight`
                      : "Portfolio billing insight"
                    : "Your payment insight"}
                </h3>
              </div>
              <div className="ai-insights-icon">
                <Sparkles size={18} />
              </div>
            </div>
            <div className={`insight-risk-badge insight-risk-badge--${insights.risk_level}`}>
              {insights.risk_level.toUpperCase()} RISK
            </div>
            <p className="insight-text">{insights.insight}</p>
          </div>
        </section>
      )}

      {actionError && <div className="demo-notice demo-notice--error">{actionError}</div>}

      <section className="content-card">
        <div className="card-heading">
          <div>
            <span className="section-kicker">
              {isStaff ? (selectedResident ? "RESIDENT INVOICES" : "ALL INVOICES") : "YOUR INVOICES"}
            </span>
            <h3>{isStaff && selectedResident ? `${selectedResident.guest?.name}'s invoice history` : "Invoice history"}</h3>
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

        <div className="invoice-toolbar">
          <div className="invoice-toolbar-dates">
            <label>
              From
              <input type="date" value={dateFrom} onChange={(event) => setDateFrom(event.target.value)} />
            </label>
            <label>
              To
              <input type="date" value={dateTo} onChange={(event) => setDateTo(event.target.value)} />
            </label>
          </div>
          <div className="invoice-toolbar-actions">
            {isStaff && (
              <>
                <button
                  className="secondary-button"
                  onClick={() => handleBulkUpdate("overdue")}
                  disabled={processingBatch}
                >
                  {processingBatch ? "Processing…" : "Mark selected overdue"}
                </button>
                <button
                  className="primary-button"
                  onClick={() => handleBulkUpdate("paid")}
                  disabled={processingBatch}
                >
                  <CheckCircle2 size={16} />
                  {processingBatch ? "Processing…" : "Approve selected"}
                </button>
                <button className="secondary-button" onClick={handleExportCsv}>
                  <FileSpreadsheet size={16} />
                  Export CSV
                </button>
              </>
            )}
            <button className="secondary-button" onClick={handleExportPdf} disabled={exporting}>
              <Download size={16} />
              {exporting ? "Exporting…" : "Export PDF"}
            </button>
          </div>
        </div>

        <div className="lease-table-wrapper">
          <table className="lease-table">
            <thead>
              <tr>
                {isStaff && <th></th>}
                {(isStaff ? STAFF_SORT_COLUMNS : RESIDENT_SORT_COLUMNS).map((column) => (
                  <th key={column.key}>
                    <button type="button" className="sortable-column-header" onClick={() => handleSort(column.key)}>
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
              {visibleInvoices.map((invoice) => {
                const canSelect = isStaff && ["pending", "payment_submitted"].includes(invoice.payment_status);
                const canPay = !isStaff && ["pending", "overdue", "due_extended"].includes(invoice.payment_status);
                return (
                  <tr key={invoice.id}>
                    {isStaff && (
                      <td>
                        <input
                          type="checkbox"
                          checked={selectedIds.includes(invoice.id)}
                          disabled={!canSelect}
                          onChange={() => toggleSelection(invoice.id)}
                        />
                      </td>
                    )}
                    {isStaff && (
                      <td>
                        <strong>{invoice.guest?.name || "—"}</strong>
                        <small>Apt {invoice.unit?.unit_number || "—"}</small>
                      </td>
                    )}
                    <td>
                      {formatDate(invoice.billing_period_start)} – {formatDate(invoice.billing_period_end)}
                    </td>
                    <td>{formatCurrency(invoice.amount)}</td>
                    <td>{formatDate(invoice.due_date)}</td>
                    <td>
                      <StatusBadge status={invoice.payment_status} />
                    </td>
                    <td>
                      <div className="lease-table-actions">
                        {canPay && (
                          <button className="text-button" onClick={() => setInvoiceToPay(invoice)}>
                            Pay
                          </button>
                        )}
                        {invoice.payment_status === "payment_submitted" && (
                          <span className="awaiting-approval-tag">Awaiting approval</span>
                        )}
                        {isStaff && invoice.payment_status !== "paid" && invoice.payment_status !== "cancelled" && (
                          <button className="text-button" onClick={() => setInvoiceToExtend(invoice)}>
                            Extend due date
                          </button>
                        )}
                        <button
                          className="text-button"
                          onClick={() => handleDownloadPdf(invoice.id)}
                          title="Download invoice PDF"
                        >
                          <Download size={14} />
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
              {visibleInvoices.length === 0 && (
                <tr>
                  <td colSpan={isStaff ? 7 : 5} className="lease-table-empty">
                    {isStaff && selectedResident
                      ? `${selectedResident.guest?.name} has no invoices in this view yet.`
                      : "No invoices in this view yet."}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <PayInvoiceDialog
        open={Boolean(invoiceToPay)}
        invoice={invoiceToPay}
        busy={busyInvoiceId === invoiceToPay?.id}
        error={actionError}
        onConfirm={handlePayConfirm}
        onCancel={() => setInvoiceToPay(null)}
      />
      <ExtendDueDateDialog
        open={Boolean(invoiceToExtend)}
        invoice={invoiceToExtend}
        busy={busyInvoiceId === invoiceToExtend?.id}
        error={actionError}
        onConfirm={handleExtendConfirm}
        onCancel={() => setInvoiceToExtend(null)}
      />
      <GenerateInvoiceDialog
        open={isGenerateOpen}
        busy={generating}
        error={actionError}
        minMonth={generateMinMonth}
        maxMonth={generateMaxMonth}
        onConfirm={handleGenerateInvoice}
        onCancel={() => setIsGenerateOpen(false)}
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
