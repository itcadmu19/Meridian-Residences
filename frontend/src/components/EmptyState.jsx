import React from "react";
import { Inbox } from "lucide-react";

export default function EmptyState({ message = "Nothing here yet.", action }) {
  return (
    <div className="state-block">
      <Inbox size={24} />
      <span>{message}</span>
      {action}
    </div>
  );
}
