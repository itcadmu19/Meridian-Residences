import React from "react";
import { Routes, Route } from "react-router-dom";
import Navbar from "./components/Navbar.jsx";
import Sidebar from "./components/Sidebar.jsx";
import ProtectedRoute from "./components/ProtectedRoute.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Maintenance from "./pages/Maintenance.jsx";
import ComingSoon from "./pages/ComingSoon.jsx";
import Login from "./pages/Login.jsx";
import { useAuth } from "./context/AuthContext.jsx";

export default function App() {
  const { currentUser } = useAuth();

  if (!currentUser) {
    return (
      <Routes>
        <Route path="*" element={<Login />} />
      </Routes>
    );
  }

  return (
    <div className="app-shell">
      <Sidebar />
      <div className="app-main">
        <Navbar />
        <div className="page-content">
          <Routes>
            <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/maintenance" element={<ProtectedRoute><Maintenance /></ProtectedRoute>} />
            <Route path="/lease" element={<ProtectedRoute><ComingSoon title="My Lease" /></ProtectedRoute>} />
            <Route path="/invoices" element={<ProtectedRoute><ComingSoon title="Invoices" /></ProtectedRoute>} />
            <Route path="/assistant" element={<ProtectedRoute><ComingSoon title="AI Assistant" /></ProtectedRoute>} />
            <Route path="/profile" element={<ProtectedRoute><ComingSoon title="Profile" /></ProtectedRoute>} />
            <Route path="/login" element={<Dashboard />} />
          </Routes>
        </div>
      </div>
    </div>
  );
}

