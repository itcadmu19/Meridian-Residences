import React, { useEffect, useMemo, useState } from "react";
import { AlertTriangle, CheckCircle2, Clock3, Plus, Wrench, X } from "lucide-react";
import {
  createTicket,
  deleteTicket,
  getTickets,
  triageTicket,
  updateTicket,
} from "../services/maintenanceService";
import { useAuth } from "../context/AuthContext";
import StatusBadge from "../components/StatusBadge";
import SummaryCard from "../components/SummaryCard";
import Toast from "../components/Toast";
import ConfirmDialog from "../components/ConfirmDialog";

// Staff-only display rule: a resolved ticket stays visible for this long
// after resolution, then drops out of the staff table to keep it from
// filling up with old closed-out work. This never touches the database -
// resident history, records, and the ticket itself are untouched; it's a
// pure client-side display filter re-evaluated on every load.
const RESOLVED_HIDE_HOURS = 48;

function isVisibleToStaff(ticket) {
  if (ticket.status !== "resolved") return true;
  if (!ticket.resolved_at) return true;
  const hoursSinceResolved = (Date.now() - new Date(ticket.resolved_at).getTime()) / (1000 * 60 * 60);
  return hoursSinceResolved < RESOLVED_HIDE_HOURS;
}

const ISSUE_TYPE_OPTIONS = [
  { value: "plumbing", label: "Plumbing" },
  { value: "electrical", label: "Electrical" },
  { value: "hvac", label: "HVAC" },
  { value: "appliance", label: "Appliance" },
  { value: "general", label: "General" },
  { value: "other", label: "Other" },
];

const FILTERS = [
  { key: "all", label: "All" },
  { key: "assigned", label: "Assigned" },
  { key: "in_progress", label: "In Progress" },
  { key: "resolved", label: "Resolved" },
  { key: "cancelled", label: "Cancelled" },
];

const PRIORITY_FILTERS = [
  { key: "all", label: "All priorities" },
  { key: "urgent", label: "Urgent" },
  { key: "high", label: "High" },
  { key: "medium", label: "Medium" },
  { key: "low", label: "Low" },
];

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

const STATUS_LABELS = Object.fromEntries(STATUS_OPTIONS.map((o) => [o.value, o.label]));
const PRIORITY_LABELS = Object.fromEntries(PRIORITY_OPTIONS.map((o) => [o.value, o.label]));

const ISSUE_TYPE_LABELS = Object.fromEntries(ISSUE_TYPE_OPTIONS.map((o) => [o.value, o.label]));

const MAX_PHOTO_BYTES = 1_000_000;

const DEMO_TICKETS = [
  {
    id: "ticket-demo-001",
    guest_id: "guest-demo-001",
    guest: { name: "Demo Resident", email: "demo.resident@example.com" },
    unit: { unit_number: "101" },
    issue_type: "plumbing",
    description: "Kitchen sink is leaking",
    priority: "high",
    status: "open",
    vendor_queue: null,
    escalated: false,
    created_at: "2026-09-10T10:00:00Z",
    resolved_at: null,
  },
  {
    id: "ticket-demo-002",
    guest_id: "guest-demo-002",
    guest: { name: "Other Resident", email: "other.resident@example.com" },
    unit: { unit_number: "204" },
    issue_type: "electrical",
    description: "Living room outlet not working",
    priority: "medium",
    status: "resolved",
    vendor_queue: "electrical-standard",
    escalated: false,
    created_at: "2026-09-05T10:00:00Z",
    resolved_at: "2026-09-06T10:00:00Z",
  },
];

