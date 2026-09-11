import React, { useEffect, useState } from "react";
import PageHeader from "../components/PageHeader.jsx";
import Loading from "../components/Loading.jsx";
import ErrorMessage from "../components/ErrorMessage.jsx";
import EmptyState from "../components/EmptyState.jsx";
import LeaseCard from "../components/LeaseCard.jsx";
import leaseService from "../services/leaseService.js";
import { useAuth } from "../context/AuthContext.jsx";

export default function Lease() {
  const { currentUser } = useAuth();
  const [selectedLease, setSelectedLease] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);

  async function loadLease() {
    setIsLoading(true);
    setError(null);
    try {
      const response = await leaseService.getGuestLeases(currentUser.guest_id);
      const leases = response.data || [];
      setSelectedLease(leases.find((lease) => lease.status === "active") || leases[0] || null);
    } catch (err) {
      setError(err.message || "Unable to load your lease.");
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    loadLease();
  }, [currentUser.guest_id]);

  return (
    <div className="page">
      <PageHeader
        title="My Lease"
        description="View your current residence agreement and important lease dates."
      />

      {isLoading && <Loading label="Loading lease details..." />}
      {!isLoading && error && <ErrorMessage message={error} onRetry={loadLease} />}
      {!isLoading && !error && !selectedLease && (
        <EmptyState message="No lease agreement is available for your account." />
      )}
      {!isLoading && !error && selectedLease && <LeaseCard lease={selectedLease} />}
    </div>
  );
}
