import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

export default function Login() {
  const { login, isSubmitting, error } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();

    const formData = new FormData(event.currentTarget);
    const submittedEmail = String(formData.get("email") || "").trim();
    const submittedPassword = String(formData.get("password") || "");

    try {
      await login(submittedEmail, submittedPassword);
      navigate("/");
    } catch (err) {
      // error already surfaced in context
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-panel auth-panel--gradient">
        <div className="auth-badge">Meridian Residences</div>
        <h1>Welcome back</h1>
        <p>
          Manage your home, maintenance requests, and resident services with ease.
        </p>
        <div className="auth-feature-list">
          <span>Live updates</span>
          <span>Track requests</span>
          <span>Resident dashboard</span>
        </div>
      </div>

      <div className="auth-panel auth-panel--form">
        <div className="auth-header-row">
          <div>
            <div className="eyebrow">Access portal</div>
            <h2>Sign in</h2>
          </div>
          <Link to="/register" className="auth-link">Register</Link>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="field">
            <label className="field__label" htmlFor="email">Email</label>
            <input
              id="email"
              name="email"
              type="email"
              className="input"
              autoComplete="username"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              required
            />
          </div>

          <div className="field">
            <label className="field__label" htmlFor="password">Password</label>
            <input
              id="password"
              name="password"
              type="password"
              className="input"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
            />
          </div>

          {error && <div className="form-error">{error}</div>}

          <button type="submit" className="btn btn--primary auth-button" disabled={isSubmitting}>
            {isSubmitting ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <div className="auth-demo-box">
          <strong>Demo accounts</strong>
          <span>Resident: anu.sharma@example.com / ResidentPass123!</span>
          <span>Staff: staff@meridian.com / StaffPass123!</span>
        </div>
      </div>
    </div>
  );
}
