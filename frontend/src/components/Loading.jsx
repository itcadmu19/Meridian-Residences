import React from "react";
import { Loader2 } from "lucide-react";

export default function Loading({ label = "Loading..." }) {
  return (
    <div className="state-block">
      <Loader2 size={24} className="spin" />
      <span>{label}</span>
    </div>
  );
}
