// NOTE: Placeholder implementation of a component owned by the shared-UI
// track (Section 12 of the UI Design System doc). If Card.jsx already
// exists in the merged repo, keep that version and delete this one —
// do not maintain two copies.

export default function Card({ children, style, ...rest }) {
  return (
    <div
      style={{
        background: "#FFFFFF",
        border: "1px solid #E4E7EC",
        borderRadius: "12px",
        padding: "20px",
        boxShadow: "0 2px 8px rgba(0,0,0,0.04)",
        ...style
      }}
      {...rest}
    >
      {children}
    </div>
  );
}