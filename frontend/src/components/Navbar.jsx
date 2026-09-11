import React from "react";
import { Bell, User } from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";

export default function Navbar() {
  const { currentUser } = useAuth();

  return (
    <header className="navbar">
      <span className="navbar__brand">MERIDIAN RESIDENCES</span>
      <div className="navbar__right">
        <span className="navbar__role">{currentUser?.role || "Resident"}</span>
        <Bell size={18} />
        <User size={18} />
        <span>{currentUser?.email}</span>
      </div>
    </header>
  );
}
