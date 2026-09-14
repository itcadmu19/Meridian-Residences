import React from "react";
import { AlertTriangle, Clock } from "lucide-react";
import Modal from "./Modal.jsx";
import StatusBadge from "./StatusBadge.jsx";
import PriorityBadge from "./PriorityBadge.jsx";
import Loading from "./Loading.jsx";

function formatDateTime(value) {
  if (!value) return "—";
  return new Date(value).toLocaleString(undefined, {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export default function MaintenanceDetailModal({ ticket, isLoading, onClose }) {
  return (
    <Modal title="Maintenance Ticket Details" onClose={onClose}>
      {isLoading && <Loading label="Loading ticket details..." />}
      {!isLoading && ticket && (
        <div className="ticket-detail">
          <div className="ticket-detail__badges">
            <PriorityBadge priority={ticket.priority} />
            <StatusBadge status={ticket.status} />
            {ticket.escalated && <span className="badge badge--error">ESCALATED</span>}
          </div>

          <p className="ticket-detail__description">{ticket.description}</p>

          {ticket.photo_data_url && (
            <img className="ticket-detail__photo" src={ticket.photo_data_url} alt="Reported issue" />
          )}

          {ticket.triage_reason && (
            <div className="ticket-detail__reason">
              <AlertTriangle size={15} />
              <span>{ticket.triage_reason}</span>
            </div>
          )}

          <div className="ticket-detail__timeline">
            <div className="ticket-detail__timeline-item">
              <Clock size={14} />
              <span>Submitted</span>
              <strong>{formatDateTime(ticket.created_at)}</strong>
            </div>
            <div className="ticket-detail__timeline-item">
              <Clock size={14} />
              <span>Last updated</span>
              <strong>{formatDateTime(ticket.updated_at)}</strong>
            </div>
            {ticket.resolved_at && (
              <div className="ticket-detail__timeline-item">
                <Clock size={14} />
                <span>Resolved</span>
                <strong>{formatDateTime(ticket.resolved_at)}</strong>
              </div>
            )}
            {ticket.vendor_queue && (
              <div className="ticket-detail__timeline-item">
                <Clock size={14} />
                <span>Vendor queue</span>
                <strong>{ticket.vendor_queue}</strong>
              </div>
            )}
          </div>
        </div>
      )}
    </Modal>
  );
}
