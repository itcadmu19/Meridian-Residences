import React, { useEffect, useState } from "react";
import {
  CalendarDays,
  CreditCard,
  FileText,
  Home,
  Wrench,
  ArrowRight,
  Clock3,
} from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { getGuestLeases, getLeaseSummary } from "../services/leaseService";
import SummaryCard from "../components/SummaryCard";
import ActivityList from "../components/ActivityList";
import QuickActions from "../components/QuickActions";
import StatusBadge from "../components/StatusBadge";
import AiInsightsCard from "../components/AiInsightsCard";
import StaffDashboard from "./StaffDashboard";

// Hero slideshow - real photographs (not renders) of different buildings,
// cross-fading on a timer. See README.md for full source credits.
const BUILDING_IMAGES = [
  "https://images.unsplash.com/photo-1759073254456-06026e026c08?auto=format&fit=crop&fm=jpg&q=90&w=2400", // Montreux, Switzerland
  "https://images.unsplash.com/photo-1742296701061-5a4289495a6c?auto=format&fit=crop&fm=jpg&q=90&w=2400", // Verona, Italy
  "https://images.unsplash.com/photo-1781136194181-aea44724c905?auto=format&fit=crop&fm=jpg&q=90&w=2400", // palm-tree tower
  "https://images.unsplash.com/photo-1762028007806-751f2bef444a?auto=format&fit=crop&fm=jpg&q=90&w=2400", // Tehran, Iran
];

const BUILDING_SLIDE_INTERVAL_MS = 5000;

const INTERIOR_IMAGE =
  "https://images.pexels.com/photos/7214456/pexels-photo-7214456.jpeg?cs=srgb&fm=jpg&w=2400";

