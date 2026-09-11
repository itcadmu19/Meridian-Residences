import React from "react";
import { AlertTriangle } from "lucide-react";
import SecondaryButton from "./SecondaryButton.jsx";

export default function ErrorMessage({ message = "Something went wrong.", onRetry }) {
  return (
    <div className="state-block state-block--error">
      <AlertTriangle size={24} />
      <span>{message}</span>
      {onRetry && <SecondaryButton onClick={onRetry}>Try again</SecondaryButton>}
    </div>
  );
}
