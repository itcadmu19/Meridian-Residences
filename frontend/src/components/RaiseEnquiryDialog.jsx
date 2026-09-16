import React, { useEffect, useState } from "react";
import { HelpCircle } from "lucide-react";

export default function RaiseEnquiryDialog({ open, busy, error, onSubmit, onCancel }) {
  const [subject, setSubject] = useState("");
  const [message, setMessage] = useState("");
  const [reference, setReference] = useState("");

  useEffect(() => {
    if (open) {
      setSubject("");
      setMessage("");
      setReference("");
    }
  }, [open]);

  if (!open) return null;

  function handleSubmit(event) {
    event.preventDefault();
    onSubmit({
      subject: subject.trim(),
      message: message.trim(),
      reference: reference.trim() || undefined,
    });
  }

  return (
    <div className="confirm-dialog-overlay" role="presentation" onClick={onCancel}>
      <div
        className="confirm-dialog"
        role="dialog"
        aria-modal="true"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="confirm-dialog-icon confirm-dialog-icon--neutral">
          <HelpCircle size={20} />
        </div>
        <h3>Raise an enquiry</h3>
        <p>Ask a question about your lease agreement. Staff will respond here.</p>

        <form className="drawer-form" onSubmit={handleSubmit}>
          <label>
            Subject
            <input
              type="text"
              value={subject}
              maxLength={200}
              onChange={(event) => setSubject(event.target.value)}
              placeholder="e.g. Security Deposit"
              required
            />
          </label>
          <label>
            Referenced clause/section (optional)
            <input
              type="text"
              value={reference}
              maxLength={200}
              onChange={(event) => setReference(event.target.value)}
              placeholder="e.g. Clause 5.2"
            />
          </label>
          <label>
            Question
            <textarea
              value={message}
              onChange={(event) => setMessage(event.target.value)}
              placeholder="Can you explain clause 5.2 regarding the security deposit refund?"
              required
            />
          </label>

          {error && <div className="demo-notice demo-notice--error">{error}</div>}

          <div className="confirm-dialog-actions">
            <button type="button" className="secondary-button" onClick={onCancel} disabled={busy}>
              Cancel
            </button>
            <button type="submit" className="primary-button" disabled={busy || !subject.trim() || !message.trim()}>
              {busy ? "Submitting…" : "Submit enquiry"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
