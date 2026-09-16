import React, { useState } from "react";
import { Briefcase, Building2, Home, Lock, Mail } from "lucide-react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const LOGIN_HERO_IMAGE =
  "https://images.unsplash.com/photo-1759073254456-06026e026c08?auto=format&fit=crop&fm=jpg&q=90&w=1600";

const ROLES = [
  {
    key: "resident",
    label: "Resident",
    icon: Home,
    description: "View your lease, invoices & maintenance",
  },
  {
    key: "staff",
    label: "Staff",
    icon: Briefcase,
    description: "Manage leases, billing & requests",
  },
];

function roleMatchesCategory(role, category) {
  if (category === "staff") return role === "staff" || role === "admin";
  return role === "resident";
}

export default function Login() {
  const { currentUser, login, logout, error, isSubmitting } = useAuth();
  const navigate = useNavigate();

  const [selectedRole, setSelectedRole] = useState("resident");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [roleError, setRoleError] = useState(null);

  if (currentUser) {
    return <Navigate to="/dashboard" replace />;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setRoleError(null);
    try {
      const user = await login(email, password, selectedRole);
      if (!roleMatchesCategory(user.role, selectedRole)) {
        logout();
        const actualLabel = user.role === "resident" ? "Resident" : "Staff";
        setRoleError(
          `This account is registered as ${actualLabel}. Select "${actualLabel}" above and sign in again.`
        );
        return;
      }
      navigate("/dashboard", { replace: true });
    } catch {
      // error is already surfaced via useAuth().error
    }
  }

  return (
    <div className="login-page">
      <div className="login-shell">
        <section
          className="login-hero"
          style={{ backgroundImage: `url(${LOGIN_HERO_IMAGE})` }}
        >
          <div className="login-hero-overlay">
            <div className="brand login-brand">
              <div className="brand-mark">
                <Building2 size={21} strokeWidth={1.8} />
              </div>
              <div>
                <div className="brand-name">MERIDIAN</div>
                <div className="brand-subtitle">RESIDENCES</div>
              </div>
            </div>

            <div className="login-hero-copy">
              <h1>Everything about your home, in one place.</h1>
              <p>Lease, invoices and maintenance — managed with ease.</p>
              <div className="hero-line" />
              <span className="hero-tagline">Your home. Our priority.</span>
            </div>
          </div>
        </section>

        <section className="login-form-panel">
          <div className="login-card">
            <span className="section-kicker">SIGN IN</span>
            <h1>Welcome back</h1>
            <p>Choose your role and sign in to continue.</p>

            <div className="role-select-group">
              {ROLES.map(({ key, label, icon: Icon, description }) => (
                <button
                  key={key}
                  type="button"
                  className={`role-select-option ${selectedRole === key ? "active" : ""}`}
                  onClick={() => {
                    setSelectedRole(key);
                    setRoleError(null);
                  }}
                >
                  <span className="role-select-icon">
                    <Icon size={18} />
                  </span>
                  <span className="role-select-copy">
                    <strong>{label}</strong>
                    <small>{description}</small>
                  </span>
                </button>
              ))}
            </div>

            <form className="drawer-form login-fields" onSubmit={handleSubmit}>
              <label className="input-with-icon">
                Email
                <div className="input-icon-wrapper">
                  <Mail size={15} />
                  <input
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                    placeholder="you@example.com"
                    autoComplete="username"
                    required
                  />
                </div>
              </label>
              <label className="input-with-icon">
                Password
                <div className="input-icon-wrapper">
                  <Lock size={15} />
                  <input
                    type="password"
                    value={password}
                    onChange={(event) => setPassword(event.target.value)}
                    autoComplete="current-password"
                    required
                  />
                </div>
              </label>

              {(error || roleError) && (
                <div className="demo-notice demo-notice--error">{roleError || error}</div>
              )}

              <div className="drawer-form-actions login-form-actions">
                <button type="submit" className="primary-button" disabled={isSubmitting}>
                  {isSubmitting ? "Signing in…" : `Sign in as ${selectedRole === "staff" ? "Staff" : "Resident"}`}
                </button>
              </div>
            </form>

            <p className="login-signup-link">
              Don&apos;t have an account? <Link to="/register">Sign up</Link>
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
