import { useState, useEffect } from "react";
import axios from "axios";

const API = "http://127.0.0.1:8000/api";

function StatCard({ label, value, color }) {
  return (
    <div style={{
      background: "white", borderRadius: 8, padding: "20px",
      boxShadow: "0 2px 8px rgba(0,0,0,0.1)", textAlign: "center"
    }}>
      <div style={{ fontSize: 32, fontWeight: "bold", color }}>{value}</div>
      <div style={{ color: "#666", marginTop: 4 }}>{label}</div>
    </div>
  );
}

function UploadSection({ tenantId, onUploadDone }) {
  const [sourceType, setSourceType] = useState("SAP");
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const handleUpload = async () => {
    if (!file) return setMessage("Please select a file!");
    setLoading(true);
    const formData = new FormData();
    formData.append("source_type", sourceType);
    formData.append("tenant_id", tenantId);
    formData.append("file", file);

    try {
      const res = await axios.post(`${API}/ingestion/ingest/`, formData);
      setMessage(`✅ Success! ${res.data.rows_created} rows ingested, ${res.data.errors} errors.`);
      onUploadDone();
    } catch (err) {
      setMessage("❌ Upload failed: " + (err.response?.data?.error || err.message));
    }
    setLoading(false);
  };

  return (
    <div style={{ background: "white", borderRadius: 8, padding: 24, boxShadow: "0 2px 8px rgba(0,0,0,0.1)", marginBottom: 24 }}>
      <h2 style={{ marginTop: 0 }}>📤 Upload Data</h2>
      <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "center" }}>
        <select value={sourceType} onChange={e => setSourceType(e.target.value)}
          style={{ padding: "8px 12px", borderRadius: 6, border: "1px solid #ddd", fontSize: 14 }}>
          <option value="SAP">SAP (Fuel & Procurement)</option>
          <option value="UTILITY">Utility (Electricity)</option>
          <option value="TRAVEL">Corporate Travel</option>
        </select>
        <input type="file" accept=".csv" onChange={e => setFile(e.target.files[0])}
          style={{ padding: "8px", border: "1px solid #ddd", borderRadius: 6 }} />
        <button onClick={handleUpload} disabled={loading}
          style={{ padding: "8px 20px", background: "#2563eb", color: "white", border: "none", borderRadius: 6, cursor: "pointer", fontSize: 14 }}>
          {loading ? "Uploading..." : "Upload"}
        </button>
      </div>
      {message && <div style={{ marginTop: 12, padding: 10, background: "#f0fdf4", borderRadius: 6, color: "#166534" }}>{message}</div>}
    </div>
  );
}

