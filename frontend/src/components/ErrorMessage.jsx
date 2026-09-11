// NOTE: Placeholder — reconcile with the shared-UI owner's ErrorMessage.jsx
// if one already exists in the merged repo.

export default function ErrorMessage({ message, onRetry }) {
  return (
    <div
      role="alert"
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: "12px",
        background: "#FBEAEA",
        border: "1px solid #C94C4C",
        borderRadius: "8px",
        padding: "12px 16px",
        color: "#C94C4C",
        fontSize: "13px"
      }}
    >
      <span>{message}</span>
      {onRetry && (
        <button
          onClick={onRetry}
          style={{
            background: "transparent",
            border: "1px solid #C94C4C",
            color: "#C94C4C",
            borderRadius: "6px",
            padding: "4px 10px",
            fontSize: "12px",
            fontWeight: 600
          }}
        >
          Retry
        </button>
      )}
    </div>
  );
}