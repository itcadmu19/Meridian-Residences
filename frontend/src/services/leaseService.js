import api from "./api";

const leaseService = {
  getLease(leaseId) {
    return api.get(`/leases/${leaseId}`);
  },

  getGuestLeases(guestId) {
    return api.get(`/guests/${guestId}/leases`);
  },

  getLeaseSummary(leaseId) {
    return api.get(`/leases/${leaseId}/summary`);
  },
};

export default leaseService;
