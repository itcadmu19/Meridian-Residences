import React, { useEffect, useMemo, useState } from "react";
import { Plus } from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";
import PageHeader from "../components/PageHeader.jsx";
import Button from "../components/Button.jsx";
import SecondaryButton from "../components/SecondaryButton.jsx";
import Modal from "../components/Modal.jsx";
import Select from "../components/Select.jsx";
import Textarea from "../components/Textarea.jsx";
import Loading from "../components/Loading.jsx";
import ErrorMessage from "../components/ErrorMessage.jsx";
import EmptyState from "../components/EmptyState.jsx";
import MaintenanceCard from "../components/MaintenanceCard.jsx";
import MaintenanceDetailModal from "../components/MaintenanceDetailModal.jsx";
import MaintenanceUpdateModal from "../components/MaintenanceUpdateModal.jsx";
import EscalationBanner from "../components/EscalationBanner.jsx";
import maintenanceService from "../services/maintenanceService.js";

const ISSUE_TYPE_OPTIONS = [
  { value: "plumbing", label: "Plumbing" },
  { value: "electrical", label: "Electrical" },
  { value: "hvac", label: "HVAC" },
  { value: "appliance", label: "Appliance" },
  { value: "general", label: "General" },
  { value: "other", label: "Other" },
];

const FILTER_TABS = [
  { key: "all", label: "All" },
  { key: "open", label: "Open" },
  { key: "in_progress", label: "In Progress" },
  { key: "resolved", label: "Resolved" },
];

const PRIORITY_FILTER_OPTIONS = [
  { value: "all", label: "All priorities" },
  { value: "urgent", label: "Urgent" },
  { value: "high", label: "High" },
  { value: "medium", label: "Medium" },
  { value: "low", label: "Low" },
];

const EMPTY_FORM = { issue_type: "plumbing", description: "" };
const MAX_PHOTO_BYTES = 1_000_000;

