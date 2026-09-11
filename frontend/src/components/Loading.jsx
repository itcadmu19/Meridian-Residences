// NOTE: Placeholder — reconcile with the shared-UI owner's Loading.jsx
// if one already exists in the merged repo.

export default function Loading({ label = "Loading..." }) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: "8px",
        color: "#667085",
        fontSize: "13px",
        padding: "12px 0"
      }}
    >
      <span
        aria-hidden="true"
        style={{
          width: "14px",
          height: "14px",
          borderRadius: "50%",
          border: "2px solid #E4E7EC",
          borderTopColor: "#3C7A89",
          animation: "meridian-spin 0.8s linear infinite"
        }}
      />
      {label}
      <style>{`
        @keyframes meridian-spin {
          to { transform: rotate(360deg); }
        }
        @media (prefers-reduced-motion: reduce) {
          [aria-hidden="true"] { animation: none; }
        }
      `}</style>
    </div>
  );
}