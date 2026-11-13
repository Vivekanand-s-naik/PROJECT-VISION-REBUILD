import React from "react";
import CustomerReview from "../CustomerReview/CustomerReview";
import "./RightSide.css";

const RightSide = () => {
  return (
    <div className="RightSide">
      <div>
        <h2 style={{ fontSize: "1.2rem", margin: "0 0 10px 0", color: "#f8fafc" }}>
          <b>Vision System Matrix</b>
        </h2>
        <div style={{
          background: "rgba(30, 41, 59, 0.7)",
          padding: "14px",
          borderRadius: "10px",
          fontSize: "0.85rem",
          color: "#cbd5e1",
          lineHeight: "1.5",
          border: "1px solid rgba(255, 255, 255, 0.08)"
        }}>
          <div style={{ marginBottom: "8px" }}>
            <strong style={{ color: "#38bdf8" }}>Cam 01:</strong> Face Attendance & Anti-Spoof
          </div>
          <div style={{ marginBottom: "8px" }}>
            <strong style={{ color: "#fbbf24" }}>Cam 02:</strong> Pose & Violence Detection
          </div>
          <div style={{ marginBottom: "8px" }}>
            <strong style={{ color: "#34d399" }}>Cam 03:</strong> Gaze & Concentration Radar
          </div>
          <div>
            <strong style={{ color: "#f87171" }}>Cam 04:</strong> Weapon & Threat Monitor
          </div>
        </div>
      </div>
      <div style={{ marginTop: "16px" }}>
        <h3 style={{ fontSize: "1rem", color: "#94a3b8", marginBottom: "8px" }}>System Integrity Score</h3>
        <CustomerReview />
      </div>
    </div>
  );
};

export default RightSide;
