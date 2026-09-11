import React from "react";

export default function Input({ label, error, id, ...rest }) {
  return (
    <div className="field">
      {label && (
        <label className="field__label" htmlFor={id}>
          {label}
        </label>
      )}
      <input id={id} className="input" {...rest} />
      {error && <span className="field__error">{error}</span>}
    </div>
  );
}
