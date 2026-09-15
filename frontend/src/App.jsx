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
