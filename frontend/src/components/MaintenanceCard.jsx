import React from "react";
import { Clock, Eye, Pencil } from "lucide-react";
import Card from "./Card.jsx";
import StatusBadge from "./StatusBadge.jsx";
import PriorityBadge from "./PriorityBadge.jsx";

function formatDate(value) {
  if (!value) return "—";
  return new Date(value).toLocaleDateString(undefined, {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

const ISSUE_TYPE_LABELS = {
  plumbing: "Plumbing",
  electrical: "Electrical",
  hvac: "HVAC",
  appliance: "Appliance",
  general: "General",
  other: "Other",
};

export default function MaintenanceCard({ ticket, onViewDetails, onManage, canManage = false }) {
  const shortId = ticket.id ? `MT-${String(ticket.id).slice(-3).toUpperCase()}` : "MT-NEW";

  return (
    <Card>
      <div className="ticket-card__top">
        <div>
          <div className="ticket-card__id">{shortId}</div>
          <div className="ticket-card__title">
            {ISSUE_TYPE_LABELS[ticket.issue_type] || ticket.issue_type}
          </div>
          <p className="ticket-card__description">{ticket.description}</p>
        </div>
        <div className="ticket-card__badges">
          <PriorityBadge priority={ticket.priority} />
          <StatusBadge status={ticket.status} />
        </div>
      </div>

      {ticket.photo_data_url && (
        <img className="ticket-card__photo" src={ticket.photo_data_url} alt="Reported issue" />
      )}

      <div className="ticket-card__meta">
        <Clock size={14} />
        <span className="ticket-card__date">Submitted: {formatDate(ticket.created_at)}</span>
        {ticket.resolved_at && (
          <span className="ticket-card__date">· Resolved: {formatDate(ticket.resolved_at)}</span>
        )}
        {ticket.vendor_queue && (
          <span className="ticket-card__date">· Vendor queue: {ticket.vendor_queue}</span>
        )}
        {ticket.escalated && <span className="badge badge--error">ESCALATED</span>}
      </div>

      <div className="ticket-card__actions">
        <button type="button" className="text-link" onClick={() => onViewDetails(ticket)}>
          <Eye size={14} />
          View Details
        </button>
        {canManage && onManage && (
          <button type="button" className="text-link" onClick={() => onManage(ticket)}>
            <Pencil size={14} />
            Update
          </button>
        )}
      </div>
    </Card>
  );
}

