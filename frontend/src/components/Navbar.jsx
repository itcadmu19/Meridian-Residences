import React, { useEffect, useRef, useState } from "react";
import { Bell, ChevronDown, LogOut } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getLeaseSummary } from "../services/leaseService";

const ROLE_LABELS = {
  resident: "Resident",
  staff: "Staff",
  admin: "Admin",
};

// There is no dedicated notifications feature/endpoint anywhere in the
// backend contract - this reuses the same recent-activity data already
// shown on the Dashboard (via /leases/{id}/summary) rather than inventing
// a separate notifications system.
export default function Navbar() {
  const { currentUser, logout } = useAuth();
  const navigate = useNavigate();
  const displayName = currentUser?.name || "Resident";
  const roleLabel = ROLE_LABELS[currentUser?.role] || "Resident";

  const [open, setOpen] = useState(false);
  const [activities, setActivities] = useState(null);
  const [loading, setLoading] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const wrapperRef = useRef(null);
  const profileRef = useRef(null);

  useEffect(() => {
    function handleClickOutside(event) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setOpen(false);
      }
      if (profileRef.current && !profileRef.current.contains(event.target)) {
        setProfileOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  async function toggleNotifications() {
    const nextOpen = !open;
    setOpen(nextOpen);

    if (nextOpen && activities === null) {
      setLoading(true);
      try {
        const leaseId =
          localStorage.getItem("selected_lease_id") || "lease-demo-001";
        const summary = await getLeaseSummary(leaseId);
        setActivities(summary?.activities || []);
      } catch {
        setActivities([]);
      } finally {
        setLoading(false);
      }
    }
  }

  function handleSignOut() {
    setProfileOpen(false);
    logout();
    navigate("/login", { replace: true });
  }

  const unreadCount = activities?.length || 0;

  return (
    <header className="top-navbar">
      <div className="navbar-actions">
        <div className="notification-wrapper" ref={wrapperRef}>
          <button
            className="icon-button notification-button"
            aria-label="Notifications"
            onClick={toggleNotifications}
          >
            <Bell size={20} strokeWidth={1.8} />
            {unreadCount > 0 && (
              <span className="notification-dot">{unreadCount}</span>
            )}
          </button>

          {open && (
            <div className="notification-panel">
              <div className="notification-panel-heading">Recent activity</div>
              {loading && (
                <div className="notification-panel-empty">Loading…</div>
              )}
              {!loading && activities?.length === 0 && (
                <div className="notification-panel-empty">
                  Nothing new right now.
                </div>
              )}
              {!loading &&
                activities?.slice(0, 5).map((activity) => (
                  <div className="notification-panel-item" key={activity.id}>
                    <strong>{activity.title}</strong>
                    <span>{activity.description}</span>
                  </div>
                ))}
            </div>
          )}
        </div>

        <div className="notification-wrapper" ref={profileRef}>
          <button
            className="profile-menu"
            aria-label="Account menu"
            onClick={() => setProfileOpen((prev) => !prev)}
          >
            <span className="avatar">
              {displayName.slice(0, 1).toUpperCase()}
            </span>
            <span className="profile-copy">
              <strong>{displayName}</strong>
              <small>{roleLabel}</small>
            </span>
            <ChevronDown size={16} />
          </button>

          {profileOpen && (
            <div className="notification-panel profile-dropdown">
              <div className="notification-panel-item profile-dropdown-identity">
                <strong>{displayName}</strong>
                <span>{currentUser?.email}</span>
              </div>
              <button className="profile-dropdown-signout" onClick={handleSignOut}>
                <LogOut size={15} />
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}
