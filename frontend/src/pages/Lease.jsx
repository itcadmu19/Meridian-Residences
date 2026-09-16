import React, { useEffect, useRef, useState } from "react";
import {
  ArrowRight,
  CalendarDays,
  Download,
  FileText,
  Home,
  IndianRupee,
  RefreshCw,
} from "lucide-react";
import {
  downloadLeaseAgreement,
  getGuestLeases,
  getLease,
  requestLeaseRenewal,
} from "../services/leaseService";
import StatusBadge from "../components/StatusBadge";
import Toast from "../components/Toast";
import LeaseAgreementPanel from "../components/LeaseAgreementPanel";
import { useAuth } from "../context/AuthContext";
import StaffLeaseManagement from "./StaffLeaseManagement";

const RENEWAL_COOLDOWN_MS = 10000;

const BUILDING_IMAGE =
  "https://images.unsplash.com/photo-1742296701061-5a4289495a6c?auto=format&fit=crop&fm=jpg&q=90&w=1800";

const DEMO_LEASE = {
  id: "lease-demo-001",
  unit_id: "unit-101",
  guest_id: "guest-001",
  unit: {
    unit_number: "Apartment 101",
    unit_type: "2 BHK",
  },
  property: {
    name: "Meridian Residences",
    address: "Premium Residential Community",
  },
  start_date: "2026-01-01",
  end_date: "2026-12-31",
  monthly_rate: 45000,
  renewal_date: "2026-12-01",
  status: "active",
  agreement_file_url: null,
  renewal_requested_at: null,
};

