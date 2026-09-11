import { Sparkles } from "lucide-react";
import Assistant from "./pages/Assistant";

export default function App() {
  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#F7F5F0",
        display: "flex",
        justifyContent: "center",
        padding: "40px 20px"
      }}
    >
      <div style={{ width: "100%", maxWidth: "820px" }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            marginBottom: "24px",
            color: "#16324F",
            fontWeight: 600,
            fontSize: "14px"
          }}
        >
          <Sparkles size={16} color="#C6A15B" />
          MERIDIAN RESIDENCES — Story 4 standalone preview
        </div>

        {/*
          This is a bare preview shell, not the real app shell.
          In the merged repo, Assistant renders INSIDE the shared
          Navbar + Sidebar layout — it does not render its own chrome.
        */}
        <Assistant />
      </div>
    </div>
  );
}
