import React from "react";
import { Bot, FileText, Plus, Wrench } from "lucide-react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const actions = [
  {
    to: "/maintenance",
    icon: Wrench,
    title: "Report an issue",
    text: "Request maintenance",
  },
  {
    to: "/lease",
    icon: FileText,
    title: "View my lease",
    text: "Review agreement",
  },
  {
    to: "/maintenance",
    icon: Plus,
    title: "New request",
    text: "Create a service request",
  },
  {
    to: "/assistant",
    icon: Bot,
    title: "AI Assistant",
    text: "Ask about your lease or policies",
    residentOnly: true,
  },
];

export default function QuickActions() {
  const { currentUser } = useAuth();
  const visibleActions = actions.filter((action) => !action.residentOnly || currentUser?.role === "resident");

  return (
    <div className="quick-actions">
      {visibleActions.map(({ to, icon: Icon, title, text }) => (
        <Link to={to} className="quick-action" key={title}>
          <span className="quick-action-icon">
            <Icon size={18} />
          </span>
          <span>
            <strong>{title}</strong>
            <small>{text}</small>
          </span>
        </Link>
      ))}
    </div>
  );
}