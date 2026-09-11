import React from "react";

export default function SecondaryButton({ children, className = "", ...rest }) {
  return (
    <button className={`btn btn--secondary ${className}`.trim()} {...rest}>
      {children}
    </button>
  );
}
