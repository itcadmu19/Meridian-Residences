import React, { useMemo } from "react";
import { Sparkles } from "lucide-react";

function formatCurrency(value) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);
}

function daysUntil(dateStr) {
  if (!dateStr) return null;
  const target = new Date(`${dateStr}T00:00:00`);
  return Math.round((target - new Date()) / (1000 * 60 * 60 * 24));
}

/**
 * Turns the resident's already-fetched dashboard summary into a few short,
 * natural-language tips. Pure client-side logic (no external AI API/key) -
 * works identically for real or demo data.
 */
function buildInsights(summary) {
  const insights = [];

  const dueInDays = daysUntil(summary?.next_payment?.due_date);
  if (dueInDays !== null) {
    const amount = formatCurrency(summary.next_payment.amount);
    if (dueInDays < 0) {
      insights.push(`Your payment of ${amount} is overdue by ${Math.abs(dueInDays)} day${Math.abs(dueInDays) === 1 ? "" : "s"}.`);
    } else if (dueInDays === 0) {
      insights.push(`Your payment of ${amount} is due today.`);
    } else if (dueInDays <= 7) {
      insights.push(`Your payment of ${amount} is due in ${dueInDays} day${dueInDays === 1 ? "" : "s"} - plan ahead.`);
    } else {
      insights.push(`Your next payment of ${amount} is due on ${new Date(`${summary.next_payment.due_date}T00:00:00`).toLocaleDateString("en-IN", { day: "2-digit", month: "short" })}.`);
    }
  }

  const leaseEndDays = daysUntil(summary?.lease_end_date);
  if (leaseEndDays !== null && summary.lease_status === "active") {
    if (leaseEndDays <= 60 && leaseEndDays >= 0) {
      insights.push(`Your lease renews in ${leaseEndDays} day${leaseEndDays === 1 ? "" : "s"} - consider requesting a renewal soon.`);
    } else if (leaseEndDays > 60) {
      insights.push(`Your lease is active with ${Math.round(leaseEndDays / 30)} month${Math.round(leaseEndDays / 30) === 1 ? "" : "s"} remaining.`);
    }
  }

  if ((summary?.open_requests ?? 0) > 0) {
    insights.push(
      `You have ${summary.open_requests} open maintenance request${summary.open_requests === 1 ? "" : "s"}${
        summary.open_request_status ? ` (${summary.open_request_status})` : ""
      }.`
    );
  } else {
    insights.push("No open maintenance requests - everything looks good.");
  }

  return insights.slice(0, 4);
}

export default function AiInsightsCard({ summary }) {
  const insights = useMemo(() => buildInsights(summary || {}), [summary]);

  return (
    <div className="content-card ai-insights-card">
      <div className="card-heading">
        <div>
          <span className="section-kicker">AI INSIGHTS</span>
          <h3>Smart summary for you</h3>
        </div>
        <div className="ai-insights-icon">
          <Sparkles size={18} />
        </div>
      </div>

      <ul className="ai-insights-list">
        {insights.map((text, index) => (
          <li key={index}>{text}</li>
        ))}
      </ul>
    </div>
  );
}
