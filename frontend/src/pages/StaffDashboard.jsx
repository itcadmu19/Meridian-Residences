import React, { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  ArrowRight,
  CalendarClock,
  CheckCircle2,
  Clock3,
  FileText,
  Receipt,
  Sparkles,
  Wrench,
} from "lucide-react";
import { Link } from "react-router-dom";
import { getStaffLeases } from "../services/staffLeaseService";
import { getTickets } from "../services/maintenanceService";
import { getInsights } from "../services/invoiceService";
import SummaryCard from "../components/SummaryCard";
import ActivityList from "../components/ActivityList";
import StatusBadge from "../components/StatusBadge";

// Same rotating-image hero scaffold as the resident Dashboard - kept as its
// own copy here (rather than imported) since it's a small, page-local
// visual detail, not shared logic.
const BUILDING_IMAGES = [
  "https://images.unsplash.com/photo-1759073254456-06026e026c08?auto=format&fit=crop&fm=jpg&q=90&w=2400", // Montreux, Switzerland
  "https://images.unsplash.com/photo-1742296701061-5a4289495a6c?auto=format&fit=crop&fm=jpg&q=90&w=2400", // Verona, Italy
  "https://images.unsplash.com/photo-1781136194181-aea44724c905?auto=format&fit=crop&fm=jpg&q=90&w=2400", // palm-tree tower
  "https://images.unsplash.com/photo-1762028007806-751f2bef444a?auto=format&fit=crop&fm=jpg&q=90&w=2400", // Tehran, Iran
];

const BUILDING_SLIDE_INTERVAL_MS = 5000;

const INTERIOR_IMAGE =
  "https://images.pexels.com/photos/7214456/pexels-photo-7214456.jpeg?cs=srgb&fm=jpg&w=2400";

const EXPIRING_SOON_DAYS = 30;
const ACTIVITY_PREVIEW_COUNT = 3;
const OPEN_TICKET_STATUSES = ["open", "assigned", "in_progress"];
const URGENT_PRIORITIES = ["high", "urgent"];

const DEMO_LEASES = [
  {
    id: "lease-demo-001",
    guest: { name: "Demo Resident" },
    unit: { unit_number: "101", unit_type: "2BHK" },
    start_date: "2026-01-01",
    end_date: "2026-12-31",
    status: "active",
  },
  {
    id: "lease-demo-002",
    guest: { name: "Other Resident" },
    unit: { unit_number: "204", unit_type: "1BHK" },
    start_date: "2026-06-01",
    end_date: "2026-09-25",
    status: "active",
  },
  {
    id: "lease-demo-003",
    guest: { name: "Third Resident" },
    unit: { unit_number: "310", unit_type: "3BHK" },
    start_date: "2027-01-01",
    end_date: "2027-12-31",
    status: "pending",
  },
];

const DEMO_TICKETS = [
  { id: "ticket-demo-001", issue_type: "plumbing", status: "open", priority: "high", updated_at: "2026-09-14T10:00:00Z" },
  { id: "ticket-demo-002", issue_type: "electrical", status: "assigned", priority: "medium", updated_at: "2026-09-13T10:00:00Z" },
];

function formatCurrency(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value || 0);
}

