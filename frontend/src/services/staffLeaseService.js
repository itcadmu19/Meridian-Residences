import api from "./api";

// App-wide Login feature: staff now use the same login/token as everyone
// else (services/api.js), so this no longer needs its own axios instance.

export async function getStaffLeases(statusFilter) {
  const response = await api.get("/staff/leases", {
    params: statusFilter ? { status: statusFilter } : undefined,
  });
  return response.data?.data ?? response.data;
}

export async function updateLease(leaseId, payload) {
  const response = await api.patch(`/leases/${leaseId}`, payload);
  return response.data?.data ?? response.data;
}

export async function activateLease(leaseId) {
  const response = await api.post(`/leases/${leaseId}/activate`);
  return response.data?.data ?? response.data;
}

export async function renewLease(leaseId, newEndDate) {
  const response = await api.post(`/leases/${leaseId}/renew`, {
    new_end_date: newEndDate,
  });
  return response.data?.data ?? response.data;
}

export async function terminateLease(leaseId) {
  const response = await api.post(`/leases/${leaseId}/terminate`);
  return response.data?.data ?? response.data;
}

// AI-Generated Lease Agreement workflow (staff side).

export async function generateAgreement(leaseId, payload) {
  const response = await api.post(`/leases/${leaseId}/generate-agreement`, payload);
  return response.data?.data ?? response.data;
}

export async function getAgreement(leaseId) {
  const response = await api.get(`/leases/${leaseId}/agreement-document`);
  return response.data?.data ?? response.data;
}

export async function updateAgreementDraft(leaseId, content) {
  const response = await api.put(`/leases/${leaseId}/agreement-document`, { content });
  return response.data?.data ?? response.data;
}

export async function sendAgreement(leaseId) {
  const response = await api.post(`/leases/${leaseId}/agreement-document/send`);
  return response.data?.data ?? response.data;
}

export async function getEnquiries(leaseId) {
  const response = await api.get(`/leases/${leaseId}/enquiries`);
  return response.data?.data ?? response.data;
}

export async function respondToEnquiry(leaseId, enquiryId, payload) {
  const response = await api.post(`/leases/${leaseId}/enquiries/${enquiryId}/respond`, payload);
  return response.data?.data ?? response.data;
}
