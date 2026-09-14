import React, { useState } from "react";
import Modal from "./Modal.jsx";
import Select from "./Select.jsx";
import Button from "./Button.jsx";
import SecondaryButton from "./SecondaryButton.jsx";

const STATUS_OPTIONS = [
  { value: "open", label: "Open" },
  { value: "assigned", label: "Assigned" },
  { value: "in_progress", label: "In Progress" },
  { value: "resolved", label: "Resolved" },
  { value: "cancelled", label: "Cancelled" },
];

const PRIORITY_OPTIONS = [
  { value: "low", label: "Low" },
  { value: "medium", label: "Medium" },
  { value: "high", label: "High" },
  { value: "urgent", label: "Urgent" },
];

export default function MaintenanceUpdateModal({ ticket, onClose, onSave }) {
  const [status, setStatus] = useState(ticket.status);
  const [priority, setPriority] = useState(ticket.priority);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState(null);

  async function handleSubmit(event) {
    event.preventDefault();
    setIsSubmitting(true);
    setError(null);
    try {
      await onSave(ticket.id, { status, priority });
    } catch (err) {
      setError(err.message || "Unable to update the ticket.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Modal title="Update Maintenance Ticket" onClose={() => !isSubmitting && onClose()}>
      <form onSubmit={handleSubmit}>
        <Select
          id="status"
          label="Status"
          options={STATUS_OPTIONS}
          value={status}
          onChange={(event) => setStatus(event.target.value)}
        />
        <Select
          id="priority"
          label="Priority"
          options={PRIORITY_OPTIONS}
          value={priority}
          onChange={(event) => setPriority(event.target.value)}
        />
        {error && <p className="field__error">{error}</p>}
        <div className="modal__actions">
          <SecondaryButton type="button" onClick={onClose} disabled={isSubmitting}>
            Cancel
          </SecondaryButton>
          <Button type="submit" disabled={isSubmitting}>
            {isSubmitting ? "Saving..." : "Save Changes"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
