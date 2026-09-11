import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json"
  }
});

// Attach auth token in one interceptor.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("meridian_auth_token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Normalize errors in one place. Every rejected promise carries a
// predictable { message, errorCode, status } shape so pages never need
// to inspect raw Axios/response internals.
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status ?? null;
    const body = error.response?.data;

    const normalized = {
      status,
      message: body?.message || "Something went wrong. Please try again.",
      errorCode: body?.error_code || "UNKNOWN_ERROR"
    };

    return Promise.reject(normalized);
  }
);

export default api;
