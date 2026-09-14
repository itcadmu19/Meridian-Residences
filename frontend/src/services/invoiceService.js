import api from "./api";

const invoiceService = {
  getInvoices(params = {}) {
    return api.get("/invoices", { params });
  },

  getInvoice(invoiceId) {
    return api.get(`/invoices/${invoiceId}`);
  },

  generateInvoice(payload) {
    return api.post("/invoices/generate", payload);
  },

  generateBatch(payload) {
    return api.post("/invoices/generate-batch", payload);
  },

  markOverdue() {
    return api.post("/invoices/mark-overdue");
  },

  updatePaymentStatus(invoiceId, paymentStatus) {
    return api.patch(`/invoices/${invoiceId}/payment-status`, {
      payment_status: paymentStatus,
    });
  },

  extendDueDate(invoiceId, dueDate) {
    return api.patch(`/invoices/${invoiceId}/due-date`, { due_date: dueDate });
  },

  submitPayment(invoiceId) {
    return api.post(`/invoices/${invoiceId}/pay`);
  },

  getInsights(params = {}) {
    return api.get("/invoices/insights", { params });
  },

  downloadInvoicePdf(invoiceId) {
    return api.get(`/invoices/${invoiceId}/pdf`, { responseType: "blob" });
  },

  exportInvoicesPdf(params = {}) {
    return api.get("/invoices/export/pdf", { params, responseType: "blob" });
  },
};

export default invoiceService;
