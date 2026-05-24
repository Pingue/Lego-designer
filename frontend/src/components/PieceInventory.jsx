import React, { useEffect, useState, useImperativeHandle, forwardRef } from "react";
import { getInventory, clearInventory } from "../api.js";

const PIECE_COLORS = [
  "#e94560", "#0f3460", "#ffd700", "#4caf50",
  "#2196f3", "#ff9800", "#9c27b0", "#00bcd4",
];

const styles = {
  container: {
    background: "#16213e",
    borderRadius: 12,
    padding: 16,
    display: "flex",
    flexDirection: "column",
    gap: 10,
  },
  header: { display: "flex", justifyContent: "space-between", alignItems: "center" },
  title: { fontSize: 16, fontWeight: 700, color: "#e94560", letterSpacing: 1 },
  totalBadge: {
    background: "#e94560",
    color: "#fff",
    borderRadius: 12,
    padding: "2px 10px",
    fontSize: 13,
    fontWeight: 700,
  },
  clearBtn: {
    background: "transparent",
    color: "#aaa",
    border: "1px solid #333",
    borderRadius: 6,
    padding: "4px 10px",
    cursor: "pointer",
    fontSize: 12,
  },
  empty: { color: "#555", fontSize: 13, textAlign: "center", padding: "20px 0" },
  table: { width: "100%", borderCollapse: "collapse" },
  th: {
    textAlign: "left",
    fontSize: 11,
    color: "#666",
    textTransform: "uppercase",
    letterSpacing: 1,
    paddingBottom: 6,
    borderBottom: "1px solid #222",
  },
  td: { padding: "6px 4px", fontSize: 13, borderBottom: "1px solid #1a1a2e" },
  dot: { display: "inline-block", width: 10, height: 10, borderRadius: 2, marginRight: 6 },
  countBadge: {
    display: "inline-block",
    background: "#0f3460",
    borderRadius: 10,
    padding: "2px 8px",
    fontWeight: 700,
    fontSize: 13,
  },
  bar: { background: "#0f0f1a", borderRadius: 4, height: 6, overflow: "hidden" },
  barFill: { height: "100%", borderRadius: 4, transition: "width 0.3s" },
};

const PieceInventory = forwardRef(function PieceInventory(_, ref) {
  const [inventory, setInventory] = useState({ counts: {}, total: 0 });

  const refresh = async () => {
    try {
      const data = await getInventory();
      setInventory(data);
    } catch {
      // silently ignore network errors
    }
  };

  useEffect(() => {
    refresh();
  }, []);

  // Expose refresh() so parent can call it after a scan
  useImperativeHandle(ref, () => ({ refresh }));

  const handleClear = async () => {
    await clearInventory();
    setInventory({ counts: {}, total: 0 });
  };

  const entries = Object.entries(inventory.counts).sort((a, b) => b[1] - a[1]);
  const maxCount = entries.length > 0 ? entries[0][1] : 1;

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={styles.title}>INVENTORY</span>
          <span style={styles.totalBadge}>{inventory.total} pcs</span>
        </div>
        <button style={styles.clearBtn} onClick={handleClear}>Clear</button>
      </div>

      {entries.length === 0 ? (
        <div style={styles.empty}>No pieces scanned yet.<br />Use the camera to scan Lego pieces.</div>
      ) : (
        <table style={styles.table}>
          <thead>
            <tr>
              <th style={styles.th}>Piece</th>
              <th style={{ ...styles.th, width: 50, textAlign: "right" }}>Count</th>
              <th style={{ ...styles.th, width: 80 }}></th>
            </tr>
          </thead>
          <tbody>
            {entries.map(([name, count], i) => (
              <tr key={name}>
                <td style={styles.td}>
                  <span
                    style={{ ...styles.dot, background: PIECE_COLORS[i % PIECE_COLORS.length] }}
                  />
                  {name}
                </td>
                <td style={{ ...styles.td, textAlign: "right" }}>
                  <span style={styles.countBadge}>{count}</span>
                </td>
                <td style={styles.td}>
                  <div style={styles.bar}>
                    <div
                      style={{
                        ...styles.barFill,
                        width: `${(count / maxCount) * 100}%`,
                        background: PIECE_COLORS[i % PIECE_COLORS.length],
                      }}
                    />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
});

export default PieceInventory;
