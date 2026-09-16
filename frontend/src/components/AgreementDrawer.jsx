import React, { useEffect, useState } from "react";
import { Sparkles, X } from "lucide-react";
import {
  generateAgreement,
  getAgreement,
  getEnquiries,
  respondToEnquiry,
  sendAgreement,
  updateAgreementDraft,
} from "../services/staffLeaseService";
import StatusBadge from "./StatusBadge";
import ConfirmDialog from "./ConfirmDialog";
import Toast from "./Toast";

function formatCurrency(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatDate(value) {
  if (!value) return "—";
  return new Date(value).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}

function formatDateTime(value) {
  if (!value) return "—";
  return new Date(value).toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

const EMPTY_FORM = {
  security_deposit: "",
  payment_due_day: "",
  notice_period_days: "",
  maintenance_responsibility: "",
  utilities_responsibility: "",
  occupancy_terms: "",
  late_payment_terms: "",
  renewal_terms: "",
};

function formFromStructuredFields(fields) {
  if (!fields) return EMPTY_FORM;
  return {
    security_deposit: fields.security_deposit ? String(fields.security_deposit).replace(/[^0-9.]/g, "") : "",
    payment_due_day: fields.payment_due_day ?? "",
    notice_period_days: fields.notice_period_days ?? "",
    maintenance_responsibility: fields.maintenance_responsibility ?? "",
    utilities_responsibility: fields.utilities_responsibility ?? "",
    occupancy_terms: fields.occupancy_terms ?? "",
    late_payment_terms: fields.late_payment_terms ?? "",
    renewal_terms: fields.renewal_terms ?? "",
  };
}

function EnquiryItem({ enquiry, onRespond, busy }) {
  const [response, setResponse] = useState(enquiry.staff_response || "");
  const [close, setClose] = useState(false);

  return (
    <div className="enquiry-item">
      <div className="enquiry-item-heading">
        <strong>{enquiry.subject}</strong>
        <StatusBadge status={enquiry.status} />
      </div>
      {enquiry.reference && <small>Re: {enquiry.reference}</small>}
      <p>{enquiry.message}</p>
      <small>Raised {formatDateTime(enquiry.created_at)}</small>

      {enquiry.status !== "closed" ? (
        <div className="enquiry-respond-form">
          <textarea
            value={response}
            onChange={(event) => setResponse(event.target.value)}
            placeholder="Write a response to the resident…"
          />
          <label className="enquiry-close-toggle">
            <input type="checkbox" checked={close} onChange={(event) => setClose(event.target.checked)} />
            Mark as closed
          </label>
          <div className="drawer-form-actions">
            <button
              className="primary-button"
              disabled={busy || !response.trim()}
              onClick={() => onRespond(enquiry.id, { response: response.trim(), close })}
            >
              {busy ? "Sending…" : "Send response"}
            </button>
          </div>
        </div>
      ) : (
        enquiry.staff_response && (
          <div className="enquiry-response">
            <span>Staff response · {formatDateTime(enquiry.responded_at)}</span>
            <p>{enquiry.staff_response}</p>
          </div>
        )
      )}
    </div>
  );
}

export default function AgreementDrawer({ open, lease, onClose }) {
  const [loading, setLoading] = useState(true);
  const [agreement, setAgreement] = useState(null);
  const [enquiries, setEnquiries] = useState([]);
  const [error, setError] = useState(null);
  const [toast, setToast] = useState(null);

  const [showGenerateForm, setShowGenerateForm] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [generating, setGenerating] = useState(false);
  const [confirmRegenerate, setConfirmRegenerate] = useState(false);

  const [draftContent, setDraftContent] = useState("");
  const [savingDraft, setSavingDraft] = useState(false);
  const [sending, setSending] = useState(false);
  const [confirmSend, setConfirmSend] = useState(false);

  const [respondingId, setRespondingId] = useState(null);

  const leaseId = lease?.id;

  useEffect(() => {
    if (!open || !leaseId) return undefined;

    let mounted = true;
    setLoading(true);
    setError(null);
    setShowGenerateForm(false);

    (async () => {
      try {
        const [doc, enquiryList] = await Promise.all([getAgreement(leaseId), getEnquiries(leaseId).catch(() => [])]);
        if (mounted) {
          setAgreement(doc);
          setEnquiries(Array.isArray(enquiryList) ? enquiryList : []);
          setDraftContent(doc?.content || "");
          setForm(formFromStructuredFields(doc?.structured_fields));
          setShowGenerateForm(!doc);
        }
      } catch {
        if (mounted) setError("Could not load the agreement for this lease.");
      } finally {
        if (mounted) setLoading(false);
      }
    })();

    return () => {
      mounted = false;
    };
  }, [open, leaseId]);

  if (!open || !lease) return null;

  function updateFormField(key, value) {
    setForm((prev) => ({ ...prev, [key]: value }));
  }

  function buildGeneratePayload() {
    const payload = { security_deposit: Number(form.security_deposit) };
    if (form.payment_due_day) payload.payment_due_day = Number(form.payment_due_day);
    if (form.notice_period_days) payload.notice_period_days = Number(form.notice_period_days);
    if (form.maintenance_responsibility.trim()) payload.maintenance_responsibility = form.maintenance_responsibility.trim();
    if (form.utilities_responsibility.trim()) payload.utilities_responsibility = form.utilities_responsibility.trim();
    if (form.occupancy_terms.trim()) payload.occupancy_terms = form.occupancy_terms.trim();
    if (form.late_payment_terms.trim()) payload.late_payment_terms = form.late_payment_terms.trim();
    if (form.renewal_terms.trim()) payload.renewal_terms = form.renewal_terms.trim();
    return payload;
  }

  async function runGenerate() {
    setGenerating(true);
    setError(null);
    try {
      const doc = await generateAgreement(leaseId, buildGeneratePayload());
      setAgreement(doc);
      setDraftContent(doc.content);
      setShowGenerateForm(false);
      setConfirmRegenerate(false);
      setToast({ title: "Draft generated", message: "AI-generated draft created — review before sending." });
    } catch (err) {
      setError(err?.response?.data?.detail?.message || "Could not generate the agreement. Check the security deposit value.");
    } finally {
      setGenerating(false);
    }
  }

  function handleGenerateSubmit(event) {
    event.preventDefault();
    if (agreement && agreement.status !== "draft") {
      setConfirmRegenerate(true);
      return;
    }
    runGenerate();
  }

  async function handleSaveDraft() {
    setSavingDraft(true);
    setError(null);
    try {
      const doc = await updateAgreementDraft(leaseId, draftContent);
      setAgreement(doc);
      setToast({ title: "Draft saved", message: "Your edits have been saved." });
    } catch {
      setError("Could not save the draft. Please try again.");
    } finally {
      setSavingDraft(false);
    }
  }

  async function handleSend() {
    setSending(true);
    setError(null);
    try {
      const doc = await sendAgreement(leaseId);
      setAgreement(doc);
      setConfirmSend(false);
      setToast({ title: "Sent to resident", message: `The agreement was sent to ${lease.guest?.name}.` });
    } catch {
      setError("Could not send the agreement. Please try again.");
    } finally {
      setSending(false);
    }
  }

  async function handleRespond(enquiryId, payload) {
    setRespondingId(enquiryId);
    try {
      const updated = await respondToEnquiry(leaseId, enquiryId, payload);
      setEnquiries((prev) => prev.map((item) => (item.id === enquiryId ? updated : item)));
      setToast({ title: "Response sent", message: "The resident will see your response." });
    } catch {
      setError("Could not send the response. Please try again.");
    } finally {
      setRespondingId(null);
    }
  }

  const isDraft = agreement?.status === "draft";
  const isSentOrAccepted = agreement && (agreement.status === "sent_to_resident" || agreement.status === "accepted");

  return (
    <>
    <div className="drawer-overlay" role="presentation" onClick={onClose}>
      <aside
        className="drawer-panel drawer-panel--wide"
        role="dialog"
        aria-modal="true"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="drawer-heading">
          <div>
            <span className="section-kicker">LEASE AGREEMENT</span>
            <h3>{lease.guest?.name} — Apartment {lease.unit?.unit_number}</h3>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close">
            <X size={18} />
          </button>
        </div>

        <div className="drawer-summary-row drawer-summary-row--grid">
          <div>
            <span>Lease ID</span>
            <strong>{lease.id}</strong>
          </div>
          <div>
            <span>Resident</span>
            <strong>{lease.guest?.name}</strong>
            <small>{lease.guest?.email}</small>
          </div>
          <div>
            <span>Residence</span>
            <strong>{lease.property?.name}</strong>
            <small>Apartment {lease.unit?.unit_number}</small>
          </div>
          <div>
            <span>Lease term</span>
            <strong>
              {formatDate(lease.start_date)} – {formatDate(lease.end_date)}
            </strong>
          </div>
          <div>
            <span>Monthly rent</span>
            <strong>{formatCurrency(lease.monthly_rate)}</strong>
          </div>
        </div>

        {error && <div className="demo-notice demo-notice--error">{error}</div>}

        {loading ? (
          <p className="lease-table-empty">Loading agreement…</p>
        ) : (
          <>
            {agreement && (
              <div className="agreement-status-row">
                <StatusBadge status={agreement.status} />
                <span>Version {agreement.version}</span>
                {agreement.sent_at && <span>Sent {formatDateTime(agreement.sent_at)}</span>}
                {agreement.accepted_at && <span>Accepted {formatDateTime(agreement.accepted_at)}</span>}
              </div>
            )}

            {showGenerateForm ? (
              <form className="drawer-form agreement-generate-form" onSubmit={handleGenerateSubmit}>
                <p className="ai-generate-banner">
                  <Sparkles size={14} /> AI-generated draft — review before sending. Fields left blank use the
                  property's standard terms.
                </p>
                <label>
                  Security deposit (required)
                  <input
                    type="number"
                    min="1"
                    step="0.01"
                    required
                    value={form.security_deposit}
                    onChange={(event) => updateFormField("security_deposit", event.target.value)}
                  />
                </label>
                <details className="agreement-advanced-fields">
                  <summary>Advanced terms (optional — defaults apply if left blank)</summary>
                  <div className="drawer-form-grid-2">
                    <label>
                      Payment due day (1–28)
                      <input
                        type="number"
                        min="1"
                        max="28"
                        value={form.payment_due_day}
                        onChange={(event) => updateFormField("payment_due_day", event.target.value)}
                      />
                    </label>
                    <label>
                      Notice period (days)
                      <input
                        type="number"
                        min="0"
                        value={form.notice_period_days}
                        onChange={(event) => updateFormField("notice_period_days", event.target.value)}
                      />
                    </label>
                  </div>
                  <label>
                    Maintenance responsibility
                    <textarea
                      value={form.maintenance_responsibility}
                      onChange={(event) => updateFormField("maintenance_responsibility", event.target.value)}
                    />
                  </label>
                  <label>
                    Utilities responsibility
                    <textarea
                      value={form.utilities_responsibility}
                      onChange={(event) => updateFormField("utilities_responsibility", event.target.value)}
                    />
                  </label>
                  <label>
                    Occupancy terms
                    <textarea
                      value={form.occupancy_terms}
                      onChange={(event) => updateFormField("occupancy_terms", event.target.value)}
                    />
                  </label>
                  <label>
                    Late-payment terms
                    <textarea
                      value={form.late_payment_terms}
                      onChange={(event) => updateFormField("late_payment_terms", event.target.value)}
                    />
                  </label>
                  <label>
                    Renewal terms
                    <textarea
                      value={form.renewal_terms}
                      onChange={(event) => updateFormField("renewal_terms", event.target.value)}
                    />
                  </label>
                </details>

                <div className="drawer-form-actions">
                  {agreement && (
                    <button type="button" className="secondary-button" onClick={() => setShowGenerateForm(false)}>
                      Back
                    </button>
                  )}
                  <button type="submit" className="primary-button" disabled={generating || !form.security_deposit}>
                    <Sparkles size={16} />
                    {generating ? "Generating…" : "Generate Lease Agreement"}
                  </button>
                </div>
              </form>
            ) : agreement ? (
              <>
                <p className="ai-generate-banner">
                  <Sparkles size={14} /> AI-generated draft — review before sending to the resident.
                </p>

                {isDraft ? (
                  <textarea
                    className="agreement-edit-textarea"
                    value={draftContent}
                    onChange={(event) => setDraftContent(event.target.value)}
                  />
                ) : (
                  <div className="agreement-content">{agreement.content}</div>
                )}

                <div className="drawer-form-actions agreement-drawer-actions">
                  {isDraft && (
                    <>
                      <button className="secondary-button" onClick={() => setShowGenerateForm(true)}>
                        Regenerate
                      </button>
                      <button className="secondary-button" onClick={handleSaveDraft} disabled={savingDraft}>
                        {savingDraft ? "Saving…" : "Save draft"}
                      </button>
                      <button className="primary-button" onClick={() => setConfirmSend(true)}>
                        Send to Resident
                      </button>
                    </>
                  )}
                  {isSentOrAccepted && (
                    <button className="secondary-button" onClick={() => setShowGenerateForm(true)}>
                      Regenerate (new version)
                    </button>
                  )}
                </div>
              </>
            ) : (
              <p className="lease-table-empty">No agreement yet for this lease.</p>
            )}

            <div className="enquiry-history">
              <span className="section-kicker">ENQUIRIES</span>
              {enquiries.length > 0 ? (
                <div className="enquiry-list">
                  {enquiries.map((enquiry) => (
                    <EnquiryItem
                      key={enquiry.id}
                      enquiry={enquiry}
                      busy={respondingId === enquiry.id}
                      onRespond={handleRespond}
                    />
                  ))}
                </div>
              ) : (
                <p className="lease-table-empty">No enquiries have been raised for this lease.</p>
              )}
            </div>
          </>
        )}
      </aside>
    </div>

    <ConfirmDialog
      open={confirmSend}
      title="Send agreement to resident?"
      message={`${lease.guest?.name} will be able to view and accept this agreement. Make sure you've reviewed it first.`}
      confirmLabel={sending ? "Sending…" : "Send to Resident"}
      busy={sending}
      onConfirm={handleSend}
      onCancel={() => setConfirmSend(false)}
    />

    <ConfirmDialog
      open={confirmRegenerate}
      title="Regenerate this agreement?"
      message="A new version will be created and the currently sent version will be marked superseded. The resident will need to accept the new version once you send it."
      confirmLabel={generating ? "Regenerating…" : "Regenerate"}
      busy={generating}
      onConfirm={runGenerate}
      onCancel={() => setConfirmRegenerate(false)}
    />

    <Toast open={Boolean(toast)} onClose={() => setToast(null)} title={toast?.title} message={toast?.message} />
    </>
  );
}