const DEMO_SUMMARY = {
  lease_id: "lease-demo-001",
  unit: {
    unit_number: "Apartment 101",
    unit_type: "2 BHK",
  },
  next_payment: {
    amount: 45000,
    due_date: "2026-09-10",
  },
  open_requests: 2,
  open_request_status: "1 in progress",
  lease_status: "active",
  lease_end_date: "2026-12-31",
  activities: [
    {
      id: 1,
      type: "invoice",
      title: "September invoice generated",
      description: "Monthly rent invoice is ready to view.",
      date: "Today",
    },
    {
      id: 2,
      type: "maintenance",
      title: "Maintenance request updated",
      description: "Your service request is in progress.",
      date: "Yesterday",
    },
    {
      id: 3,
      type: "payment",
      title: "Payment received",
      description: "Your August rent payment was recorded.",
      date: "28 Aug",
    },
    {
      id: 4,
      type: "lease",
      title: "Lease agreement available",
      description: "Your current lease is available to view.",
      date: "24 Aug",
    },
  ],
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

function DashboardSkeleton() {
  return (
    <div className="dashboard-skeleton">
      <div className="skeleton hero-skeleton" />
      <div className="skeleton-card-grid">
        <div className="skeleton" />
        <div className="skeleton" />
        <div className="skeleton" />
        <div className="skeleton" />
      </div>
    </div>
  );
}

const ACTIVITY_PREVIEW_COUNT = 3;

export default function Dashboard() {
  const { currentUser, isBootstrapping } = useAuth();
  const isStaff = currentUser?.role === "staff" || currentUser?.role === "admin";
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [usingDemoData, setUsingDemoData] = useState(false);
  const [noLeaseAssigned, setNoLeaseAssigned] = useState(false);
  const [showAllActivity, setShowAllActivity] = useState(false);
  const [activeSlide, setActiveSlide] = useState(0);

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveSlide((prev) => (prev + 1) % BUILDING_IMAGES.length);
    }, BUILDING_SLIDE_INTERVAL_MS);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    if (isBootstrapping || isStaff) return undefined;

    let mounted = true;

    // A brand-new self-registered account (or a session restored from
    // localStorage that never ran login()'s "pick the active lease"
    // bootstrap) may genuinely have zero leases - there is no "create a
    // lease" flow, leases are assigned by staff/seed data. That's a real,
    // valid state, not a backend outage, so it gets `noLeaseAssigned`
    // instead of silently falling through to demo data.
    async function resolveLeaseId() {
      const stored = localStorage.getItem("selected_lease_id");
      if (stored) return { leaseId: stored };

      if (currentUser?.role !== "resident" || !currentUser?.guest_id) return { leaseId: null };

      const leases = await getGuestLeases(currentUser.guest_id);
      const safeLeases = Array.isArray(leases) ? leases : [];
      if (safeLeases.length === 0) return { leaseId: null, noLeases: true };

      const active = safeLeases.find((lease) => lease.status === "active") || safeLeases[0];
      localStorage.setItem("selected_lease_id", active.id);
      return { leaseId: active.id };
    }

    async function loadSummary() {
      try {
        const { leaseId, noLeases } = await resolveLeaseId();

        if (noLeases) {
          if (mounted) {
            setNoLeaseAssigned(true);
            setUsingDemoData(false);
          }
          return;
        }

        if (!leaseId) throw new Error("No lease available for this account.");

        const data = await getLeaseSummary(leaseId);

        if (mounted) {
          setSummary(data);
          setUsingDemoData(false);
          setNoLeaseAssigned(false);
        }
      } catch {
        if (mounted) {
          setSummary(DEMO_SUMMARY);
          setUsingDemoData(true);
        }
      } finally {
        if (mounted) setLoading(false);
      }
    }

    loadSummary();

    return () => {
      mounted = false;
    };
  }, [isBootstrapping, isStaff]);

  // Which view a signed-in user gets is decided by their role, not a manual
  // toggle - staff/admin get the cross-property portfolio view (see
  // StaffDashboard.jsx), everyone else gets the resident view below. This
  // must come before the loading check: staff's effect above exits without
  // ever calling setLoading(false), so falling through to the skeleton
  // first would leave them stuck on it forever.
  if (isStaff) {
    return <StaffDashboard />;
  }

  if (loading) {
    return <DashboardSkeleton />;
  }

  if (noLeaseAssigned) {
    return (
      <div className="dashboard-page">
        <section className="dashboard-intro">
          <div>
            <span className="section-kicker">RESIDENT OVERVIEW</span>
            <h2>Welcome to Meridian Residences</h2>
          </div>
          <p>Stay up to date with your lease, payments and service requests.</p>
        </section>

        <section className="content-card lease-help-card">
          <div className="help-icon">
            <FileText size={20} />
          </div>
          <h3>No lease is assigned to your account yet</h3>
          <p>
            Your property manager hasn't linked a lease to this account yet. Once they do, your
            dashboard will populate automatically - please contact them if you believe this is a
            mistake.
          </p>
        </section>
      </div>
    );
  }

  const data = summary || DEMO_SUMMARY;
  const allActivities = data.activities || DEMO_SUMMARY.activities;
  const visibleActivities = showAllActivity
    ? allActivities
    : allActivities.slice(0, ACTIVITY_PREVIEW_COUNT);
  const hasMoreActivity = allActivities.length > ACTIVITY_PREVIEW_COUNT;

  return (
    <div className="dashboard-page">
      {usingDemoData && (
        <div className="demo-notice">
          <Clock3 size={16} />
          <span>
            Backend is not connected, so demo resident data is being shown.
          </span>
        </div>
      )}

      <section className="dashboard-hero">
        <div className="hero-copy">
          <span className="eyebrow">MERIDIAN RESIDENCES</span>
          <h1>Welcome to Meridian Residences</h1>
          <p>
            Everything you need for your residence, all in one place.
          </p>
          <div className="hero-line" />
          <span className="hero-tagline">Your home. Our priority.</span>
        </div>

        <div
          className="hero-building-image"
          role="img"
          aria-label="Modern Meridian-style apartment building"
        >
          {BUILDING_IMAGES.map((src, index) => (
            <div
              key={src}
              className={`hero-building-slide${index === activeSlide ? " active" : ""}`}
              style={{ backgroundImage: `url(${src})` }}
            />
          ))}
        </div>
      </section>

      <section className="dashboard-intro">
        <div>
          <span className="section-kicker">RESIDENT OVERVIEW</span>
          <h2>Your residence at a glance</h2>
        </div>
        <p>
          Stay up to date with your lease, payments and service requests.
        </p>
      </section>

      <section className="summary-grid">
        <SummaryCard
          icon={<Home size={21} />}
          label="Current Unit"
          value={data.unit?.unit_number || "Apartment 101"}
          detail={data.unit?.unit_type || "2 BHK"}
          accent="green"
        />

        <SummaryCard
          icon={<CreditCard size={21} />}
          label="Next Payment"
          value={formatCurrency(data.next_payment?.amount || 45000)}
          detail={`Due ${formatDate(data.next_payment?.due_date)}`}
          accent="gold"
        />

        <SummaryCard
          icon={<Wrench size={21} />}
          label="Open Requests"
          value={data.open_requests ?? 0}
          detail={data.open_request_status || "No open requests"}
          accent="olive"
        />

        <SummaryCard
          icon={<CalendarDays size={21} />}
          label="Lease Status"
          value={
            <StatusBadge status={data.lease_status || "active"} />
          }
          detail={`Ends ${formatDate(data.lease_end_date)}`}
          accent="cream"
        />
      </section>

      <section className="dashboard-content-grid">
        <div className="content-card activity-card">
          <div className="card-heading">
            <div>
              <span className="section-kicker">RECENT ACTIVITY</span>
              <h3>Recent activity</h3>
            </div>
            {hasMoreActivity && (
              <button
                className="text-button"
                onClick={() => setShowAllActivity((prev) => !prev)}
              >
                {showAllActivity ? "Show less" : "View all"} <ArrowRight size={15} />
              </button>
            )}
          </div>

          <ActivityList activities={visibleActivities} />
        </div>

        <div className="content-card welcome-card">
          <div
            className="welcome-image"
            style={{ backgroundImage: `url(${INTERIOR_IMAGE})` }}
            role="img"
            aria-label="Modern luxury apartment interior"
          />
          <div className="welcome-copy">
            <span className="section-kicker">MERIDIAN LIVING</span>
            <h3>Welcome to a smarter living experience.</h3>
            <p>
              Manage your residence, payments, lease and service requests from
              one simple place.
            </p>
            <Link to="/lease" className="outline-button">
              View my lease <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </section>

      <section className="ai-insights-section">
        <AiInsightsCard summary={data} />
      </section>

      <section className="quick-section">
        <div className="card-heading">
          <div>
            <span className="section-kicker">SHORTCUTS</span>
            <h3>Quick actions</h3>
          </div>
        </div>
        <QuickActions />
      </section>

      <section className="dashboard-footer-banner">
        <div>
          <span className="section-kicker">RESIDENT SUPPORT</span>
          <h3>Need something? We're here to help.</h3>
          <p>
            Use Maintenance for service requests or AI Assistant for quick
            answers about your residence.
          </p>
        </div>
        <Link to="/maintenance" className="primary-button">
          Get support <ArrowRight size={16} />
        </Link>
      </section>
    </div>
  );
}