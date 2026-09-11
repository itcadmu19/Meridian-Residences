import React from "react";

export default function Textarea({ label, error, id, ...rest }) {
  return (
    <div className="field">
      {label && (
        <label className="field__label" htmlFor={id}>
          {label}
        </label>
      )}
      <textarea id={id} className="textarea" {...rest} />
      {error && <span className="field__error">{error}</span>}
    </div>
  );
}
