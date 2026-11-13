import * as React from "react";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import Paper from "@mui/material/Paper";
import "./Table.css";

const makeStyle = (status) => {
  if (status === "Approved" || status === "Active") {
    return {
      background: "rgba(145, 254, 159, 0.25)",
      color: "#4ade80",
      fontWeight: "bold",
      padding: "4px 10px",
      borderRadius: "6px",
      fontSize: "0.8rem"
    };
  } else if (status === "Pending" || status === "Warning") {
    return {
      background: "rgba(255, 173, 173, 0.25)",
      color: "#f87171",
      fontWeight: "bold",
      padding: "4px 10px",
      borderRadius: "6px",
      fontSize: "0.8rem"
    };
  } else {
    return {
      background: "rgba(89, 191, 255, 0.25)",
      color: "#38bdf8",
      fontWeight: "bold",
      padding: "4px 10px",
      borderRadius: "6px",
      fontSize: "0.8rem"
    };
  }
};

export default function BasicTable({ title, headers, rows }) {
  const tableHeaders = headers || ["Name", "ID / Course", "Role / Status", "Details / Hash", "Status"];
  const tableRows = rows || [];

  return (
    <div className="Table">
      <h2 style={{ marginBottom: "16px", color: "#f8fafc", fontSize: "1.4rem" }}>
        <b>{title || "Activity & Attendance Ledger"}</b>
      </h2>
      <TableContainer
        component={Paper}
        style={{
          boxShadow: "0px 13px 20px 0px rgba(0, 0, 0, 0.25)",
          background: "rgba(30, 41, 59, 0.8)",
          backdropFilter: "blur(12px)",
          borderRadius: "12px",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          overflow: "hidden"
        }}
      >
        <Table sx={{ minWidth: 650 }} aria-label="user telemetry table">
          <TableHead>
            <TableRow style={{ background: "rgba(15, 23, 42, 0.6)" }}>
              {tableHeaders.map((header, idx) => (
                <TableCell key={idx} style={{ color: "#94a3b8", fontWeight: "600", fontSize: "0.85rem" }}>
                  {header}
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {tableRows.length === 0 ? (
              <TableRow>
                <TableCell colSpan={tableHeaders.length} style={{ textAlign: "center", color: "#64748b", padding: "24px" }}>
                  No records to display.
                </TableCell>
              </TableRow>
            ) : (
              tableRows.map((row, idx) => (
                <TableRow
                  key={idx}
                  sx={{
                    "&:last-child td, &:last-child th": { border: 0 },
                    "&:hover": { background: "rgba(255, 255, 255, 0.04)" },
                    transition: "background 0.2s"
                  }}
                >
                  <TableCell component="th" scope="row" style={{ color: "#f8fafc", fontWeight: "600" }}>
                    {row.name}
                  </TableCell>
                  <TableCell align="left" style={{ color: "#cbd5e1", fontSize: "0.85rem" }}>
                    {row.id}
                  </TableCell>
                  <TableCell align="left" style={{ color: "#94a3b8", fontSize: "0.85rem" }}>
                    {row.role}
                  </TableCell>
                  <TableCell align="left" style={{ color: "#cbd5e1", fontSize: "0.85rem" }}>
                    {row.meta}
                  </TableCell>
                  <TableCell align="left">
                    <span className="status" style={makeStyle(row.status)}>{row.status}</span>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  );
}
