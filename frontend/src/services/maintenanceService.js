import api from "./api";

// Member 3 — Maintenance service layer (frozen API contract, section 9.4 / 13).
const maintenanceService = {
  createTicket(payload) {
    return api.post("/maintenance-tickets", payload);
  },

  getTickets(params = {}) {
    return api.get("/maintenance-tickets", { params });
  },

  getTicket(ticketId) {
    return api.get(`/maintenance-tickets/${ticketId}`);
  },

  updateTicket(ticketId, payload) {
    return api.patch(`/maintenance-tickets/${ticketId}`, payload);
  },

  triageTicket(ticketId) {
    return api.post(`/maintenance-tickets/${ticketId}/triage`);
  },
};

export default maintenanceService;
