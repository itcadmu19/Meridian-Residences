import React from "react";

export default function Button({ children, className = "", ...rest }) {
  return (
    <button className={`btn btn--primary ${className}`.trim()} {...rest}>
      {children}
    </button>
  );
}
