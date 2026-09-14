import React, { useEffect, useMemo, useState } from "react";
import { CalendarClock, CheckCircle2, Download, FileSpreadsheet, Plus, Sparkles, Wallet } from "lucide-react";
import PageHeader from "../components/PageHeader.jsx";
import Card from "../components/Card.jsx";
import StatCard from "../components/StatCard.jsx";
import Button from "../components/Button.jsx";
import SecondaryButton from "../components/SecondaryButton.jsx";
import Modal from "../components/Modal.jsx";
import Input from "../components/Input.jsx";
import Loading from "../components/Loading.jsx";
import ErrorMessage from "../components/ErrorMessage.jsx";
import EmptyState from "../components/EmptyState.jsx";
import InvoiceCard from "../components/InvoiceCard.jsx";
import invoiceService from "../services/invoiceService.js";
import { useAuth } from "../context/AuthContext.jsx";

const FILTERS = [
  { key: "all", label: "All" },
  { key: "pending", label: "Pending" },
  { key: "payment_submitted", label: "Awaiting approval" },
  { key: "paid", label: "Paid" },
  { key: "overdue", label: "Overdue" },
];

function getDefaultBillingDates() {
  const today = new Date();
  const start = new Date(today.getFullYear(), today.getMonth(), 1);
  const due = new Date(start);
  due.setDate(due.getDate() + 10);
  const toIsoDate = (date) => date.toISOString().slice(0, 10);
  return {
    billing_month: toIsoDate(start).slice(0, 7),
    billing_period_start: toIsoDate(start),
    billing_period_end: toIsoDate(new Date(due.getTime() - 86400000)),
    due_date: toIsoDate(due),
  };
}

function getBillingDatesForMonth(month) {
  const [year, monthNumber] = month.split("-").map(Number);
  const start = new Date(year, monthNumber - 1, 1);
  const due = new Date(start);
  due.setDate(due.getDate() + 10);
  const toIsoDate = (date) => date.toISOString().slice(0, 10);
  return {
    billing_month: month,
    billing_period_start: toIsoDate(start),
    billing_period_end: toIsoDate(new Date(due.getTime() - 86400000)),
    due_date: toIsoDate(due),
  };
}

function formatCurrency(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(Number(value));
}

