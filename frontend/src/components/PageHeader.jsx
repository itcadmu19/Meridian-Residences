import React from "react";

export default function PageHeader({ title, description, action }) {
  return (
    <div className="page-header">
      <div>
        <h1 className="page-header__title">{title}</h1>
        {description && <p className="page-header__description">{description}</p>}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}
