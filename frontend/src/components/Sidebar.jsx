import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { Home, FileText, CreditCard, Wrench, MessageCircle, User, HelpCircle, LogOut } from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: Home, end: true },
  { to: "/lease", label: "My Lease", icon: FileText },
  { to: "/invoices", label: "Invoices", icon: CreditCard },
  { to: "/maintenance", label: "Maintenance", icon: Wrench },
  { to: "/assistant", label: "AI Assistant", icon: MessageCircle },
  { to: "/profile", label: "Profile", icon: User },
];

export default function Sidebar() {
  const { logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout(event) {
    event.preventDefault();
    logout();
    navigate("/login");
  }

  return (
    <aside className="sidebar">
      <div className="sidebar__logo">
        <span>MERIDIAN</span>
        <span>RESIDENCES</span>
      </div>

      <nav className="sidebar__nav">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) => `sidebar__link${isActive ? " active" : ""}`}
          >
            <Icon size={18} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar__footer">
        <a className="sidebar__link" href="#help">
          <HelpCircle size={18} />
          <span>Help</span>
        </a>
        <a className="sidebar__link" href="#logout" onClick={handleLogout}>
          <LogOut size={18} />
          <span>Log Out</span>
        </a>
      </div>
    </aside>
  );
}
