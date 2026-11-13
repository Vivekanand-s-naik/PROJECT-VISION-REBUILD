import React, { useState, useEffect, useCallback } from "react";
import Cards from "../Cards/Cards";
import Table from "../Table/Table";
import "./MainDash.css";

const MainDash = () => {
  const [dashboardData, setDashboardData] = useState(null);
  const [currentUser, setCurrentUser] = useState(null);
  const [systemActive, setSystemActive] = useState(false);
  const [loading, setLoading] = useState(true);
  const [toggling, setToggling] = useState(false);
  const [activeRole, setActiveRole] = useState("admin");

  // Fetch role-specific user data from Flask backend
  const fetchData = useCallback(async (roleOverride = null) => {
    try {
      setLoading(true);
      const url = roleOverride ? `/api/dashboard/user-data?as_role=${roleOverride}` : "/api/dashboard/user-data";
      const res = await fetch(url);
      const json = await res.json();

      if (json.success) {
        setDashboardData(json.data);
        setCurrentUser(json.user);
        setSystemActive(json.data.system_active);
        setActiveRole(json.user?.role || "admin");
      }
    } catch (err) {
      console.error("Failed to fetch dashboard data:", err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
    const interval = setInterval(() => {
      fetch("/api/system/status")
        .then((r) => r.json())
        .then((d) => setSystemActive(d.active))
        .catch(() => {});
    }, 4000);
    return () => clearInterval(interval);
  }, [fetchData]);

  const handleRoleSwitch = (role) => {
    setActiveRole(role);
    fetchData(role);
  };

  const handleToggleSystem = async () => {
    setToggling(true);
    try {
      const endpoint = systemActive ? "/api/system/stop" : "/api/system/start";
      const res = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" }
      });
      const data = await res.json();
      if (data.success) {
        setSystemActive(data.active);
      } else {
        alert(data.message || data.error);
      }
    } catch (err) {
      alert("System control error: " + err);
    } finally {
      setToggling(false);
    }
  };

  return (
    <div className="MainDash">
      {/* Top Header & Role Switcher */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px", marginBottom: "16px" }}>
        <div>
          <h1 style={{ margin: "0 0 6px 0", fontSize: "1.8rem" }}>
            {dashboardData?.title || "Vision Command Dashboard"}
          </h1>
          {currentUser && (
            <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "0.85rem", color: "#94a3b8" }}>
              <span>Signed in as: <strong style={{ color: "#f8fafc" }}>{currentUser.name}</strong></span>
              <span style={{
                background: currentUser.role === "admin" ? "#3b82f6" : currentUser.role === "faculty" ? "#06b6d4" : "#10b981",
                color: "#fff",
                padding: "2px 8px",
                borderRadius: "12px",
                fontSize: "0.7rem",
                fontWeight: "bold",
                textTransform: "uppercase"
              }}>
                {currentUser.role}
              </span>
            </div>
          )}
        </div>

        {/* Action Controls & Role Gating */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
          {/* Quick RBAC Role Switcher */}
          <div style={{ display: "flex", background: "rgba(15, 23, 42, 0.6)", borderRadius: "8px", padding: "3px", border: "1px solid rgba(255,255,255,0.08)" }}>
            {["admin", "faculty", "student"].map((r) => (
              <button
                key={r}
                onClick={() => handleRoleSwitch(r)}
                style={{
                  background: activeRole === r ? "rgba(59, 130, 246, 0.3)" : "transparent",
                  color: activeRole === r ? "#60a5fa" : "#94a3b8",
                  border: activeRole === r ? "1px solid #3b82f6" : "1px solid transparent",
                  padding: "4px 10px",
                  borderRadius: "6px",
                  fontSize: "0.75rem",
                  cursor: "pointer",
                  fontWeight: activeRole === r ? "600" : "normal",
                  textTransform: "capitalize",
                  transition: "all 0.2s"
                }}
              >
                {r}
              </button>
            ))}
          </div>

          {/* Vision Camera System Start/Stop Button */}
          {dashboardData?.system_controls_enabled ? (
            <button
              onClick={handleToggleSystem}
              disabled={toggling}
              style={{
                background: systemActive ? "linear-gradient(135deg, #ef4444 0%, #b91c1c 100%)" : "linear-gradient(135deg, #10b981 0%, #047857 100%)",
                color: "white",
                border: "none",
                borderRadius: "8px",
                padding: "8px 16px",
                fontSize: "0.85rem",
                fontWeight: "600",
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "6px",
                boxShadow: systemActive ? "0 4px 12px rgba(239, 68, 68, 0.3)" : "0 4px 12px rgba(16, 185, 129, 0.3)"
              }}
            >
              <span>{systemActive ? "■ Stop Vision System" : "▶ Start Vision System"}</span>
              <span style={{
                background: "rgba(0,0,0,0.25)",
                fontSize: "0.65rem",
                padding: "2px 6px",
                borderRadius: "4px"
              }}>
                {systemActive ? "ACTIVE" : "STANDBY"}
              </span>
            </button>
          ) : (
            <span style={{
              background: "rgba(100, 116, 139, 0.2)",
              color: "#94a3b8",
              padding: "6px 12px",
              borderRadius: "8px",
              fontSize: "0.75rem",
              border: "1px solid rgba(255,255,255,0.06)"
            }}>
              System Control Restricted (Faculty/Admin)
            </span>
          )}
        </div>
      </div>

      {/* Dynamic Telemetry Cards */}
      <Cards cards={dashboardData?.cards || []} />

      {/* Role-Specific Activity Table */}
      <div style={{ marginTop: "24px" }}>
        <Table
          title={dashboardData?.table_title}
          headers={dashboardData?.table_headers}
          rows={dashboardData?.table_rows}
        />
      </div>
    </div>
  );
};

export default MainDash;