function formatDate(value) {
  if (!value) return "—";
  return new Date(value).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function NewTicketDrawer({ open, saving, error, onClose, onSubmit }) {
  const [issueType, setIssueType] = useState("plumbing");
  const [description, setDescription] = useState("");
  const [photoDataUrl, setPhotoDataUrl] = useState(null);
  const [photoError, setPhotoError] = useState(null);

  useEffect(() => {
    if (open) {
      setIssueType("plumbing");
      setDescription("");
      setPhotoDataUrl(null);
      setPhotoError(null);
    }
  }, [open]);

  if (!open) return null;

  function handlePhotoChange(event) {
    const file = event.target.files?.[0];
    if (!file) {
      setPhotoDataUrl(null);
      setPhotoError(null);
      return;
    }
    if (file.size > MAX_PHOTO_BYTES) {
      setPhotoError("Photo is too large - please choose one under 1MB.");
      event.target.value = "";
      return;
    }
    setPhotoError(null);
    const reader = new FileReader();
    reader.onload = () => setPhotoDataUrl(reader.result);
    reader.readAsDataURL(file);
  }

  function handleSubmit(event) {
    event.preventDefault();
    if (!description.trim()) return;
    onSubmit({
      issue_type: issueType,
      description: description.trim(),
      photo_data_url: photoDataUrl || undefined,
    });
  }

  return (
    <div className="drawer-overlay" role="presentation" onClick={onClose}>
      <aside className="drawer-panel" role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-heading">
          <div>
            <span className="section-kicker">NEW REQUEST</span>
            <h3>Report an issue</h3>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close">
            <X size={18} />
          </button>
        </div>

        <div className="drawer-body">
          <form className="drawer-form" onSubmit={handleSubmit}>
            <label>
              Issue type
              <select value={issueType} onChange={(event) => setIssueType(event.target.value)}>
                {ISSUE_TYPE_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Description
              <textarea
                rows={4}
                value={description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="Describe the issue, e.g. Kitchen sink is leaking"
                required
              />
            </label>
            <label>
              Photo (optional)
              <input type="file" accept="image/*" onChange={handlePhotoChange} />
            </label>
            {photoDataUrl && (
              <img src={photoDataUrl} alt="Attached preview" className="ticket-photo-preview" />
            )}
            {photoError && <div className="demo-notice demo-notice--error">{photoError}</div>}

            {error && <div className="demo-notice demo-notice--error">{error}</div>}

            <div className="drawer-form-actions">
              <button type="button" className="secondary-button" onClick={onClose} disabled={saving}>
                Cancel
              </button>
              <button type="submit" className="primary-button" disabled={saving}>
                {saving ? "Submitting…" : "Submit request"}
              </button>
            </div>
          </form>
        </div>
      </aside>
    </div>
  );
}

function UpdateTicketDrawer({ ticket, saving, onClose, onSubmit }) {
  const [status, setStatus] = useState(ticket?.status || "open");
  const [priority, setPriority] = useState(ticket?.priority || "medium");

  useEffect(() => {
    if (ticket) {
      setStatus(ticket.status);
      setPriority(ticket.priority);
    }
  }, [ticket]);

  if (!ticket) return null;

  function handleSubmit(event) {
    event.preventDefault();
    onSubmit({ status, priority });
  }

  return (
    <div className="drawer-overlay" role="presentation" onClick={onClose}>
      <aside className="drawer-panel" role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-heading">
          <div>
            <span className="section-kicker">UPDATE REQUEST</span>
            <h3>{ISSUE_TYPE_LABELS[ticket.issue_type] || ticket.issue_type}</h3>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close">
            <X size={18} />
          </button>
        </div>

        <div className="drawer-body">
          <form className="drawer-form" onSubmit={handleSubmit}>
            <label>
              Status
              <select value={status} onChange={(event) => setStatus(event.target.value)}>
                {STATUS_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Priority
              <select value={priority} onChange={(event) => setPriority(event.target.value)}>
                {PRIORITY_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <div className="drawer-form-actions">
              <button type="button" className="secondary-button" onClick={onClose} disabled={saving}>
                Cancel
              </button>
              <button type="submit" className="primary-button" disabled={saving}>
                {saving ? "Saving…" : "Save changes"}
              </button>
            </div>
          </form>
        </div>
      </aside>
    </div>
  );
}

function TicketDetailsDrawer({ ticket, isStaff, onClose }) {
  if (!ticket) return null;

  return (
    <div className="drawer-overlay" role="presentation" onClick={onClose}>
      <aside className="drawer-panel" role="dialog" aria-modal="true" onClick={(e) => e.stopPropagation()}>
        <div className="drawer-heading">
          <div>
            <span className="section-kicker">REQUEST DETAILS</span>
            <h3>{ISSUE_TYPE_LABELS[ticket.issue_type] || ticket.issue_type}</h3>
          </div>
          <button className="icon-button" onClick={onClose} aria-label="Close">
            <X size={18} />
          </button>
        </div>

        <div className="drawer-body">
          <dl className="ticket-details-list">
            <dt>Description</dt>
            <dd>{ticket.description}</dd>

            <dt>Status</dt>
            <dd>
              <StatusBadge status={ticket.status} />
            </dd>

            <dt>Priority</dt>
            <dd>
              <StatusBadge status={ticket.priority} />
            </dd>

            {isStaff && (
              <>
                <dt>Resident</dt>
                <dd>
                  {ticket.guest?.name || "Unknown resident"}
                  {ticket.guest?.email && ` (${ticket.guest.email})`}
                  <br />
                  <small>ID: {ticket.guest_id}</small>
                </dd>
                <dt>Unit</dt>
                <dd>{ticket.unit?.unit_number || "—"}</dd>
              </>
            )}

            <dt>Vendor queue</dt>
            <dd>{ticket.vendor_queue || "Not yet assigned"}</dd>

            <dt>Escalated</dt>
            <dd>{ticket.escalated ? "Yes" : "No"}</dd>

            <dt>Submitted</dt>
            <dd>{formatDate(ticket.created_at)}</dd>

            <dt>Last updated</dt>
            <dd>{formatDate(ticket.updated_at)}</dd>

            <dt>Resolved</dt>
            <dd>{ticket.resolved_at ? formatDate(ticket.resolved_at) : "Not resolved yet"}</dd>

            {ticket.photo_data_url && (
              <>
                <dt>Photo</dt>
                <dd>
                  <a href={ticket.photo_data_url} target="_blank" rel="noreferrer">
                    <img src={ticket.photo_data_url} alt="Attached" className="ticket-photo-preview" />
                  </a>
                </dd>
              </>
            )}
          </dl>
        </div>
      </aside>
    </div>
  );
}

export default function Maintenance() {
  const { currentUser } = useAuth();
  const isStaff = currentUser?.role === "staff" || currentUser?.role === "admin";

  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [usingDemoData, setUsingDemoData] = useState(false);
  const [activeFilter, setActiveFilter] = useState("all");
  const [activePriorityFilter, setActivePriorityFilter] = useState("all");
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState(null);
  const [toast, setToast] = useState(null);
  const [busyTicketId, setBusyTicketId] = useState(null);
  const [deleteTarget, setDeleteTarget] = useState(null);
  const [updateTarget, setUpdateTarget] = useState(null);
  const [updateSaving, setUpdateSaving] = useState(false);
  const [detailsTarget, setDetailsTarget] = useState(null);

  async function loadTickets() {
    try {
      const data = await getTickets();
      setTickets(Array.isArray(data) ? data : []);
      setUsingDemoData(false);
    } catch {
      setTickets(DEMO_TICKETS);
      setUsingDemoData(true);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    setLoading(true);
    loadTickets();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const filteredTickets = useMemo(() => {
    return tickets
      .filter((ticket) => !isStaff || isVisibleToStaff(ticket))
      .filter((ticket) => activeFilter === "all" || ticket.status === activeFilter)
      .filter((ticket) => activePriorityFilter === "all" || ticket.priority === activePriorityFilter);
  }, [tickets, activeFilter, activePriorityFilter, isStaff]);

  const ticketCounts = useMemo(
    () => ({
      total: tickets.length,
      pending: tickets.filter((t) => !["resolved", "cancelled"].includes(t.status)).length,
      resolved: tickets.filter((t) => t.status === "resolved").length,
    }),
    [tickets]
  );

  async function handleCreateTicket(payload) {
    setSubmitting(true);
    setFormError(null);
    try {
      const created = await createTicket(payload);
      setTickets((prev) => [created, ...prev]);
      setIsDrawerOpen(false);
      setToast({ title: "Request submitted", message: "We're routing your request now." });

      // Kick off AI triage immediately, same as feature-lavanya's flow -
      // failure here shouldn't block ticket creation, resident can still
      // track it untriaged.
      try {
        const triaged = await triageTicket(created.id);
        setTickets((prev) =>
          prev.map((item) =>
            item.id === created.id
              ? {
                  ...item,
                  issue_type: triaged.issue_type,
                  priority: triaged.priority,
                  vendor_queue: triaged.vendor_queue,
                  escalated: triaged.escalated,
                  triage_reason: triaged.reason,
                  status: item.status === "open" ? "assigned" : item.status,
                }
              : item
          )
        );
      } catch {
        // ignore - ticket still exists, just untriaged
      }
    } catch {
      setFormError("Unable to submit the request. Please try again.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleUpdateSubmit(payload) {
    if (!updateTarget) return;
    setUpdateSaving(true);
    try {
      const updated = await updateTicket(updateTarget.id, payload);
      setTickets((prev) => prev.map((item) => (item.id === updateTarget.id ? updated : item)));
      setUpdateTarget(null);
      setToast({
        title: "Request updated",
        message: `Status: ${STATUS_LABELS[updated.status] || updated.status} · Priority: ${
          PRIORITY_LABELS[updated.priority] || updated.priority
        }`,
      });
    } catch {
      setToast({ title: "Update failed", message: "Could not update this request." });
    } finally {
      setUpdateSaving(false);
    }
  }

  async function handleDeleteConfirm() {
    if (!deleteTarget) return;
    setBusyTicketId(deleteTarget.id);
    try {
      await deleteTicket(deleteTarget.id);
      setTickets((prev) => prev.filter((item) => item.id !== deleteTarget.id));
      setDeleteTarget(null);
      setToast({ title: "Request deleted", message: "Your maintenance request has been removed." });
    } catch {
      setDeleteTarget(null);
      setToast({ title: "Delete failed", message: "Could not delete this request. Please try again." });
    } finally {
      setBusyTicketId(null);
    }
  }

  if (loading) {
    return (
      <div className="dashboard-skeleton">
        <div className="skeleton lease-header-skeleton" />
        <div className="skeleton lease-main-skeleton" />
      </div>
    );
  }

  return (
    <div className="staff-page">
      {usingDemoData && (
        <div className="demo-notice">
          <Wrench size={16} />
          <span>Backend is not connected, so demo maintenance data is being shown.</span>
        </div>
      )}

      <section className="page-heading lease-heading">
        <div>
          <span className="section-kicker">RESIDENT SERVICES</span>
          <h1>Maintenance</h1>
          <p>
            {isStaff
              ? "Review and triage maintenance requests across all properties."
              : "Report an issue or track your existing requests."}
          </p>
        </div>
        {!isStaff && (
          <button className="primary-button" onClick={() => setIsDrawerOpen(true)} disabled={usingDemoData}>
            <Plus size={17} />
            Submit request
          </button>
        )}
      </section>

      {isStaff && (
        <section className="summary-grid">
          <SummaryCard icon={<Wrench size={21} />} label="Total Tickets" value={ticketCounts.total} accent="green" />
          <SummaryCard icon={<Clock3 size={21} />} label="Pending Tickets" value={ticketCounts.pending} accent="gold" />
          <SummaryCard
            icon={<CheckCircle2 size={21} />}
            label="Resolved Tickets"
            value={ticketCounts.resolved}
            accent="olive"
          />
        </section>
      )}

      <section className="content-card">
        <div className="card-heading">
          <div>
            <span className="section-kicker">{isStaff ? "ALL REQUESTS" : "YOUR REQUESTS"}</span>
            <h3>Request directory</h3>
            {isStaff && (
              <p className="payment-helper">
                Resolved requests stay visible here for {RESOLVED_HIDE_HOURS} hours, then drop off this list to
                keep it current - the record itself is never deleted.
              </p>
            )}
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

        <div className="filter-tabs priority-filter-tabs">
          {PRIORITY_FILTERS.map((filter) => (
            <button
              key={filter.key}
              className={`filter-tab ${activePriorityFilter === filter.key ? "active" : ""}`}
              onClick={() => setActivePriorityFilter(filter.key)}
            >
              {filter.label}
            </button>
          ))}
        </div>

        <div className="lease-table-wrapper">
          <table className="lease-table">
            <thead>
              <tr>
                {isStaff && <th>Resident</th>}
                <th>Issue</th>
                <th>Description</th>
                <th>Priority</th>
                <th>Status</th>
                <th>Submitted</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {filteredTickets.map((ticket) => (
                <tr key={ticket.id}>
                  {isStaff && (
                    <td>
                      <strong>{ticket.guest?.name || "Unknown resident"}</strong>
                      <small>ID: {ticket.guest_id?.slice(0, 8) || "—"}</small>
                    </td>
                  )}
                  <td>
                    <strong>{ISSUE_TYPE_LABELS[ticket.issue_type] || ticket.issue_type}</strong>
                    {ticket.vendor_queue && <small>{ticket.vendor_queue}</small>}
                  </td>
                  <td className="ticket-description-cell">
                    {ticket.description}
                    {ticket.escalated && (
                      <span className="escalated-flag">
                        <AlertTriangle size={11} /> ESCALATED
                      </span>
                    )}
                    {ticket.photo_data_url && (
                      <a href={ticket.photo_data_url} target="_blank" rel="noreferrer" className="ticket-photo-link">
                        <img src={ticket.photo_data_url} alt="Attached" className="ticket-photo-thumb" />
                      </a>
                    )}
                  </td>
                  <td>
                    <StatusBadge status={ticket.priority} />
                  </td>
                  <td>
                    <StatusBadge status={ticket.status} />
                  </td>
                  <td>{formatDate(ticket.created_at)}</td>
                  <td>
                    <div className="lease-table-actions">
                      <button
                        className="text-button"
                        disabled={usingDemoData}
                        onClick={() => setDetailsTarget(ticket)}
                      >
                        View details
                      </button>
                      {isStaff && (
                        <button
                          className="text-button"
                          disabled={busyTicketId === ticket.id || usingDemoData}
                          onClick={() => setUpdateTarget(ticket)}
                        >
                          Update
                        </button>
                      )}
                      {!isStaff && (
                        <button
                          className="text-button text-button--danger"
                          disabled={busyTicketId === ticket.id || usingDemoData}
                          onClick={() => setDeleteTarget(ticket)}
                        >
                          Delete
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
              {filteredTickets.length === 0 && (
                <tr>
                  <td colSpan={isStaff ? 7 : 6} className="lease-table-empty">
                    No maintenance requests in this view yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </section>

      <NewTicketDrawer
        open={isDrawerOpen}
        saving={submitting}
        error={formError}
        onClose={() => setIsDrawerOpen(false)}
        onSubmit={handleCreateTicket}
      />

      <Toast
        open={Boolean(toast)}
        onClose={() => setToast(null)}
        title={toast?.title}
        message={toast?.message}
      />

      <ConfirmDialog
        open={Boolean(deleteTarget)}
        title="Delete this request?"
        message={
          deleteTarget
            ? `This will permanently remove your "${ISSUE_TYPE_LABELS[deleteTarget.issue_type] || deleteTarget.issue_type}" request. This cannot be undone.`
            : ""
        }
        confirmLabel="Delete request"
        busy={busyTicketId === deleteTarget?.id}
        onConfirm={handleDeleteConfirm}
        onCancel={() => setDeleteTarget(null)}
      />

      <UpdateTicketDrawer
        ticket={updateTarget}
        saving={updateSaving}
        onClose={() => setUpdateTarget(null)}
        onSubmit={handleUpdateSubmit}
      />

      <TicketDetailsDrawer ticket={detailsTarget} isStaff={isStaff} onClose={() => setDetailsTarget(null)} />
    </div>
  );
}
