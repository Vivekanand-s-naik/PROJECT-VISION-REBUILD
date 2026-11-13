import React, { useState } from "react";
import "./Sidebar.css";
import { UilSignOutAlt, UilEstate, UilVideo, UilTable, UilMicrophone, UilBars } from "@iconscout/react-unicons";
import { motion } from "framer-motion";

const navItems = [
  { icon: UilEstate, heading: "Analytics", link: "/react" },
  { icon: UilVideo, heading: "Live Command", link: "/dashboard" },
  { icon: UilTable, heading: "Camera Grid", link: "/grid" },
  { icon: UilMicrophone, heading: "AI Notes", link: "/notes" }
];

const Sidebar = () => {
  const [selected, setSelected] = useState(0);
  const [expanded, setExpanded] = useState(true);

  const handleNav = (index, link) => {
    setSelected(index);
    if (link !== "/react") {
      window.location.href = link;
    }
  };

  const handleSignOut = () => {
    window.location.href = "/logout";
  };

  const sidebarVariants = {
    true: { left: "0" },
    false: { left: "-60%" }
  };

  return (
    <>
      <div className="bars" style={expanded ? { left: "60%" } : { left: "5%" }} onClick={() => setExpanded(!expanded)}>
        <UilBars />
      </div>
      <motion.div
        className="sidebar"
        variants={sidebarVariants}
        animate={window.innerWidth <= 768 ? `${expanded}` : ""}
      >
        <div className="logo" style={{ marginBottom: "20px", display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ fontWeight: "bold", fontSize: "1.3rem", color: "#f8fafc" }}>
            PROJECT<span style={{ color: "#38bdf8" }}>VISION</span>
          </span>
        </div>

        <div className="menu">
          {navItems.map((item, index) => {
            return (
              <div
                className={selected === index ? "menuItem active" : "menuItem"}
                key={index}
                onClick={() => handleNav(index, item.link)}
                style={{ cursor: "pointer" }}
              >
                <item.icon />
                <span>{item.heading}</span>
              </div>
            );
          })}
          <div className="menuItem" onClick={handleSignOut} style={{ cursor: "pointer", color: "#ef4444" }}>
            <UilSignOutAlt />
            <span>Sign Out</span>
          </div>
        </div>
      </motion.div>
    </>
  );
};

export default Sidebar;
