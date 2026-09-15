import axios from "axios";

// Shared Axios client — the only place allowed to configure baseURL, headers
// and error normalization. Pages/components must call services, not Axios directly.
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("auth_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const envelope = error.response?.data;
    const detail = envelope?.detail;
    const isStaffAuthorizationFailure =
      error.response?.status === 403 &&
      (detail?.error_code === "FORBIDDEN" || detail?.message?.includes("staff"));

    if (error.response?.status === 401 || isStaffAuthorizationFailure) {
      localStorage.removeItem("auth_token");
      localStorage.removeItem("auth_user");
      window.dispatchEvent(new Event("auth:unauthorized"));
    }

    const normalized = {
      success: false,
      data: null,
      message:
        detail?.message || envelope?.message || error.message || "Unexpected error",
      error_code: detail?.error_code || envelope?.error_code || "UNKNOWN_ERROR",
      status: error.response?.status || null,
    };
    return Promise.reject(normalized);
  }
);

export default api;
