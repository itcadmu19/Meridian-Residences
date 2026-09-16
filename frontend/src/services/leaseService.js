import api from "./api";

export async function getLease(leaseId) {
  const response = await api.get(`/leases/${leaseId}`);
  return response.data?.data ?? response.data;
}

export async function getLeaseSummary(leaseId) {
  const response = await api.get(`/leases/${leaseId}/summary`);
  return response.data?.data ?? response.data;
}

export async function getGuestLeases(guestId) {
  const response = await api.get(`/guests/${guestId}/leases`);
  return response.data?.data ?? response.data;
}

export async function downloadLeaseAgreement(leaseId) {
  // Must go through the authenticated axios instance (not a plain <a href>)
  // so the bearer token is attached - a static link wouldn't carry auth.
  const response = await api.get(`/leases/${leaseId}/agreement`, {
    responseType: "blob",
  });
  return response.data;
}

export async function requestLeaseRenewal(leaseId) {
  const response = await api.post(`/leases/${leaseId}/renewal-request`);
  return response.data?.data ?? response.data;
}

// AI-Generated Lease Agreement workflow (resident side). Same endpoints the
// staff service calls - authorization (own lease only) is enforced server-
// side via authorize_lease_access, not by which service file makes the call.

export async function getAgreementDocument(leaseId) {
  const response = await api.get(`/leases/${leaseId}/agreement-document`);
  return response.data?.data ?? response.data;
}

export async function downloadAgreementDocumentPdf(leaseId) {
  const response = await api.get(`/leases/${leaseId}/agreement-document/pdf`, {
    responseType: "blob",
  });
  return response.data;
}

export async function acceptAgreementDocument(leaseId) {
  const response = await api.post(`/leases/${leaseId}/agreement-document/accept`);
  return response.data?.data ?? response.data;
}

export async function getLeaseEnquiries(leaseId) {
  const response = await api.get(`/leases/${leaseId}/enquiries`);
  return response.data?.data ?? response.data;
}

export async function createLeaseEnquiry(leaseId, payload) {
  const response = await api.post(`/leases/${leaseId}/enquiries`, payload);
  return response.data?.data ?? response.data;
}