import React from "react";
import {
  BadgeCheck,
  Building2,
  CalendarDays,
  Check,
  Fingerprint,
  KeyRound,
  Mail,
  ShieldCheck,
} from "lucide-react";
import { useAuth } from "../context/AuthContext";

const ROLE_LABELS = {
  resident: "Resident",
  staff: "Staff",
  admin: "Admin",
};

function formatIdentifier(value) {
  if (!value) return "Not assigned";
  const identifier = String(value);
  return identifier.length > 18 ? `${identifier.slice(0, 8)}...${identifier.slice(-6)}` : identifier;
}

function getInitials(name) {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase();
}

function DetailRow({ icon: Icon, label, value, caption }) {
  return (
    <div className="profile-detail-row">
      <span className="profile-detail-row-icon">
        <Icon size={17} />
      </span>
      <div>
        <span className="profile-detail-row-label">{label}</span>
        <strong>{value}</strong>
        {caption && <small>{caption}</small>}
      </div>
    </div>
  );
}

export default function Profile() {
  const { currentUser } = useAuth();
  const displayName = currentUser?.name || "Meridian resident";
  const roleLabel = ROLE_LABELS[currentUser?.role] || "Resident";
  const isStaff = currentUser?.role === "staff" || currentUser?.role === "admin";

  return (
    <div className="lease-page">
      <section className="page-heading lease-heading">
        <div>
          <span className="section-kicker">ACCOUNT CENTER</span>
          <h1>Your profile</h1>
          <p>Keep your Meridian identity and residence access details close at hand.</p>
        </div>
      </section>

      <section className="content-card profile-hero">
        <div className="avatar profile-hero-avatar">{getInitials(displayName)}</div>
        <div className="profile-hero-identity">
          <span className="section-kicker">SIGNED IN ACCOUNT</span>
          <h2>{displayName}</h2>
          <p>{currentUser?.email || "Email unavailable"}</p>
        </div>
        <div className="profile-hero-badge">
          <BadgeCheck size={18} /> {roleLabel} access
        </div>
      </section>

      <div className="profile-layout">
        <section className="content-card profile-panel">
          <div className="card-heading">
            <div>
              <span className="section-kicker">IDENTITY</span>
              <h3>Identity details</h3>
            </div>
          </div>
          <div className="profile-detail-list">
            <DetailRow icon={Mail} label="Email address" value={currentUser?.email || "Not available"} />
            <DetailRow
              icon={ShieldCheck}
              label="Account role"
              value={roleLabel}
              caption={isStaff ? "Property operations access" : "Resident portal access"}
            />
            <DetailRow
              icon={Fingerprint}
              label="Guest ID"
              value={formatIdentifier(currentUser?.guest_id)}
              caption="Internal account identifier"
            />
          </div>
        </section>

        <section className="content-card profile-panel">
          <div className="card-heading">
            <div>
              <span className="section-kicker">RESIDENCE</span>
              <h3>Residence access</h3>
            </div>
          </div>
          <div className="profile-detail-list">
            <DetailRow
              icon={Building2}
              label="Unit ID"
              value={formatIdentifier(currentUser?.unit_id)}
              caption="Assigned residence unit"
            />
            <DetailRow
              icon={KeyRound}
              label="Portal permissions"
              value={isStaff ? "Staff operations" : "Resident services"}
              caption={isStaff ? "Manage property workflows" : "Manage your residence services"}
            />
            <DetailRow icon={CalendarDays} label="Account status" value="Active" caption="Access is available" />
          </div>
        </section>

        <section className="content-card profile-panel">
          <div className="card-heading">
            <div>
              <span className="section-kicker">SECURITY</span>
              <h3>Security &amp; privacy</h3>
            </div>
          </div>
          <div className="security-items">
            <div className="security-item">
              <span className="security-item-check">
                <Check size={15} />
              </span>
              <div>
                <strong>Authenticated session</strong>
                <span>Your access token is active for this visit.</span>
              </div>
            </div>
            <div className="security-item">
              <span className="security-item-check">
                <Check size={15} />
              </span>
              <div>
                <strong>Protected account</strong>
                <span>Credentials are handled securely by the portal.</span>
              </div>
            </div>
          </div>
          <p className="profile-security-note">
            To end this session on a shared device, use <strong>Sign out</strong> from the account menu.
          </p>
        </section>
      </div>
    </div>
  );
}
