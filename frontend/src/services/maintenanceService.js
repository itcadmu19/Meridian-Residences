import api from "./api";

export async function getTickets(params = {}) {
  const response = await api.get("/maintenance-tickets", { params });
  return response.data?.data ?? response.data;
}

export async function getTicket(ticketId) {
  const response = await api.get(`/maintenance-tickets/${ticketId}`);
  return response.data?.data ?? response.data;
}

export async function createTicket(payload) {
  const response = await api.post("/maintenance-tickets", payload);
  return response.data?.data ?? response.data;
}

export async function updateTicket(ticketId, payload) {
  const response = await api.patch(`/maintenance-tickets/${ticketId}`, payload);
  return response.data?.data ?? response.data;
}

export async function deleteTicket(ticketId) {
  await api.delete(`/maintenance-tickets/${ticketId}`);
}

export async function triageTicket(ticketId) {
  const response = await api.post(`/maintenance-tickets/${ticketId}/triage`);
  return response.data?.data ?? response.data;
}
