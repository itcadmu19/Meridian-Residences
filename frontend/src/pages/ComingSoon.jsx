import React from "react";
import PageHeader from "../components/PageHeader.jsx";
import EmptyState from "../components/EmptyState.jsx";

// Placeholder for other members' stories (Lease, Invoices, Assistant, Profile).
// Kept out of scope for Member 3 — Maintenance so this build does not touch their files.
export default function ComingSoon({ title }) {
  return (
    <div className="page">
      <PageHeader title={title} description="This story is owned by another team member." />
      <EmptyState message="Not part of the Member 3 (Maintenance) build." />
    </div>
  );
}