function formatDate(value) {
  if (!value) return "—";
  return new Date(`${value}T00:00:00`).toLocaleDateString(undefined, {
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
  const headers = ["Invoice ID", "Lease ID", "Billing Period Start", "Billing Period End", "Amount", "Due Date", "Payment Status"];
  const rows = invoices.map((invoice) => [
    invoice.id,
    invoice.lease_id,
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

export default function Invoices() {
  const { currentUser } = useAuth();
  const isStaff = ["staff", "admin"].includes(currentUser?.role);
  const [invoices, setInvoices] = useState([]);
  const [activeFilter, setActiveFilter] = useState("all");
  const [dateFrom, setDateFrom] = useState("");
  const [dateTo, setDateTo] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isGenerateOpen, setIsGenerateOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [isProcessingBatch, setIsProcessingBatch] = useState(false);
  const [selectedInvoiceIds, setSelectedInvoiceIds] = useState([]);
  const [invoiceToPay, setInvoiceToPay] = useState(null);
  const [invoiceToExtend, setInvoiceToExtend] = useState(null);
  const [extendedDueDate, setExtendedDueDate] = useState("");
  const [isPaying, setIsPaying] = useState(false);
  const [statusMessage, setStatusMessage] = useState(null);
  const [formError, setFormError] = useState(null);
  const [insights, setInsights] = useState(null);
  const [isInsightsLoading, setIsInsightsLoading] = useState(false);
  const [generateForm, setGenerateForm] = useState(getDefaultBillingDates);

  async function loadInvoices() {
    setIsLoading(true);
    setError(null);
    try {
      const response = await invoiceService.getInvoices({
        page: 1,
        page_size: 100,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
      });
      setInvoices(response.data || []);
    } catch (err) {
      setError(err.message || "Unable to load your invoices.");
    } finally {
      setIsLoading(false);
    }
  }

  async function loadInsights(leaseId) {
    if (!isStaff && !leaseId) return;
    setIsInsightsLoading(true);
    try {
      const response = await invoiceService.getInsights({ lease_id: leaseId });
      setInsights(response.data);
    } catch {
      setInsights(null);
    } finally {
      setIsInsightsLoading(false);
    }
  }

  useEffect(() => {
    loadInvoices();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dateFrom, dateTo]);

  useEffect(() => {
    if (invoices.length && (isStaff || invoices[0]?.lease_id)) {
      loadInsights(isStaff ? undefined : invoices[0].lease_id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [invoices.length, isStaff]);

  async function handleGenerate(event) {
    event.preventDefault();
    const leaseId = invoices[0]?.lease_id;
    if (!leaseId) {
      setFormError("An active lease is required before an invoice can be generated.");
      return;
    }

    const existingInvoice = invoices.find(
      (invoice) => invoice.billing_period_start === generateForm.billing_period_start
    );
    if (existingInvoice) {
      setFormError("This month's invoice has already been generated and is already in the invoice list.");
      return;
    }

    setIsSubmitting(true);
    setFormError(null);
    try {
      const response = await invoiceService.generateInvoice({
        lease_id: leaseId,
        billing_period_start: generateForm.billing_period_start,
        billing_period_end: generateForm.billing_period_end,
        due_date: generateForm.due_date,
      });
      setInvoices((currentInvoices) => [
        response.data,
        ...currentInvoices.filter((invoice) => invoice.id !== response.data.id),
      ]);
      setIsGenerateOpen(false);
    } catch (err) {
      setFormError(err.message || "Unable to generate the invoice.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleGenerateBatch() {
    setIsProcessingBatch(true);
    setStatusMessage(null);
    try {
      const response = await invoiceService.generateBatch(generateForm);
      const monthLabel = new Date(`${generateForm.billing_period_start}T00:00:00`).toLocaleDateString(undefined, {
        month: "long",
        year: "numeric",
      });
      setStatusMessage(response.data.generated_count
        ? `${response.data.generated_count} invoice(s) generated for ${monthLabel}; ${response.data.duplicate_count} existing invoice(s) skipped.`
        : `${monthLabel} is already generated for all active leases. No duplicate invoices were created.`);
      await loadInvoices();
    } catch (err) {
      setError(err.message || "Unable to generate the invoice batch.");
    } finally {
      setIsProcessingBatch(false);
    }
  }

  function toggleInvoiceSelection(invoiceId) {
    setSelectedInvoiceIds((current) => current.includes(invoiceId)
      ? current.filter((id) => id !== invoiceId)
      : [...current, invoiceId]);
  }

  async function updateSelectedInvoices(paymentStatus) {
    if (!selectedInvoiceIds.length) {
      setStatusMessage("Select at least one invoice first.");
      return;
    }
    setIsProcessingBatch(true);
    setStatusMessage(null);
    try {
      await Promise.all(selectedInvoiceIds.map((invoiceId) => invoiceService.updatePaymentStatus(invoiceId, paymentStatus)));
      setStatusMessage(`${selectedInvoiceIds.length} invoice(s) marked as ${paymentStatus}.`);
      setSelectedInvoiceIds([]);
      await loadInvoices();
    } catch (err) {
      setError(err.message || "Unable to update overdue invoices.");
    } finally {
      setIsProcessingBatch(false);
    }
  }

  async function handlePaymentSubmit(event) {
    event.preventDefault();
    if (!invoiceToPay) return;
    setIsPaying(true);
    setError(null);
    try {
      const response = await invoiceService.submitPayment(invoiceToPay.id);
      setInvoices((current) => current.map((invoice) => invoice.id === response.data.id ? response.data : invoice));
      setInvoiceToPay(null);
      setStatusMessage("Payment submitted. Staff will approve it before it is marked paid.");
    } catch (err) {
      setError(err.message || "Unable to submit payment.");
    } finally {
      setIsPaying(false);
    }
  }

  function openExtendDueDate(invoice) {
    setInvoiceToExtend(invoice);
    setExtendedDueDate(invoice.due_date);
    setFormError(null);
  }

  async function handleExtendDueDate(event) {
    event.preventDefault();
    if (!invoiceToExtend || extendedDueDate <= invoiceToExtend.due_date) {
      setFormError("The extended due date must be later than the current due date.");
      return;
    }
    setIsSubmitting(true);
    setFormError(null);
    try {
      const response = await invoiceService.extendDueDate(invoiceToExtend.id, extendedDueDate);
      setInvoices((current) => current.map((invoice) => invoice.id === response.data.id ? response.data : invoice));
      setInvoiceToExtend(null);
      setStatusMessage("Due date extended. The billing period end date was updated automatically.");
    } catch (err) {
      setFormError(err.message || "Unable to extend the due date.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleDownloadInvoice(invoiceId) {
    try {
      const blob = await invoiceService.downloadInvoicePdf(invoiceId);
      triggerBlobDownload(blob, `invoice-${invoiceId.slice(0, 8)}.pdf`);
    } catch (err) {
      setError(err.message || "Unable to download the invoice PDF.");
    }
  }

  async function handleExportPdf() {
    setIsExporting(true);
    try {
      const blob = await invoiceService.exportInvoicesPdf({
        payment_status: activeFilter === "all" ? undefined : activeFilter,
        date_from: dateFrom || undefined,
        date_to: dateTo || undefined,
      });
      triggerBlobDownload(blob, "meridian-invoice-statement.pdf");
    } catch (err) {
      setError(err.message || "Unable to export invoices as PDF.");
    } finally {
      setIsExporting(false);
    }
  }

  function handleExportCsv() {
    downloadCsv(filteredInvoices);
    setStatusMessage(`${filteredInvoices.length} invoice(s) exported as CSV.`);
  }

  const filteredInvoices = useMemo(() => {
    if (activeFilter === "all") return invoices;
    return invoices.filter((invoice) => invoice.payment_status === activeFilter);
  }, [activeFilter, invoices]);

  const totalOutstanding = invoices
    .filter((invoice) => ["pending", "payment_submitted", "overdue"].includes(invoice.payment_status))
    .reduce((total, invoice) => total + Number(invoice.amount), 0);
  const nextInvoice = invoices
    .filter((invoice) => invoice.payment_status === "pending")
    .sort((a, b) => a.due_date.localeCompare(b.due_date))[0];
  const lastPayment = invoices
    .filter((invoice) => invoice.payment_status === "paid")
    .sort((a, b) => (b.paid_at || "").localeCompare(a.paid_at || ""))[0];
  const paidInvoices = invoices.filter((invoice) => invoice.payment_status === "paid");
  const overdueInvoices = invoices.filter((invoice) => invoice.payment_status === "overdue");
  const totalCollected = paidInvoices.reduce((total, invoice) => total + Number(invoice.amount), 0);
  const overdueAmount = overdueInvoices.reduce((total, invoice) => total + Number(invoice.amount), 0);
  const collectionRate = invoices.length ? Math.round((paidInvoices.length / invoices.length) * 100) : 0;

  return (
    <div className="page">
      <PageHeader
        title="Invoices"
        description={isStaff ? "Manage recurring billing across Meridian Residences." : "View your recurring billing and payment status."}
        action={
          isStaff ? (
            <div className="invoice-page-actions">
              <SecondaryButton onClick={() => updateSelectedInvoices("overdue")} disabled={isProcessingBatch}>
                {isProcessingBatch ? "Processing..." : "Mark Selected Overdue"}
              </SecondaryButton>
              <Button onClick={() => updateSelectedInvoices("paid")} disabled={isProcessingBatch}>
                <CheckCircle2 size={16} />
                {isProcessingBatch ? "Processing..." : "Approve Selected"}
              </Button>
              <SecondaryButton onClick={handleGenerateBatch} disabled={isProcessingBatch}>
                <Plus size={16} />
                {isProcessingBatch ? "Generating..." : "Generate Monthly Batch"}
              </SecondaryButton>
            </div>
          ) : (
            <Button onClick={() => { setFormError(null); setIsGenerateOpen(true); }}>
              <Plus size={16} />
              Generate Invoice
            </Button>
          )
        }
      />

      {isLoading && <Loading label="Loading invoices..." />}
      {!isLoading && error && <ErrorMessage message={error} onRetry={loadInvoices} />}
      {!isLoading && !error && (
        <>
          {statusMessage && <p className="invoice-status-message">{statusMessage}</p>}
          <div className="card-grid">
            <StatCard icon={Wallet} label="Total outstanding" value={formatCurrency(totalOutstanding)} />
            <StatCard
              icon={CalendarClock}
              label="Next due"
              value={nextInvoice ? formatDate(nextInvoice.due_date) : "No pending payment"}
            />
            <StatCard
              icon={CheckCircle2}
              label="Last payment"
              value={lastPayment ? formatCurrency(lastPayment.amount) : "No payment recorded"}
            />
          </div>

          {isStaff && (
            <div className="card-grid staff-invoice-kpis">
              <StatCard icon={CheckCircle2} label="Total collected" value={formatCurrency(totalCollected)} />
              <StatCard icon={Wallet} label="Overdue exposure" value={formatCurrency(overdueAmount)} />
              <StatCard icon={CalendarClock} label="Collection rate" value={`${collectionRate}%`} />
            </div>
          )}

          {!isInsightsLoading && insights && (
            <Card className="ai-insight-card">
              <div className="ai-insight-card__icon"><Sparkles size={18} /></div>
              <div>
                <div className="ai-insight-card__header">
                  <strong>{isStaff ? "AI Portfolio Billing Insight" : "AI Payment Insight"}</strong>
                  <span className={`ai-insight-card__risk ai-insight-card__risk--${insights.risk_level}`}>
                    {insights.risk_level.toUpperCase()} RISK
                  </span>
                </div>
                <p>{insights.insight}</p>
              </div>
            </Card>
          )}

          <div className="section-heading-row">
            <h2 className="section-title">Recurring invoices</h2>
            <span className="section-count">{filteredInvoices.length} invoice{filteredInvoices.length === 1 ? "" : "s"}</span>
          </div>

          <div className="invoice-filter-bar">
            <div className="filter-tabs">
              {FILTERS.map((filter) => (
                <button
                  key={filter.key}
                  className={`filter-tab${activeFilter === filter.key ? " active" : ""}`}
                  onClick={() => setActiveFilter(filter.key)}
                >
                  {filter.label}
                </button>
              ))}
            </div>
            <div className="invoice-filter-bar__actions">
              <Input
                id="date_from"
                type="date"
                label="From"
                value={dateFrom}
                onChange={(event) => setDateFrom(event.target.value)}
              />
              <Input
                id="date_to"
                type="date"
                label="To"
                value={dateTo}
                onChange={(event) => setDateTo(event.target.value)}
              />
              {isStaff && (
                <SecondaryButton onClick={handleExportCsv}>
                  <FileSpreadsheet size={16} />
                  Export CSV
                </SecondaryButton>
              )}
              <SecondaryButton onClick={handleExportPdf} disabled={isExporting}>
                <Download size={16} />
                {isExporting ? "Exporting..." : "Export PDF"}
              </SecondaryButton>
            </div>
          </div>

          {filteredInvoices.length === 0 ? (
            <EmptyState message="No invoices match this filter." />
          ) : (
            <div className="invoice-list">
              {filteredInvoices.map((invoice) => (
                <InvoiceCard
                  key={invoice.id}
                  invoice={invoice}
                  onDownload={handleDownloadInvoice}
                  isStaff={isStaff}
                  isSelected={selectedInvoiceIds.includes(invoice.id)}
                  onSelect={toggleInvoiceSelection}
                  onPay={setInvoiceToPay}
                  onExtendDueDate={openExtendDueDate}
                />
              ))}
            </div>
          )}
        </>
      )}

      {isGenerateOpen && (
        <Modal title="Generate Recurring Invoice" onClose={() => !isSubmitting && setIsGenerateOpen(false)}>
          <form onSubmit={handleGenerate}>
            <Input
              id="billing_month"
              label="Select invoice month"
              type="month"
              value={generateForm.billing_month}
              onChange={(event) => {
                setFormError(null);
                setGenerateForm(getBillingDatesForMonth(event.target.value));
              }}
              required
            />
            <Input
              id="billing_period_start"
              label="Billing period start"
              type="date"
              value={generateForm.billing_period_start}
              readOnly={!isStaff}
              onChange={(event) => setGenerateForm((form) => ({ ...form, billing_period_start: event.target.value }))}
              required
            />
            <Input
              id="billing_period_end"
              label="Billing period end"
              type="date"
              value={generateForm.billing_period_end}
              readOnly={!isStaff}
              onChange={(event) => setGenerateForm((form) => ({ ...form, billing_period_end: event.target.value }))}
              required
            />
            <Input
              id="due_date"
              label="Due date"
              type="date"
              value={generateForm.due_date}
              readOnly={!isStaff}
              onChange={(event) => setGenerateForm((form) => ({ ...form, due_date: event.target.value }))}
              required
            />
            {formError && <p className="field__error">{formError}</p>}
            <div className="modal__actions">
              <SecondaryButton type="button" onClick={() => setIsGenerateOpen(false)} disabled={isSubmitting}>
                Cancel
              </SecondaryButton>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Generating..." : "Generate Invoice"}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {invoiceToExtend && (
        <Modal title="Extend invoice due date" onClose={() => !isSubmitting && setInvoiceToExtend(null)}>
          <form onSubmit={handleExtendDueDate}>
            <p className="payment-helper">Current due date: {formatDate(invoiceToExtend.due_date)}. The billing period will end the day before the new due date.</p>
            <Input
              id="extended_due_date"
              label="New due date"
              type="date"
              min={invoiceToExtend.due_date}
              value={extendedDueDate}
              onChange={(event) => setExtendedDueDate(event.target.value)}
              required
            />
            {formError && <p className="field__error">{formError}</p>}
            <div className="modal__actions">
              <SecondaryButton type="button" onClick={() => setInvoiceToExtend(null)} disabled={isSubmitting}>Cancel</SecondaryButton>
              <Button type="submit" disabled={isSubmitting}>{isSubmitting ? "Updating..." : "Extend due date"}</Button>
            </div>
          </form>
        </Modal>
      )}

      {invoiceToPay && (
        <Modal title={`Pay ${formatDate(invoiceToPay.billing_period_start)} invoice`} onClose={() => !isPaying && setInvoiceToPay(null)}>
          <form onSubmit={handlePaymentSubmit}>
            <div className="payment-summary">
              <span>Amount due</span>
              <strong>{formatCurrency(invoiceToPay.amount)}</strong>
            </div>
            <Input id="dummy_card_number" label="Dummy card number" placeholder="4242 4242 4242 4242" required />
            <div className="payment-form-grid">
              <Input id="dummy_expiry" label="Expiry" placeholder="12/30" required />
              <Input id="dummy_cvv" label="CVV" placeholder="123" required />
            </div>
            <p className="payment-helper">Demo gateway only. No real payment is processed.</p>
            <div className="modal__actions">
              <SecondaryButton type="button" onClick={() => setInvoiceToPay(null)} disabled={isPaying}>Cancel</SecondaryButton>
              <Button type="submit" disabled={isPaying}>{isPaying ? "Submitting..." : "Pay & Notify Staff"}</Button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}
