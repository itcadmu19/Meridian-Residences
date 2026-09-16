import React, { useState } from "react";
import { Briefcase, Building2, Home, Lock, Mail, User } from "lucide-react";
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

export default function Register() {
  const { currentUser, register, error, isSubmitting } = useAuth();
  const navigate = useNavigate();

  const [selectedRole, setSelectedRole] = useState("resident");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [unitNumber, setUnitNumber] = useState("");
  const [unitType, setUnitType] = useState("");

  if (currentUser) {
    return <Navigate to="/dashboard" replace />;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    try {
      await register({
        name,
        email,
        password,
        role: selectedRole,
        unit_number: unitNumber.trim() || undefined,
        unit_type: unitType.trim() || undefined,
      });
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
              <h1>Join Meridian Residences today.</h1>
              <p>Create your account to manage your lease, invoices and maintenance.</p>
              <div className="hero-line" />
              <span className="hero-tagline">Your home. Our priority.</span>
            </div>
          </div>
        </section>

        <section className="login-form-panel">
          <div className="login-card">
            <span className="section-kicker">SIGN UP</span>
            <h1>Create your account</h1>
            <p>Choose your role and fill in your details to get started.</p>

            <div className="role-select-group">
              {ROLES.map(({ key, label, icon: Icon, description }) => (
                <button
                  key={key}
                  type="button"
                  className={`role-select-option ${selectedRole === key ? "active" : ""}`}
                  onClick={() => setSelectedRole(key)}
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
                Full name
                <div className="input-icon-wrapper">
                  <User size={15} />
                  <input
                    type="text"
                    value={name}
                    onChange={(event) => setName(event.target.value)}
                    placeholder="Jane Doe"
                    autoComplete="name"
                    required
                  />
                </div>
              </label>
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
                    autoComplete="new-password"
                    minLength={8}
                    required
                  />
                </div>
              </label>
              <label>
                {selectedRole === "staff" ? "Staff ID (optional)" : "Unit number (optional)"}
                <input
                  type="text"
                  value={unitNumber}
                  onChange={(event) => setUnitNumber(event.target.value)}
                  placeholder={selectedRole === "staff" ? "STAFF-01" : "e.g. 305"}
                />
              </label>
              {selectedRole === "resident" && (
                <label>
                  Unit type (optional)
                  <input
                    type="text"
                    value={unitType}
                    onChange={(event) => setUnitType(event.target.value)}
                    placeholder="e.g. 2BHK"
                  />
                </label>
              )}

              {error && <div className="demo-notice demo-notice--error">{error}</div>}

              <div className="drawer-form-actions login-form-actions">
                <button type="submit" className="primary-button" disabled={isSubmitting}>
                  {isSubmitting ? "Creating account…" : `Sign up as ${selectedRole === "staff" ? "Staff" : "Resident"}`}
                </button>
              </div>
            </form>

            <p className="login-signup-link">
              Already have an account? <Link to="/login">Sign in</Link>
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