function formatCurrency(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

function formatDate(value) {
  if (!value) return "—";

  return new Date(`${value}T00:00:00`).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function formatLongDate(value) {
  if (!value) return "—";

  return new Date(`${value}T00:00:00`).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
}

function formatLeaseOptionLabel(item) {
  const unitLabel = item.unit?.unit_number
    ? `Apartment ${item.unit.unit_number}`
    : "Apartment";
  const statusLabel = item.status
    ? item.status.charAt(0).toUpperCase() + item.status.slice(1)
    : "";
  return `${unitLabel} — ${statusLabel} (${formatDate(item.start_date)} – ${formatDate(
    item.end_date
  )})`;
}

export default function Lease() {
  const { currentUser, isBootstrapping } = useAuth();
  const isStaff = currentUser?.role === "staff" || currentUser?.role === "admin";
  const [lease, setLease] = useState(null);
  const [loading, setLoading] = useState(true);
  const [usingDemoData, setUsingDemoData] = useState(false);
  const [noLeaseAssigned, setNoLeaseAssigned] = useState(false);

  const [leases, setLeases] = useState([]);
  const [selectedLeaseId, setSelectedLeaseId] = useState(
    () => localStorage.getItem("selected_lease_id") || null
  );

  const [downloading, setDownloading] = useState(false);
  const [renewing, setRenewing] = useState(false);
  const [renewalCoolingDown, setRenewalCoolingDown] = useState(false);
  const [renewalToast, setRenewalToast] = useState(null);
  const [actionNotice, setActionNotice] = useState(null);
  const cooldownTimerRef = useRef(null);

  useEffect(() => {
    return () => clearTimeout(cooldownTimerRef.current);
  }, []);

  // Resolve which lease (if any) this resident should see. A brand-new
  // self-registered account has a login but no lease yet (there is no
  // "create a lease" flow - leases are assigned by staff/seed data), which
  // is a real, valid state - not a backend outage - so it gets its own
  // `noLeaseAssigned` flag instead of falling through to the demo-data path.
  useEffect(() => {
    if (isBootstrapping || isStaff) return undefined;

    let mounted = true;

    async function resolveLease() {
      try {
        const list = await getGuestLeases(currentUser.guest_id);
        const safeList = Array.isArray(list) ? list : [];
        if (!mounted) return;

        setLeases(safeList);

        if (safeList.length === 0) {
          setNoLeaseAssigned(true);
          setLease(null);
          setUsingDemoData(false);
          setLoading(false);
          return;
        }

        // Prefer whatever was previously selected, but only if it's still
        // one of this resident's own leases (stale/foreign ids are ignored
        // rather than sent to the detail endpoint as-is).
        const stored = localStorage.getItem("selected_lease_id");
        const storedMatch = stored && safeList.find((item) => item.id === stored);
        const target = storedMatch || safeList.find((item) => item.status === "active") || safeList[0];

        setNoLeaseAssigned(false);
        localStorage.setItem("selected_lease_id", target.id);
        setSelectedLeaseId(target.id);
      } catch {
        // Couldn't even reach the leases list endpoint - that's a genuine
        // backend/connectivity problem, so fall back to demo data as before.
        if (mounted) {
          setLease(DEMO_LEASE);
          setUsingDemoData(true);
          setLoading(false);
        }
      }
    }

    resolveLease();

    return () => {
      mounted = false;
    };
  }, [isBootstrapping, currentUser.guest_id, isStaff]);

  // Load the full detail for whichever lease id is currently selected
  // (initial resolution above, or a manual switch via the dropdown).
  useEffect(() => {
    if (isBootstrapping || isStaff || noLeaseAssigned || !selectedLeaseId) return undefined;

    let mounted = true;

    async function loadLease() {
      try {
        const data = await getLease(selectedLeaseId);

        if (mounted) {
          setLease(data);
          setUsingDemoData(false);
        }
      } catch {
        if (mounted) {
          setLease(DEMO_LEASE);
          setUsingDemoData(true);
        }
      } finally {
        if (mounted) setLoading(false);
      }
    }

    setLoading(true);
    setActionNotice(null);
    loadLease();

    return () => {
      mounted = false;
    };
  }, [isBootstrapping, selectedLeaseId, isStaff, noLeaseAssigned]);

  function handleSwitchLease(event) {
    const nextId = event.target.value;
    setSelectedLeaseId(nextId);
    localStorage.setItem("selected_lease_id", nextId);
  }

  // Which view a signed-in user gets is decided by their role, not a manual
  // toggle - staff/admin get the cross-property management view, everyone
  // else gets the classic single-lease resident view below.
  if (isStaff) {
    return <StaffLeaseManagement />;
  }

  if (loading) {
    return (
      <div className="lease-page">
        <div className="skeleton lease-header-skeleton" />
        <div className="skeleton lease-main-skeleton" />
      </div>
    );
  }

  if (noLeaseAssigned) {
    return (
      <div className="lease-page">
        <section className="page-heading lease-heading">
          <div>
            <span className="section-kicker">RESIDENT SERVICES</span>
            <h1>My Lease</h1>
            <p>View and manage your current residential lease agreement.</p>
          </div>
        </section>

        <section className="content-card lease-help-card">
          <div className="help-icon">
            <FileText size={20} />
          </div>
          <h3>No lease is assigned to your account yet</h3>
          <p>
            Your property manager hasn't linked a lease to this account yet. Once they do, it will
            appear here automatically - please contact them if you believe this is a mistake.
          </p>
        </section>
      </div>
    );
  }

  const data = lease || DEMO_LEASE;
  const canDownload = !usingDemoData && Boolean(data.agreement_file_url) && !downloading;
  const canRequestRenewal =
    !usingDemoData && !renewalCoolingDown && data.status === "active" && !renewing;

  async function handleDownload() {
    if (!canDownload) return;
    setDownloading(true);
    setActionNotice(null);
    try {
      const blob = await downloadLeaseAgreement(data.id);
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `lease_agreement_${data.id}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    } catch {
      setActionNotice({
        type: "error",
        text: "Could not download the agreement. Please try again.",
      });
    } finally {
      setDownloading(false);
    }
  }

  async function handleViewDocuments() {
    if (!canDownload) return;
    setDownloading(true);
    setActionNotice(null);
    try {
      const blob = await downloadLeaseAgreement(data.id);
      const url = URL.createObjectURL(blob);
      window.open(url, "_blank", "noopener,noreferrer");
      // Revoke after giving the new tab time to load the blob URL.
      setTimeout(() => URL.revokeObjectURL(url), 10000);
    } catch {
      setActionNotice({
        type: "error",
        text: "Could not open the agreement. Please try again.",
      });
    } finally {
      setDownloading(false);
    }
  }

  async function handleRequestRenewal() {
    if (!canRequestRenewal) return;
    setRenewing(true);
    setActionNotice(null);
    try {
      const result = await requestLeaseRenewal(data.id);
      setRenewalToast({
        title: result.already_requested ? "Renewal already requested" : "Renewal requested",
        message: result.already_requested
          ? `You already requested a renewal for this lease on ${formatDate(result.renewal_requested_at)}.`
          : `Your renewal request was submitted on ${formatDate(result.renewal_requested_at)}.`,
      });
      setRenewalCoolingDown(true);
      clearTimeout(cooldownTimerRef.current);
      cooldownTimerRef.current = setTimeout(() => {
        setRenewalCoolingDown(false);
      }, RENEWAL_COOLDOWN_MS);
    } catch {
      setActionNotice({
        type: "error",
        text: "Could not submit the renewal request. Please try again.",
      });
    } finally {
      setRenewing(false);
    }
  }

  return (
    <div className="lease-page">
      {usingDemoData && (
        <div className="demo-notice">
          <FileText size={16} />
          <span>
            Backend is not connected, so demo lease information is being shown.
          </span>
        </div>
      )}

      <section className="page-heading lease-heading">
        <div>
          <span className="section-kicker">RESIDENT SERVICES</span>
          <h1>My Lease</h1>
          <p>View and manage your current residential lease agreement.</p>
        </div>
        <StatusBadge status={data.status || "active"} />
      </section>

      {!usingDemoData && leases.length > 1 && (
        <section className="lease-switcher">
          <label htmlFor="lease-switcher-select">Viewing lease:</label>
          <select
            id="lease-switcher-select"
            value={selectedLeaseId}
            onChange={handleSwitchLease}
          >
            {leases.map((item) => (
              <option key={item.id} value={item.id}>
                {formatLeaseOptionLabel(item)}
              </option>
            ))}
          </select>
        </section>
      )}

      {actionNotice && (
        <div className={`demo-notice demo-notice--${actionNotice.type}`}>
          <FileText size={16} />
          <span>{actionNotice.text}</span>
        </div>
      )}

      <section className="lease-layout">
        <article className="lease-main-card">
          <div
            className="lease-property-image"
            style={{ backgroundImage: `url(${BUILDING_IMAGE})` }}
            role="img"
            aria-label="Modern apartment building"
          >
            <div className="property-image-overlay">
              <span>ACTIVE RESIDENCE</span>
            </div>
          </div>

          <div className="lease-main-content">
            <div className="lease-property-title">
              <div>
                <span className="section-kicker">CURRENT RESIDENCE</span>
                <h2>{data.unit?.unit_number || "Apartment 101"}</h2>
                <p>{data.property?.name || "Meridian Residences"}</p>
              </div>
              <div className="unit-icon">
                <Home size={25} />
              </div>
            </div>

            <div className="lease-detail-grid">
              <div className="lease-detail">
                <span>
                  <CalendarDays size={16} /> Lease period
                </span>
                <strong>
                  {formatLongDate(data.start_date)} —{" "}
                  {formatLongDate(data.end_date)}
                </strong>
              </div>

              <div className="lease-detail">
                <span>
                  <IndianRupee size={16} /> Monthly rent
                </span>
                <strong>{formatCurrency(data.monthly_rate)}</strong>
              </div>

              <div className="lease-detail">
                <span>
                  <RefreshCw size={16} /> Renewal date
                </span>
                <strong>{formatLongDate(data.renewal_date)}</strong>
              </div>

              <div className="lease-detail">
                <span>
                  <Home size={16} /> Apartment type
                </span>
                <strong>{data.unit?.unit_type || "2 BHK"}</strong>
              </div>
            </div>

            <div className="lease-actions">
              <button
                className="primary-button"
                onClick={handleDownload}
                disabled={!canDownload}
                title={
                  !usingDemoData && !data.agreement_file_url
                    ? "No agreement on file yet"
                    : undefined
                }
              >
                <Download size={17} />
                {downloading ? "Downloading…" : "Download agreement"}
              </button>
              <button
                className="secondary-button"
                onClick={handleRequestRenewal}
                disabled={!canRequestRenewal}
              >
                <RefreshCw size={17} />
                {renewing
                  ? "Requesting…"
                  : renewalCoolingDown
                  ? "Renewal requested"
                  : "Request renewal"}
              </button>
            </div>
          </div>
        </article>

        <aside className="lease-side-column">
          <div className="content-card lease-summary-card">
            <span className="section-kicker">LEASE SUMMARY</span>
            <h3>Agreement overview</h3>

            <div className="summary-list">
              <div>
                <span>Lease ID</span>
                <strong>{data.id || "lease-demo-001"}</strong>
              </div>
              <div>
                <span>Status</span>
                <StatusBadge status={data.status || "active"} />
              </div>
              <div>
                <span>Start date</span>
                <strong>{formatDate(data.start_date)}</strong>
              </div>
              <div>
                <span>End date</span>
                <strong>{formatDate(data.end_date)}</strong>
              </div>
              <div>
                <span>Monthly rent</span>
                <strong>{formatCurrency(data.monthly_rate)}</strong>
              </div>
              <div>
                <span>Renewal date</span>
                <strong>{formatDate(data.renewal_date)}</strong>
              </div>
            </div>
          </div>

          <div className="content-card lease-help-card">
            <div className="help-icon">
              <FileText size={20} />
            </div>
            <span className="section-kicker">DOCUMENTS</span>
            <h3>Your agreement is always available.</h3>
            <p>
              Download a copy of your lease agreement whenever you need it.
            </p>
            <button
              className="text-button"
              onClick={handleViewDocuments}
              disabled={!canDownload}
            >
              View documents <ArrowRight size={15} />
            </button>
          </div>
        </aside>
      </section>

      <LeaseAgreementPanel lease={data} disabled={usingDemoData} />

      <Toast
        open={Boolean(renewalToast)}
        onClose={() => setRenewalToast(null)}
        title={renewalToast?.title}
        message={renewalToast?.message}
      />
    </div>
  );
}
