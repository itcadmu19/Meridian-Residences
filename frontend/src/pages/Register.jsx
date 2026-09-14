import React, { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext.jsx";

const roleOptions = [
  { label: "Resident", value: "resident" },
  { label: "Staff", value: "staff" },
];

export default function Register() {
  const { register, isSubmitting, error } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    role: "resident",
    unit_number: "",
    unit_type: "2BHK",
  });

  const passwordStrength = useMemo(() => {
    if (!form.password) return { label: "No password", tone: "neutral" };
    if (form.password.length >= 12 && /[A-Z]/.test(form.password) && /\d/.test(form.password) && /[^A-Za-z\d]/.test(form.password)) {
      return { label: "Strong", tone: "strong" };
    }
    if (form.password.length >= 8) {
      return { label: "Medium", tone: "medium" };
    }
    return { label: "Weak", tone: "weak" };
  }, [form.password]);

  async function handleSubmit(event) {
    event.preventDefault();
    const payload = {
      ...form,
      unit_number: form.unit_number.trim() || (form.role === "staff" ? "STAFF-01" : "101"),
      unit_type: form.unit_type.trim() || (form.role === "staff" ? "Staff" : "2BHK"),
    };

    try {
      await register(payload);
      navigate("/");
    } catch (err) {
      // error already surfaced in context
    }
  }

  function handleChange(event) {
    const { name, value } = event.target;
    setForm((current) => ({ ...current, [name]: value }));
  }

  return (
    <div className="auth-page">
      <div className="auth-panel auth-panel--gradient">
        <div className="auth-badge">Meridian Residences</div>
        <h1>Create your account</h1>
        <p>
          Access your apartment, maintenance requests, and resident services in one place.
        </p>
        <div className="auth-feature-list">
          <span>Resident portal</span>
          <span>Maintenance tracking</span>
          <span>Secure access</span>
        </div>
      </div>

      <div className="auth-panel auth-panel--form">
        <div className="auth-header-row">
          <div>
            <div className="eyebrow">Welcome</div>
            <h2>Sign up</h2>
          </div>
          <Link to="/login" className="auth-link">Sign in</Link>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <div className="field-group field-group--two">
            <div className="field">
              <label className="field__label" htmlFor="name">Full name</label>
              <input id="name" name="name" className="input" value={form.name} onChange={handleChange} required />
            </div>
            <div className="field">
              <label className="field__label" htmlFor="role">Role</label>
              <select id="role" name="role" className="input" value={form.role} onChange={handleChange}>
                {roleOptions.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="field">
            <label className="field__label" htmlFor="email">Email</label>
            <input id="email" name="email" type="email" className="input" value={form.email} onChange={handleChange} required />
          </div>

          <div className="field">
            <label className="field__label" htmlFor="password">Password</label>
            <input id="password" name="password" type="password" className="input" value={form.password} onChange={handleChange} required />
            <div className={`password-strength password-strength--${passwordStrength.tone}`}>
              {passwordStrength.label}
            </div>
          </div>

          <div className="field-group field-group--two">
            <div className="field">
              <label className="field__label" htmlFor="unit_number">Unit number</label>
              <input id="unit_number" name="unit_number" className="input" value={form.unit_number} onChange={handleChange} placeholder={form.role === "staff" ? "STAFF-01" : "101"} />
            </div>
            <div className="field">
              <label className="field__label" htmlFor="unit_type">Unit type</label>
              <input id="unit_type" name="unit_type" className="input" value={form.unit_type} onChange={handleChange} placeholder={form.role === "staff" ? "Staff" : "2BHK"} />
            </div>
          </div>

          {error && <div className="form-error">{error}</div>}

          <button type="submit" className="btn btn--primary auth-button" disabled={isSubmitting}>
            {isSubmitting ? "Creating account..." : "Create account"}
          </button>
        </form>
      </div>
    </div>
  );
}
