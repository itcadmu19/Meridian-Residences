import api from "./api";

export async function getInvoices(params = {}) {
  const response = await api.get("/invoices", { params });
  return response.data?.data ?? response.data;
}

export async function getInvoice(invoiceId) {
  const response = await api.get(`/invoices/${invoiceId}`);
  return response.data?.data ?? response.data;
}

export async function generateInvoice(payload) {
  // Returns the full envelope (not just .data) so callers can check
  // `message === "Existing invoice returned"` to tell a fresh invoice
  // apart from one that already existed for that month.
  const response = await api.post("/invoices/generate", payload);
  return response.data;
}

export async function generateBatch(payload) {
  const response = await api.post("/invoices/generate-batch", payload);
  return response.data?.data ?? response.data;
}

export async function markOverdue() {
  const response = await api.post("/invoices/mark-overdue");
  return response.data?.data ?? response.data;
}

export async function updatePaymentStatus(invoiceId, paymentStatus) {
  const response = await api.patch(`/invoices/${invoiceId}/payment-status`, {
    payment_status: paymentStatus,
  });
  return response.data?.data ?? response.data;
}

export async function extendDueDate(invoiceId, dueDate) {
  const response = await api.patch(`/invoices/${invoiceId}/due-date`, { due_date: dueDate });
  return response.data?.data ?? response.data;
}

export async function submitPayment(invoiceId) {
  const response = await api.post(`/invoices/${invoiceId}/pay`);
  return response.data?.data ?? response.data;
}

export async function getInsights(params = {}) {
  // Longer timeout than api.js's 8s default - this call may try (and time
  // out on) a local Ollama server server-side before falling back, and
  // that fallback path alone can take a couple of seconds. See
  // ai/ollama_client.py's timeout split for the matching backend-side fix.
  const response = await api.get("/invoices/insights", { params, timeout: 20000 });
  return response.data?.data ?? response.data;
}

export async function downloadInvoicePdf(invoiceId) {
  const response = await api.get(`/invoices/${invoiceId}/pdf`, { responseType: "blob" });
  return response.data;
}

export async function exportInvoicesPdf(params = {}) {
  const response = await api.get("/invoices/export/pdf", { params, responseType: "blob" });
  return response.data;
}