function ReviewTable({ rows, onReview }) {
  const statusColor = { PENDING: "#f59e0b", FLAGGED: "#ef4444", APPROVED: "#22c55e", REJECTED: "#6b7280" };

  return (
    <div style={{ background: "white", borderRadius: 8, padding: 24, boxShadow: "0 2px 8px rgba(0,0,0,0.1)" }}>
      <h2 style={{ marginTop: 0 }}>📋 Activity Rows</h2>
      <div style={{ overflowX: "auto" }}>
        <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
          <thead>
            <tr style={{ background: "#f8fafc" }}>
              {["ID", "Category", "Scope", "Date", "Location", "Quantity", "Status", "Flag Reason", "Actions"].map(h => (
                <th key={h} style={{ padding: "10px 12px", textAlign: "left", borderBottom: "2px solid #e2e8f0", whiteSpace: "nowrap" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && (
              <tr><td colSpan={9} style={{ padding: 24, textAlign: "center", color: "#888" }}>No rows found. Upload a file to get started.</td></tr>
            )}
            {rows.map(row => (
              <tr key={row.id} style={{ borderBottom: "1px solid #f1f5f9" }}>
                <td style={{ padding: "8px 12px" }}>{row.id}</td>
                <td style={{ padding: "8px 12px" }}>{row.category}</td>
                <td style={{ padding: "8px 12px" }}>Scope {row.scope}</td>
                <td style={{ padding: "8px 12px" }}>{row.activity_date || "-"}</td>
                <td style={{ padding: "8px 12px" }}>{row.location || "-"}</td>
                <td style={{ padding: "8px 12px" }}>
                  {row.quantity_kwh ? `${row.quantity_kwh} kWh` :
                    row.quantity_liters ? `${row.quantity_liters} L` :
                      row.quantity_km ? `${Math.round(row.quantity_km)} km` :
                        row.raw_quantity || "-"}
                </td>
                <td style={{ padding: "8px 12px" }}>
                  <span style={{ padding: "3px 8px", borderRadius: 12, background: statusColor[row.status] + "22", color: statusColor[row.status], fontWeight: 600, fontSize: 12 }}>
                    {row.status}
                  </span>
                </td>
                <td style={{ padding: "8px 12px", color: "#ef4444", fontSize: 12 }}>{row.flag_reason || "-"}</td>
                <td style={{ padding: "8px 12px" }}>
                  {!row.locked ? (
                    <div style={{ display: "flex", gap: 6 }}>
                      <button onClick={() => onReview(row.id, "APPROVED")}
                        style={{ padding: "4px 10px", background: "#22c55e", color: "white", border: "none", borderRadius: 4, cursor: "pointer", fontSize: 12 }}>
                        ✓ Approve
                      </button>
                      <button onClick={() => onReview(row.id, "FLAGGED")}
                        style={{ padding: "4px 10px", background: "#ef4444", color: "white", border: "none", borderRadius: 4, cursor: "pointer", fontSize: 12 }}>
                        ⚑ Flag
                      </button>
                    </div>
                  ) : (
                    <span style={{ color: "#6b7280", fontSize: 12 }}>🔒 Locked</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default function App() {
  const [rows, setRows] = useState([]);
  const [stats, setStats] = useState(null);
  const [statusFilter, setStatusFilter] = useState("");
  const TENANT_ID = 1;

  const fetchRows = async () => {
    try {
      const url = statusFilter
        ? `${API}/review/rows/?tenant_id=${TENANT_ID}&status=${statusFilter}`
        : `${API}/review/rows/?tenant_id=${TENANT_ID}`;
      const res = await axios.get(url);
      setRows(res.data);
    } catch (err) {
      console.error("Failed to fetch rows", err);
    }
  };

  const fetchStats = async () => {
    try {
      const res = await axios.get(`${API}/review/stats/?tenant_id=${TENANT_ID}`);
      setStats(res.data);
    } catch (err) {
      console.error("Failed to fetch stats", err);
    }
  };

  useEffect(() => {
    fetchRows();
    fetchStats();
  }, [statusFilter]);

  const handleReview = async (rowId, newStatus) => {
    try {
      await axios.post(`${API}/review/rows/${rowId}/review/`, { status: newStatus });
      fetchRows();
      fetchStats();
    } catch (err) {
      alert("Review failed: " + (err.response?.data?.error || err.message));
    }
  };

  return (
    <div style={{ minHeight: "100vh", background: "#f1f5f9", fontFamily: "sans-serif" }}>
      <div style={{ background: "#1e3a5f", color: "white", padding: "16px 32px", display: "flex", alignItems: "center", gap: 12 }}>
        <span style={{ fontSize: 24 }}>🌿</span>
        <div>
          <div style={{ fontSize: 20, fontWeight: "bold" }}>Breathe ESG</div>
          <div style={{ fontSize: 12, opacity: 0.7 }}>Emissions Data Ingestion & Review</div>
        </div>
      </div>

      <div style={{ maxWidth: 1200, margin: "0 auto", padding: 24 }}>
        {stats && (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))", gap: 16, marginBottom: 24 }}>
            <StatCard label="Total Rows" value={stats.total} color="#2563eb" />
            <StatCard label="Pending" value={stats.pending} color="#f59e0b" />
            <StatCard label="Flagged" value={stats.flagged} color="#ef4444" />
            <StatCard label="Approved" value={stats.approved} color="#22c55e" />
            <StatCard label="Rejected" value={stats.rejected} color="#6b7280" />
          </div>
        )}

        <UploadSection tenantId={TENANT_ID} onUploadDone={() => { fetchRows(); fetchStats(); }} />

        <div style={{ marginBottom: 16, display: "flex", gap: 8 }}>
          {["", "PENDING", "FLAGGED", "APPROVED", "REJECTED"].map(s => (
            <button key={s} onClick={() => setStatusFilter(s)}
              style={{ padding: "6px 16px", borderRadius: 20, border: "none", cursor: "pointer", fontSize: 13,
                background: statusFilter === s ? "#2563eb" : "#e2e8f0",
                color: statusFilter === s ? "white" : "#374151" }}>
              {s || "All"}
            </button>
          ))}
        </div>

        <ReviewTable rows={rows} onReview={handleReview} />
      </div>
    </div>
  );
}
