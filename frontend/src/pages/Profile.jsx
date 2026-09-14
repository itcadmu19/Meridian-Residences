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
  UserRound,
} from "lucide-react";
import { useAuth } from "../context/AuthContext.jsx";

function formatRole(role) {
  if (!role) return "Resident";
  return role.charAt(0).toUpperCase() + role.slice(1).toLowerCase();
}

function formatIdentifier(value) {
  if (!value) return "Not assigned";
  const identifier = String(value);
  return identifier.length > 18
    ? `${identifier.slice(0, 8)}...${identifier.slice(-6)}`
    : identifier;
}

function getDisplayName(email) {
  const name = email?.split("@")[0]?.replace(/[._-]+/g, " ");
  return name ? name.replace(/\b\w/g, (letter) => letter.toUpperCase()) : "Meridian resident";
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
      <span className="profile-detail-row__icon"><Icon size={17} /></span>
      <div>
        <span className="profile-detail-row__label">{label}</span>
        <strong>{value}</strong>
        {caption && <small>{caption}</small>}
      </div>
    </div>
  );
}

export default function Profile() {
  const { currentUser } = useAuth();
  const displayName = getDisplayName(currentUser?.email);
  const role = formatRole(currentUser?.role);
  const isStaff = ["staff", "admin"].includes(currentUser?.role?.toLowerCase());

  return (
    <main className="page profile-page">
      <div className="page-header profile-page__header">
        <div>
          <span className="profile-page__eyebrow">Account center</span>
          <h1 className="page-header__title">Your profile</h1>
          <p className="page-header__description">
            Keep your Meridian identity and residence access details close at hand.
          </p>
        </div>
        <div className="profile-page__status"><Check size={15} /> Session active</div>
      </div>

      <section className="profile-hero" aria-labelledby="profile-name">
        <div className="profile-avatar">{getInitials(displayName)}</div>
        <div className="profile-hero__identity">
          <span className="profile-page__eyebrow">Signed in account</span>
          <h2 id="profile-name">{displayName}</h2>
          <p>{currentUser?.email || "Email unavailable"}</p>
        </div>
        <div className="profile-hero__badge"><BadgeCheck size={18} /> {role} access</div>
      </section>

      <div className="profile-layout">
        <section className="card profile-panel" aria-labelledby="identity-title">
          <div className="profile-panel__heading">
            <div className="profile-panel__title-icon"><UserRound size={18} /></div>
            <div>
              <h2 id="identity-title">Identity details</h2>
              <p>Information associated with your login.</p>
            </div>
          </div>
          <div className="profile-detail-list">
            <DetailRow icon={Mail} label="Email address" value={currentUser?.email || "Not available"} />
            <DetailRow icon={ShieldCheck} label="Account role" value={role} caption={isStaff ? "Property operations access" : "Resident portal access"} />
            <DetailRow icon={Fingerprint} label="Guest ID" value={formatIdentifier(currentUser?.guest_id)} caption="Internal account identifier" />
          </div>
        </section>

        <section className="card profile-panel" aria-labelledby="residence-title">
          <div className="profile-panel__heading">
            <div className="profile-panel__title-icon profile-panel__title-icon--gold"><Building2 size={18} /></div>
            <div>
              <h2 id="residence-title">Residence access</h2>
              <p>Your current Meridian association.</p>
            </div>
          </div>
          <div className="profile-detail-list">
            <DetailRow icon={Building2} label="Unit ID" value={formatIdentifier(currentUser?.unit_id)} caption="Assigned residence unit" />
            <DetailRow icon={KeyRound} label="Portal permissions" value={isStaff ? "Staff operations" : "Resident services"} caption={isStaff ? "Manage property workflows" : "Manage your residence services"} />
            <DetailRow icon={CalendarDays} label="Account status" value="Active" caption="Access is available" />
          </div>
        </section>

        <section className="card profile-security" aria-labelledby="security-title">
          <div className="profile-panel__heading">
            <div className="profile-panel__title-icon"><ShieldCheck size={18} /></div>
            <div>
              <h2 id="security-title">Security & privacy</h2>
              <p>Your account is protected by Meridian authentication.</p>
            </div>
          </div>
          <div className="security-items">
            <div className="security-item">
              <span className="security-item__check"><Check size={15} /></span>
              <div><strong>Authenticated session</strong><span>Your access token is active for this visit.</span></div>
            </div>
            <div className="security-item">
              <span className="security-item__check"><Check size={15} /></span>
              <div><strong>Protected account</strong><span>Credentials are handled securely by the portal.</span></div>
            </div>
          </div>
          <p className="profile-security__note">To end this session on a shared device, use <strong>Log Out</strong> in the sidebar.</p>
        </section>
      </div>
    </main>
  );
}