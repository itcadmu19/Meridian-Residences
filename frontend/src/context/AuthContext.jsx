import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import authService from "../services/authService.js";

const STORAGE_KEY = "auth_token";
const USER_STORAGE_KEY = "auth_user";

function loadStoredUser() {
  try {
    const raw = localStorage.getItem(USER_STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

const AuthContext = createContext(null);

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

  async function login(email, password) {
    setIsSubmitting(true);
    setError(null);
    try {
      const token = await authService.login(email, password);
      const user = { guest_id: token.guest_id, unit_id: token.unit_id, role: token.role, email };

      localStorage.setItem(STORAGE_KEY, token.access_token);
      localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
      setCurrentUser(user);
      return user;
    } catch (err) {
      setError(err.message || "Invalid email or password");
      throw err;
    } finally {
      setIsSubmitting(false);
    }
  }

  function logout() {
    localStorage.removeItem(STORAGE_KEY);
    localStorage.removeItem(USER_STORAGE_KEY);
    setCurrentUser(null);
  }

  const value = useMemo(
    () => ({ currentUser, login, logout, error, isSubmitting }),
    [currentUser, error, isSubmitting]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}

