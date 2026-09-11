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

  updatePaymentStatus(invoiceId, paymentStatus) {
    return api.patch(`/invoices/${invoiceId}/payment-status`, {
      payment_status: paymentStatus,
    });
  },
};

export default invoiceService;
