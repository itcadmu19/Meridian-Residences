import React, { useEffect, useMemo, useState } from "react";
import { CalendarClock, CheckCircle2, Plus, Wallet } from "lucide-react";
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

const FILTERS = [
  { key: "all", label: "All" },
  { key: "pending", label: "Pending" },
  { key: "paid", label: "Paid" },
  { key: "overdue", label: "Overdue" },
];

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

export default function Invoices() {
  const [invoices, setInvoices] = useState([]);
  const [activeFilter, setActiveFilter] = useState("all");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isGenerateOpen, setIsGenerateOpen] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState(null);
  const [generateForm, setGenerateForm] = useState({
    billing_period_start: "2026-09-01",
    billing_period_end: "2026-09-30",
    due_date: "2026-10-10",
  });

  async function loadInvoices() {
    setIsLoading(true);
    setError(null);
    try {
      const response = await invoiceService.getInvoices({ page: 1, page_size: 100 });
      setInvoices(response.data || []);
    } catch (err) {
      setError(err.message || "Unable to load your invoices.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadInvoices();
  }, []);

  async function handleGenerate(event) {
    event.preventDefault();
    const leaseId = invoices[0]?.lease_id;
    if (!leaseId) {
      setFormError("An active lease is required before an invoice can be generated.");
      return;
    }

    setIsSubmitting(true);
    setFormError(null);
    try {
      const response = await invoiceService.generateInvoice({ lease_id: leaseId, ...generateForm });
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

  const filteredInvoices = useMemo(() => {
    if (activeFilter === "all") return invoices;
    return invoices.filter((invoice) => invoice.payment_status === activeFilter);
  }, [activeFilter, invoices]);

  const totalOutstanding = invoices
    .filter((invoice) => ["pending", "overdue"].includes(invoice.payment_status))
    .reduce((total, invoice) => total + Number(invoice.amount), 0);
  const nextInvoice = invoices
    .filter((invoice) => invoice.payment_status === "pending")
    .sort((a, b) => a.due_date.localeCompare(b.due_date))[0];
  const lastPayment = invoices
    .filter((invoice) => invoice.payment_status === "paid")
    .sort((a, b) => (b.paid_at || "").localeCompare(a.paid_at || ""))[0];

  return (
    <div className="page">
      <PageHeader
        title="Invoices"
        description="View your recurring billing and payment status."
        action={
          <Button onClick={() => { setFormError(null); setIsGenerateOpen(true); }}>
            <Plus size={16} />
            Generate Invoice
          </Button>
        }
      />

      {isLoading && <Loading label="Loading invoices..." />}
      {!isLoading && error && <ErrorMessage message={error} onRetry={loadInvoices} />}
      {!isLoading && !error && (
        <>
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

          <div className="section-heading-row">
            <h2 className="section-title">Recurring invoices</h2>
            <span className="section-count">{filteredInvoices.length} invoice{filteredInvoices.length === 1 ? "" : "s"}</span>
          </div>

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

          {filteredInvoices.length === 0 ? (
            <EmptyState message="No invoices match this filter." />
          ) : (
            <div className="invoice-list">
              {filteredInvoices.map((invoice) => <InvoiceCard key={invoice.id} invoice={invoice} />)}
            </div>
          )}
        </>
      )}

      {isGenerateOpen && (
        <Modal title="Generate Recurring Invoice" onClose={() => !isSubmitting && setIsGenerateOpen(false)}>
          <form onSubmit={handleGenerate}>
            <Input
              id="billing_period_start"
              label="Billing period start"
              type="date"
              value={generateForm.billing_period_start}
              onChange={(event) => setGenerateForm((form) => ({ ...form, billing_period_start: event.target.value }))}
              required
            />
            <Input
              id="billing_period_end"
              label="Billing period end"
              type="date"
              value={generateForm.billing_period_end}
              onChange={(event) => setGenerateForm((form) => ({ ...form, billing_period_end: event.target.value }))}
              required
            />
            <Input
              id="due_date"
              label="Due date"
              type="date"
              value={generateForm.due_date}
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
    </div>
  );
}