function formatDate(value) {
  if (!value) return "—";
  return new Date(value).toLocaleDateString("en-IN", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function isExpiringSoon(lease) {
  if (lease.status !== "active") return false;
  const end = new Date(`${lease.end_date}T00:00:00`);
  const days = (end - new Date()) / (1000 * 60 * 60 * 24);
  return days >= 0 && days <= EXPIRING_SOON_DAYS;
}

function buildStaffInsights(leaseCounts, ticketCounts) {
  const insights = [];

  if (leaseCounts.expiring > 0) {
    insights.push(
      `${leaseCounts.expiring} lease${leaseCounts.expiring === 1 ? "" : "s"} expiring within ${EXPIRING_SOON_DAYS} days - review renewals soon.`
    );
  } else {
    insights.push(`No leases expiring in the next ${EXPIRING_SOON_DAYS} days.`);
  }

  if (leaseCounts.pending > 0) {
    insights.push(`${leaseCounts.pending} pending lease${leaseCounts.pending === 1 ? "" : "s"} awaiting activation.`);
  }

  if (ticketCounts.urgent > 0) {
    insights.push(`${ticketCounts.urgent} urgent maintenance request${ticketCounts.urgent === 1 ? "" : "s"} need attention.`);
  } else if (ticketCounts.open > 0) {
    insights.push(`${ticketCounts.open} open maintenance request${ticketCounts.open === 1 ? "" : "s"} in the queue.`);
  } else {
    insights.push("No open maintenance requests - the queue is clear.");
  }

  return insights.slice(0, 4);
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

export default function StaffDashboard() {
  const [leases, setLeases] = useState([]);
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [usingDemoData, setUsingDemoData] = useState(false);
  const [showAllActivity, setShowAllActivity] = useState(false);
  const [activeSlide, setActiveSlide] = useState(0);
  const [billingSnapshot, setBillingSnapshot] = useState(null);
  const [billingUnavailable, setBillingUnavailable] = useState(false);

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveSlide((prev) => (prev + 1) % BUILDING_IMAGES.length);
    }, BUILDING_SLIDE_INTERVAL_MS);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    let mounted = true;

    async function loadPortfolio() {
      try {
        const [leaseData, ticketData] = await Promise.all([
          getStaffLeases(),
          getTickets({ page_size: 100 }),
        ]);
        if (mounted) {
          setLeases(Array.isArray(leaseData) ? leaseData : []);
          setTickets(Array.isArray(ticketData) ? ticketData : []);
          setUsingDemoData(false);
        }
      } catch {
        if (mounted) {
          setLeases(DEMO_LEASES);
          setTickets(DEMO_TICKETS);
          setUsingDemoData(true);
        }
      } finally {
        if (mounted) setLoading(false);
      }
    }

    loadPortfolio();

    return () => {
      mounted = false;
    };
  }, []);

  // Separate, independent fetch - a slow or failing AI insight shouldn't
  // block the rest of the dashboard or force it into demo mode, it should
  // just leave this one card showing its own "unavailable" state.
  useEffect(() => {
    let mounted = true;

    getInsights({})
      .then((data) => {
        if (mounted) setBillingSnapshot(data);
      })
      .catch(() => {
        if (mounted) setBillingUnavailable(true);
      });

    return () => {
      mounted = false;
    };
  }, []);

  const leaseCounts = useMemo(
    () => ({
      active: leases.filter((lease) => lease.status === "active").length,
      pending: leases.filter((lease) => lease.status === "pending").length,
      expiring: leases.filter(isExpiringSoon).length,
      expired: leases.filter((lease) => lease.status === "expired").length,
    }),
    [leases]
  );

  const ticketCounts = useMemo(() => {
    const open = tickets.filter((ticket) => OPEN_TICKET_STATUSES.includes(ticket.status));
    return {
      open: open.length,
      urgent: open.filter((ticket) => URGENT_PRIORITIES.includes(ticket.priority)).length,
    };
  }, [tickets]);

  const staffInsights = useMemo(() => buildStaffInsights(leaseCounts, ticketCounts), [leaseCounts, ticketCounts]);

  const urgentTickets = useMemo(
    () =>
      tickets
        .filter((ticket) => OPEN_TICKET_STATUSES.includes(ticket.status) && URGENT_PRIORITIES.includes(ticket.priority))
        .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
        .slice(0, 4),
    [tickets]
  );

  const recentActivity = useMemo(() => {
    const ticketActivities = [...tickets]
      .sort((a, b) => new Date(b.updated_at) - new Date(a.updated_at))
      .slice(0, 3)
      .map((ticket) => ({
        id: `ticket-${ticket.id}`,
        type: "maintenance",
        title: "Maintenance request updated",
        description: `A ${ticket.issue_type} request is ${ticket.status.replace("_", " ")}.`,
        sortValue: new Date(ticket.updated_at).getTime(),
        date: formatDate(ticket.updated_at),
      }));

    const leaseActivities = [...leases]
      .sort((a, b) => new Date(b.start_date) - new Date(a.start_date))
      .slice(0, 2)
      .map((lease) => ({
        id: `lease-${lease.id}`,
        type: "lease",
        title: "Lease on record",
        description: `${lease.guest?.name || "A resident"}'s lease for Unit ${lease.unit?.unit_number || "—"} is ${lease.status}.`,
        sortValue: new Date(`${lease.start_date}T00:00:00`).getTime(),
        date: formatDate(lease.start_date),
      }));

    return [...ticketActivities, ...leaseActivities].sort((a, b) => b.sortValue - a.sortValue);
  }, [tickets, leases]);

  const visibleActivities = showAllActivity ? recentActivity : recentActivity.slice(0, ACTIVITY_PREVIEW_COUNT);
  const hasMoreActivity = recentActivity.length > ACTIVITY_PREVIEW_COUNT;

  if (loading) {
    return <DashboardSkeleton />;
  }

  return (
    <div className="dashboard-page">
      {usingDemoData && (
        <div className="demo-notice">
          <Clock3 size={16} />
          <span>Backend is not connected, so demo portfolio data is being shown.</span>
        </div>
      )}

      <section className="dashboard-hero">
        <div className="hero-copy">
          <span className="eyebrow">MERIDIAN RESIDENCES</span>
          <h1>Portfolio Overview</h1>
          <p>Everything staff need to manage leases, requests and billing, all in one place.</p>
          <div className="hero-line" />
          <span className="hero-tagline">Your properties. Well managed.</span>
        </div>

        <div className="hero-building-image" role="img" aria-label="Modern Meridian-style apartment building">
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
          <span className="section-kicker">STAFF OVERVIEW</span>
          <h2>Your portfolio at a glance</h2>
        </div>
        <p>Track leases, maintenance requests and billing across every property.</p>
      </section>

      <section className="summary-grid">
        <SummaryCard icon={<CheckCircle2 size={21} />} label="Active Leases" value={leaseCounts.active} accent="green" />
        <SummaryCard icon={<Clock3 size={21} />} label="Pending Leases" value={leaseCounts.pending} accent="gold" />
        <SummaryCard icon={<CalendarClock size={21} />} label="Expiring Soon" value={leaseCounts.expiring} accent="olive" />
        <SummaryCard
          icon={<Wrench size={21} />}
          label="Open Maintenance"
          value={ticketCounts.open}
          detail={ticketCounts.urgent > 0 ? `${ticketCounts.urgent} urgent` : "None urgent"}
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
              <button className="text-button" onClick={() => setShowAllActivity((prev) => !prev)}>
                {showAllActivity ? "Show less" : "View all"} <ArrowRight size={15} />
              </button>
            )}
          </div>

          {visibleActivities.length > 0 ? (
            <ActivityList activities={visibleActivities} />
          ) : (
            <p className="lease-table-empty">No recent activity yet.</p>
          )}
        </div>

        <div className="content-card welcome-card">
          <div
            className="welcome-image"
            style={{ backgroundImage: `url(${INTERIOR_IMAGE})` }}
            role="img"
            aria-label="Modern luxury apartment interior"
          />
          <div className="welcome-copy">
            <span className="section-kicker">MERIDIAN OPERATIONS</span>
            <h3>Keep every property running smoothly.</h3>
            <p>Review leases, respond to maintenance requests and manage billing from one dashboard.</p>
            <Link to="/lease" className="outline-button">
              Manage leases <ArrowRight size={16} />
            </Link>
          </div>
        </div>
      </section>

      <section className="dashboard-content-grid">
        <div className="content-card">
          <div className="card-heading">
            <div>
              <span className="section-kicker">BILLING</span>
              <h3>Billing snapshot</h3>
            </div>
          </div>

          {billingSnapshot ? (
            <>
              <div className="billing-snapshot-row">
                <StatusBadge status={billingSnapshot.risk_level} />
                <span>{billingSnapshot.overdue_count} overdue invoice{billingSnapshot.overdue_count === 1 ? "" : "s"}</span>
                <strong>{formatCurrency(billingSnapshot.overdue_amount)}</strong>
              </div>
              <p>{billingSnapshot.insight}</p>
            </>
          ) : billingUnavailable ? (
            <p className="lease-table-empty">Billing insight is unavailable right now.</p>
          ) : (
            <p className="lease-table-empty">Loading billing snapshot…</p>
          )}

          <Link to="/invoices" className="text-button">
            Go to billing &amp; invoices <ArrowRight size={15} />
          </Link>
        </div>

        <div className="content-card">
          <div className="card-heading">
            <div>
              <span className="section-kicker">NEEDS ATTENTION</span>
              <h3>Urgent maintenance requests</h3>
            </div>
          </div>

          {urgentTickets.length > 0 ? (
            <div className="activity-list">
              {urgentTickets.map((ticket) => (
                <div className="activity-row" key={ticket.id}>
                  <div className="activity-icon maintenance">
                    <AlertTriangle size={17} />
                  </div>
                  <div className="activity-content">
                    <strong>{ticket.issue_type} request</strong>
                    <span>Status: {ticket.status.replace("_", " ")}</span>
                  </div>
                  <StatusBadge status={ticket.priority} />
                </div>
              ))}
            </div>
          ) : (
            <p className="lease-table-empty">No urgent maintenance requests right now.</p>
          )}

          <Link to="/maintenance" className="text-button">
            Go to maintenance queue <ArrowRight size={15} />
          </Link>
        </div>
      </section>

      <section className="ai-insights-section">
        <div className="content-card ai-insights-card">
          <div className="card-heading">
            <div>
              <span className="section-kicker">AI INSIGHTS</span>
              <h3>Smart summary for your portfolio</h3>
            </div>
            <div className="ai-insights-icon">
              <Sparkles size={18} />
            </div>
          </div>

          <ul className="ai-insights-list">
            {staffInsights.map((text, index) => (
              <li key={index}>{text}</li>
            ))}
          </ul>
        </div>
      </section>

      <section className="quick-section">
        <div className="card-heading">
          <div>
            <span className="section-kicker">SHORTCUTS</span>
            <h3>Quick actions</h3>
          </div>
        </div>
        <div className="quick-actions">
          <Link to="/lease" className="quick-action">
            <span className="quick-action-icon">
              <FileText size={18} />
            </span>
            <span>
              <strong>Manage leases</strong>
              <small>Review and update leases</small>
            </span>
          </Link>
          <Link to="/maintenance" className="quick-action">
            <span className="quick-action-icon">
              <Wrench size={18} />
            </span>
            <span>
              <strong>Maintenance queue</strong>
              <small>Triage and resolve requests</small>
            </span>
          </Link>
          <Link to="/invoices" className="quick-action">
            <span className="quick-action-icon">
              <Receipt size={18} />
            </span>
            <span>
              <strong>Billing & invoices</strong>
              <small>Generate and review invoices</small>
            </span>
          </Link>
        </div>
      </section>

      <section className="dashboard-footer-banner">
        <div>
          <span className="section-kicker">MERIDIAN RESIDENCES</span>
          <h3>Consistent, well-managed living for every resident.</h3>
        </div>
        <Link to="/lease" className="primary-button">
          Go to lease management <ArrowRight size={16} />
        </Link>
      </section>
    </div>
  );
}
