import React from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import AppShell from "./components/AppShell";
import ProtectedRoute from "./components/ProtectedRoute";
import { useAuth } from "./context/AuthContext";
import AiAssistant from "./pages/AiAssistant";
import Dashboard from "./pages/Dashboard";
import Invoices from "./pages/Invoices";
import Lease from "./pages/Lease";
import Login from "./pages/Login";
import Maintenance from "./pages/Maintenance";
import Profile from "./pages/Profile";
import Register from "./pages/Register";

function ResidentOnlyRoute({ children }) {
  const { currentUser } = useAuth();
  if (currentUser?.role !== "resident") {
    return <Navigate to="/dashboard" replace />;
  }
  return children;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route
        element={
          <ProtectedRoute>
            <AppShell />
          </ProtectedRoute>
        }
      >
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/lease" element={<Lease />} />
        <Route path="/invoices" element={<Invoices />} />
        <Route path="/maintenance" element={<Maintenance />} />
        <Route
          path="/assistant"
          element={
            <ResidentOnlyRoute>
              <AiAssistant />
            </ResidentOnlyRoute>
          }
        />
        <Route path="/profile" element={<Profile />} />
        {/* Staff Lease Management now lives inside /lease, decided by role. */}
        <Route path="/owner/leases" element={<Navigate to="/lease" replace />} />
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
