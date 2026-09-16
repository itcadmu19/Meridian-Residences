import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import api from "../services/api";
import { getGuestLeases } from "../services/leaseService";

const AuthContext = createContext(null);

const TOKEN_KEY = "access_token";
const USER_KEY = "auth_user";

// There is no real "display name" from the backend (TokenResponse only
// carries guest_id/unit_id/role) - derive a friendly one from the email
// typed at login, e.g. "demo.resident@..." -> "Demo Resident".
function displayNameFromEmail(email) {
  const local = email.split("@")[0];
  return local
    .split(/[._-]+/)
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

function loadStoredUser() {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

async function bootstrapSelectedLease(user) {
  if (user.role !== "resident") return;
  try {
    const leases = await getGuestLeases(user.guest_id);
    const active = leases.find((lease) => lease.status === "active") || leases[0];
    if (active) {
      localStorage.setItem("selected_lease_id", active.id);
    }
  } catch {
    // ignore - Dashboard/Lease will fall back to demo data until this succeeds
  }
}

export function AuthProvider({ children }) {
  const [currentUser, setCurrentUser] = useState(loadStoredUser);
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    function handleUnauthorized() {
      setCurrentUser(null);
    }
    window.addEventListener("auth:unauthorized", handleUnauthorized);
    return () => window.removeEventListener("auth:unauthorized", handleUnauthorized);
  }, []);

  // A session restored from localStorage (page refresh, reopened tab) never
  // ran login()'s bootstrap - if selected_lease_id is missing, Dashboard/
  // Lease fall back to a fake "lease-demo-001" id forever, which the
  // backend correctly rejects as invalid, permanently showing demo data
  // until the next fresh login. Re-derive it here too so a restored session
  // self-heals instead of staying stuck on demo data.
  useEffect(() => {
    if (currentUser?.role === "resident" && !localStorage.getItem("selected_lease_id")) {
      bootstrapSelectedLease(currentUser);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentUser?.guest_id]);

  async function login(email, password, role = "resident") {
    setIsSubmitting(true);
    setError(null);
    try {
      const response = await api.post("/auth/login", { email, password, role });
      const token = response.data;
      const user = {
        guest_id: token.guest_id,
        unit_id: token.unit_id,
        role: token.role,
        email,
        name: displayNameFromEmail(email),
      };
      localStorage.setItem(TOKEN_KEY, token.access_token);
      localStorage.setItem(USER_KEY, JSON.stringify(user));
      setCurrentUser(user);

      // Dashboard/Lease default to this key for "which lease am I looking
      // at" - pick the resident's active lease (or their first) so those
      // pages show real data right after login instead of falling back to
      // demo data. Not fatal if it fails - they'll just show demo data.
      if (user.role === "resident") {
        try {
          const leases = await getGuestLeases(user.guest_id);
          const active = leases.find((lease) => lease.status === "active") || leases[0];
          if (active) {
            localStorage.setItem("selected_lease_id", active.id);
          }
        } catch {
          // ignore
        }
      }

      return user;
    } catch {
      setError("Invalid email or password.");
      throw new Error("Invalid email or password.");
    } finally {
      setIsSubmitting(false);
    }
  }

  async function register(payload) {
    setIsSubmitting(true);
    setError(null);
    try {
      const response = await api.post("/auth/register", payload);
      const token = response.data;
      const user = {
        guest_id: token.guest_id,
        unit_id: token.unit_id,
        role: token.role,
        email: token.email,
        name: token.name,
      };
      localStorage.setItem(TOKEN_KEY, token.access_token);
      localStorage.setItem(USER_KEY, JSON.stringify(user));
      setCurrentUser(user);

      if (user.role === "resident") {
        try {
          const leases = await getGuestLeases(user.guest_id);
          const active = leases.find((lease) => lease.status === "active") || leases[0];
          if (active) {
            localStorage.setItem("selected_lease_id", active.id);
          }
        } catch {
          // ignore
        }
      }

      return user;
    } catch (err) {
      const message =
        err?.response?.status === 409
          ? "An account with this email already exists."
          : "Could not create your account. Please try again.";
      setError(message);
      throw new Error(message);
    } finally {
      setIsSubmitting(false);
    }
  }

  function logout() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem("selected_lease_id");
    setCurrentUser(null);
  }

  const value = useMemo(
    // isBootstrapping stays false always - login is synchronous from
    // localStorage now, kept only so existing effects that gate on it
    // (Dashboard.jsx, Lease.jsx) don't need to change.
    () => ({ currentUser, isBootstrapping: false, login, register, logout, error, isSubmitting }),
    [currentUser, error, isSubmitting]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
