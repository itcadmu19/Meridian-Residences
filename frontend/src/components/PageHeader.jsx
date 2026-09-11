// NOTE: Placeholder — reconcile with the shared-UI owner's PageHeader.jsx
// if one already exists in the merged repo (Section 12 of the UI Design
// System doc).

export default function PageHeader({ title, description, action }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "flex-start",
        justifyContent: "space-between",
        marginBottom: "24px"
      }}
    >
      <div>
        <h1
          style={{
            fontSize: "28px",
            fontWeight: 600,
            color: "#1F2933",
            margin: 0
          }}
        >
          {title}
        </h1>
        {description && (
          <p
            style={{
              fontSize: "14px",
              color: "#667085",
              margin: "4px 0 0"
            }}
          >
            {description}
          </p>
        )}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}