function readFileAsDataUrl(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

export default function Maintenance() {
  const { currentUser } = useAuth();
  const canManageTickets = currentUser?.role === "staff" || currentUser?.role === "admin";

  const [maintenanceTickets, setMaintenanceTickets] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [form, setForm] = useState(EMPTY_FORM);
  const [photoDataUrl, setPhotoDataUrl] = useState(null);
  const [photoError, setPhotoError] = useState(null);
  const [formError, setFormError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [activeFilter, setActiveFilter] = useState("all");
  const [activePriority, setActivePriority] = useState("all");

  const [detailTicket, setDetailTicket] = useState(null);
  const [isDetailLoading, setIsDetailLoading] = useState(false);
  const [manageTicket, setManageTicket] = useState(null);
  const [escalationMessage, setEscalationMessage] = useState(null);

  async function loadTickets() {
    setIsLoading(true);
    setError(null);
    try {
      const response = await maintenanceService.getTickets();
      setMaintenanceTickets(response.data || []);
    } catch (err) {
      setError(err.message || "Unable to load maintenance requests.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadTickets();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const filteredTickets = useMemo(() => {
    return maintenanceTickets.filter((ticket) => {
      const matchesStatus = activeFilter === "all" || ticket.status === activeFilter;
      const matchesPriority = activePriority === "all" || ticket.priority === activePriority;
      return matchesStatus && matchesPriority;
    });
  }, [maintenanceTickets, activeFilter, activePriority]);

  function openModal() {
    setForm(EMPTY_FORM);
    setPhotoDataUrl(null);
    setPhotoError(null);
    setFormError(null);
    setIsModalOpen(true);
  }

  function closeModal() {
    if (isSubmitting) return;
    setIsModalOpen(false);
  }

  async function handlePhotoChange(event) {
    const file = event.target.files?.[0];
    if (!file) {
      setPhotoDataUrl(null);
      return;
    }
    if (file.size > MAX_PHOTO_BYTES) {
      setPhotoError("Photo must be smaller than 1 MB.");
      event.target.value = "";
      return;
    }
    setPhotoError(null);
    setPhotoDataUrl(await readFileAsDataUrl(file));
  }

  async function handleSubmit(event) {
    event.preventDefault();

    if (!form.description.trim()) {
      setFormError("Please describe the issue.");
      return;
    }

    setIsSubmitting(true);
    setFormError(null);

    try {
      const created = await maintenanceService.createTicket({
        issue_type: form.issue_type,
        description: form.description.trim(),
        photo_data_url: photoDataUrl || undefined,
      });

      const ticket = created.data;
      setMaintenanceTickets((prev) => [ticket, ...prev]);
      setIsModalOpen(false);

      // Kick off AI triage; update the ticket in place once classified.
      try {
        const triaged = await maintenanceService.triageTicket(ticket.id);
        setMaintenanceTickets((prev) =>
          prev.map((item) => (item.id === ticket.id ? { ...item, ...triaged.data } : item))
        );
        if (triaged.data.escalated) {
          setEscalationMessage(
            `Ticket escalated: ${triaged.data.reason || "This issue requires urgent attention."}`
          );
        }
      } catch {
        // Triage failure should not block ticket creation; resident can still track it.
      }
    } catch (err) {
      setFormError(err.message || "Unable to submit the request.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleViewDetails(ticket) {
    setDetailTicket(ticket);
    setIsDetailLoading(true);
    try {
      const response = await maintenanceService.getTicket(ticket.id);
      setDetailTicket(response.data);
    } catch {
      // Keep the summary data already shown if the detail fetch fails.
    } finally {
      setIsDetailLoading(false);
    }
  }

  async function handleSaveUpdate(ticketId, payload) {
    const updated = await maintenanceService.updateTicket(ticketId, payload);
    setMaintenanceTickets((prev) =>
      prev.map((item) => (item.id === ticketId ? { ...item, ...updated.data } : item))
    );
    setManageTicket(null);
  }

  return (
    <div className="page">
      <PageHeader
        title="Maintenance"
        description="Report an issue or track your existing requests."
        action={
          <Button onClick={openModal}>
            <Plus size={16} />
            Submit Request
          </Button>
        }
      />

      {escalationMessage && (
        <EscalationBanner message={escalationMessage} onDismiss={() => setEscalationMessage(null)} />
      )}

      <div className="filter-tabs">
        {FILTER_TABS.map((tab) => (
          <button
            key={tab.key}
            className={`filter-tab${activeFilter === tab.key ? " active" : ""}`}
            onClick={() => setActiveFilter(tab.key)}
          >
            {tab.label}
          </button>
        ))}
        <label className="priority-filter">
          <span className="priority-filter__label">Priority</span>
          <select
            className="priority-filter__select"
            value={activePriority}
            onChange={(event) => setActivePriority(event.target.value)}
            aria-label="Filter maintenance requests by priority"
          >
            {PRIORITY_FILTER_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {isLoading && <Loading label="Loading maintenance requests..." />}
      {!isLoading && error && <ErrorMessage message={error} onRetry={loadTickets} />}
      {!isLoading && !error && filteredTickets.length === 0 && (
        <EmptyState message="No maintenance requests in this view yet." />
      )}

      {!isLoading && !error && filteredTickets.length > 0 && (
        <div className="ticket-list">
          {filteredTickets.map((ticket) => (
            <MaintenanceCard
              key={ticket.id}
              ticket={ticket}
              onViewDetails={handleViewDetails}
              onManage={canManageTickets ? setManageTicket : undefined}
              canManage={canManageTickets}
            />
          ))}
        </div>
      )}

      {isModalOpen && (
        <Modal title="Submit Maintenance Request" onClose={closeModal}>
          <form onSubmit={handleSubmit}>
            <Select
              id="issue_type"
              label="Issue type"
              options={ISSUE_TYPE_OPTIONS}
              value={form.issue_type}
              onChange={(event) => setForm((prev) => ({ ...prev, issue_type: event.target.value }))}
            />
            <Textarea
              id="description"
              label="Description"
              placeholder="Describe the issue, e.g. Kitchen sink is leaking"
              value={form.description}
              onChange={(event) => setForm((prev) => ({ ...prev, description: event.target.value }))}
              error={formError}
            />
            <div className="field">
              <label className="field__label" htmlFor="photo">
                Photo (optional)
              </label>
              <input id="photo" className="input" type="file" accept="image/*" onChange={handlePhotoChange} />
              {photoError && <span className="field__error">{photoError}</span>}
              {photoDataUrl && <img className="photo-preview" src={photoDataUrl} alt="Selected preview" />}
            </div>
            <div className="modal__actions">
              <SecondaryButton type="button" onClick={closeModal} disabled={isSubmitting}>
                Cancel
              </SecondaryButton>
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? "Submitting..." : "Submit Request"}
              </Button>
            </div>
          </form>
        </Modal>
      )}

      {detailTicket && (
        <MaintenanceDetailModal
          ticket={detailTicket}
          isLoading={isDetailLoading}
          onClose={() => setDetailTicket(null)}
        />
      )}

      {manageTicket && (
        <MaintenanceUpdateModal
          ticket={manageTicket}
          onClose={() => setManageTicket(null)}
          onSave={handleSaveUpdate}
        />
      )}
    </div>
  );
}
