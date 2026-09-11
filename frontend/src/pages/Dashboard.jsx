import React from "react";
import { Home, CreditCard, Wrench } from "lucide-react";
import { Link } from "react-router-dom";
import PageHeader from "../components/PageHeader.jsx";
import StatCard from "../components/StatCard.jsx";
import { useAuth } from "../context/AuthContext.jsx";

export default function Dashboard() {
  const { currentUser } = useAuth();

  return (
    <div className="page">
      <PageHeader title="Good morning" description="Welcome back to Meridian Residences" />

      <div className="card-grid">
        <StatCard icon={Home} label="Signed in as" value={currentUser?.email} />
        <StatCard icon={CreditCard} label="Next Payment" value="Owned by Member 2" />
        <StatCard icon={Wrench} label="Open Requests" value="See Maintenance" />
      </div>

      <p className="page-header__description">
        This build focuses on Story 3 — Maintenance. Visit{" "}
        <Link to="/maintenance">Maintenance</Link> to submit and track requests.
      </p>
    </div>
  );
}
