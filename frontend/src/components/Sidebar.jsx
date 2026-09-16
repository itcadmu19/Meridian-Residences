import React from "react";
import {
  Bot,
  Building2,
  FileText,
  Home,
  Receipt,
  Settings,
  Wrench,
} from "lucide-react";
import { NavLink } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function buildLinks(isStaff) {
  return [
    { to: "/dashboard", label: "Dashboard", icon: Home },
    { to: "/lease", label: isStaff ? "Lease Directory" : "My Lease", icon: FileText },
    { to: "/invoices", label: "Invoices", icon: Receipt },
    { to: "/maintenance", label: "Maintenance", icon: Wrench },
    { to: "/assistant", label: "AI Assistant", icon: Bot, residentOnly: true },
  ];
}

export default function Sidebar() {
  const { currentUser } = useAuth();
  const isStaff = currentUser?.role === "staff" || currentUser?.role === "admin";
  const visibleLinks = buildLinks(isStaff).filter((link) => !link.residentOnly || currentUser?.role === "resident");

  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">
          <Building2 size={21} strokeWidth={1.8} />
        </div>
        <div>
          <div className="brand-name">MERIDIAN</div>
          <div className="brand-subtitle">RESIDENCES</div>
        </div>
      </div>

      <div className="sidebar-section-label">MAIN MENU</div>

      <nav className="sidebar-nav">
        {visibleLinks.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `sidebar-link ${isActive ? "active" : ""}`
            }
          >
            <Icon size={19} strokeWidth={1.8} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-bottom">
        <NavLink
          to="/profile"
          className={({ isActive }) =>
            `sidebar-link ${isActive ? "active" : ""}`
          }
        >
          <Settings size={19} strokeWidth={1.8} />
          <span>Profile & Settings</span>
        </NavLink>

        <div className="sidebar-footer">© 2026 Meridian Residences</div>
      </div>
    </aside>
  );
}