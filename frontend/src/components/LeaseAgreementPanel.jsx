import React, { useEffect, useState } from "react";
import { Download, FileText, MessageCircleQuestion, ShieldCheck } from "lucide-react";
import {
  acceptAgreementDocument,
  createLeaseEnquiry,
  downloadAgreementDocumentPdf,
  getAgreementDocument,
  getLeaseEnquiries,
} from "../services/leaseService";
import StatusBadge from "./StatusBadge";
import ConfirmDialog from "./ConfirmDialog";
import RaiseEnquiryDialog from "./RaiseEnquiryDialog";
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
  return new Date(value).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
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

const ENQUIRY_CAN_RAISE_STATUSES = new Set(["sent_to_resident", "accepted"]);

export default function LeaseAgreementPanel({ lease, disabled }) {
  const [agreement, setAgreement] = useState(null);
  const [loading, setLoading] = useState(true);
  const [enquiries, setEnquiries] = useState([]);
  const [unavailable, setUnavailable] = useState(false);

  const [downloading, setDownloading] = useState(false);
  const [showAccept, setShowAccept] = useState(false);
  const [accepting, setAccepting] = useState(false);

  const [showEnquiry, setShowEnquiry] = useState(false);
  const [submittingEnquiry, setSubmittingEnquiry] = useState(false);
  const [enquiryError, setEnquiryError] = useState(null);

  const [toast, setToast] = useState(null);

  const leaseId = lease?.id;

  useEffect(() => {
    if (disabled || !leaseId) {
      setLoading(false);
      return undefined;
    }

    let mounted = true;
    setLoading(true);

    (async () => {
      try {
        const [doc, enquiryList] = await Promise.all([
          getAgreementDocument(leaseId),
          getLeaseEnquiries(leaseId).catch(() => []),
        ]);
        if (mounted) {
          setAgreement(doc);
          setEnquiries(Array.isArray(enquiryList) ? enquiryList : []);
          setUnavailable(false);
        }
      } catch {
        if (mounted) setUnavailable(true);
      } finally {
        if (mounted) setLoading(false);
      }
    })();

    return () => {
      mounted = false;
    };
  }, [leaseId, disabled]);

  if (disabled) {
    return (
      <section className="content-card lease-agreement-card">
        <div className="card-heading">
          <div>
            <span className="section-kicker">LEASE AGREEMENT</span>
            <h3>Agreement overview</h3>
          </div>
        </div>
        <p className="lease-table-empty">Connect to the backend to view your lease agreement.</p>
      </section>
    );
  }

  async function handleDownloadPdf() {
    setDownloading(true);
    try {
      const blob = await downloadAgreementDocumentPdf(leaseId);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `agreement_${leaseId}_v${agreement.version}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch {
      setToast({ title: "Download failed", message: "Could not download the agreement PDF. Please try again." });
    } finally {
      setDownloading(false);
    }
  }

  async function handleAcceptConfirm() {
    setAccepting(true);
    try {
      const updated = await acceptAgreementDocument(leaseId);
      setAgreement(updated);
      setShowAccept(false);
      setToast({ title: "Lease accepted", message: "You have accepted this lease agreement." });
    } catch {
      setShowAccept(false);
      setToast({ title: "Could not accept", message: "Something went wrong accepting the agreement. Please try again." });
    } finally {
      setAccepting(false);
    }
  }

  async function handleEnquirySubmit(payload) {
    setSubmittingEnquiry(true);
    setEnquiryError(null);
    try {
      const created = await createLeaseEnquiry(leaseId, payload);
      setEnquiries((prev) => [created, ...prev]);
      setShowEnquiry(false);
      setToast({ title: "Enquiry submitted", message: "Your question has been sent to the property team." });
    } catch {
      setEnquiryError("Could not submit your enquiry. Please try again.");
    } finally {
      setSubmittingEnquiry(false);
    }
  }

  const canAccept = agreement?.status === "sent_to_resident";
  const canRaiseEnquiry = agreement && ENQUIRY_CAN_RAISE_STATUSES.has(agreement.status);

  return (
    <section className="content-card lease-agreement-card">
      <div className="card-heading">
        <div>
          <span className="section-kicker">LEASE AGREEMENT</span>
          <h3>Agreement overview</h3>
        </div>
        {agreement && <StatusBadge status={agreement.status} />}
      </div>

      {loading ? (
        <p className="lease-table-empty">Loading your lease agreement…</p>
      ) : unavailable ? (
        <p className="lease-table-empty">Could not load your lease agreement right now. Please try again later.</p>
      ) : !agreement ? (
        <div className="agreement-empty-state">
          <div className="help-icon">
            <FileText size={20} />
          </div>
          <p>No lease agreement has been sent yet. You'll be able to review it here once your property manager sends it.</p>
        </div>
      ) : (
        <>
          <div className="agreement-meta-grid">
            <div>
              <span>Lease ID</span>
              <strong>{lease.id}</strong>
            </div>
            <div>
              <span>Property</span>
              <strong>{lease.property?.name || "—"}</strong>
            </div>
            <div>
              <span>Unit</span>
              <strong>{lease.unit?.unit_number || "—"}</strong>
            </div>
            <div>
              <span>Lease duration</span>
              <strong>
                {formatDate(lease.start_date)} – {formatDate(lease.end_date)}
              </strong>
            </div>
            <div>
              <span>Monthly rent</span>
              <strong>{formatCurrency(lease.monthly_rate)}</strong>
            </div>
            <div>
              <span>Current version</span>
              <strong>v{agreement.version}</strong>
            </div>
            <div>
              <span>Date sent</span>
              <strong>{formatDateTime(agreement.sent_at)}</strong>
            </div>
            {agreement.accepted_at && (
              <div>
                <span>Date accepted</span>
                <strong>{formatDateTime(agreement.accepted_at)}</strong>
              </div>
            )}
          </div>

          <p className="agreement-ai-note">
            <ShieldCheck size={14} /> This agreement was generated with AI assistance from your lease data and
            reviewed by property staff before being sent to you.
          </p>

          <div className="agreement-content">{agreement.content}</div>

          <div className="lease-actions agreement-actions">
            <button className="secondary-button" onClick={handleDownloadPdf} disabled={downloading}>
              <Download size={16} />
              {downloading ? "Downloading…" : "Download PDF"}
            </button>
            {canAccept && (
              <button className="primary-button" onClick={() => setShowAccept(true)}>
                Accept Lease
              </button>
            )}
            {canRaiseEnquiry && (
              <button className="secondary-button" onClick={() => setShowEnquiry(true)}>
                <MessageCircleQuestion size={16} />
                Raise Enquiry
              </button>
            )}
          </div>

          {agreement.status === "accepted" && (
            <p className="agreement-accepted-note">Agreement Status: ACCEPTED</p>
          )}
        </>
      )}

      {enquiries.length > 0 && (
        <div className="enquiry-history">
          <span className="section-kicker">YOUR ENQUIRIES</span>
          <div className="enquiry-list">
            {enquiries.map((enquiry) => (
              <div className="enquiry-item" key={enquiry.id}>
                <div className="enquiry-item-heading">
                  <strong>{enquiry.subject}</strong>
                  <StatusBadge status={enquiry.status} />
                </div>
                {enquiry.reference && <small>Re: {enquiry.reference}</small>}
                <p>{enquiry.message}</p>
                {enquiry.staff_response && (
                  <div className="enquiry-response">
                    <span>Staff response · {formatDateTime(enquiry.responded_at)}</span>
                    <p>{enquiry.staff_response}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      <ConfirmDialog
        open={showAccept}
        title="Accept lease agreement?"
        message="I confirm that I have reviewed this lease agreement and want to accept it. This cannot be undone."
        confirmLabel={accepting ? "Accepting…" : "Accept Lease"}
        busy={accepting}
        onConfirm={handleAcceptConfirm}
        onCancel={() => setShowAccept(false)}
      />

      <RaiseEnquiryDialog
        open={showEnquiry}
        busy={submittingEnquiry}
        error={enquiryError}
        onSubmit={handleEnquirySubmit}
        onCancel={() => {
          setShowEnquiry(false);
          setEnquiryError(null);
        }}
      />

      <Toast open={Boolean(toast)} onClose={() => setToast(null)} title={toast?.title} message={toast?.message} />
    </section>
  );
}
