import React, { useRef, useState, useEffect } from "react";
import CameraFeed from "./components/CameraFeed.jsx";
import PieceInventory from "./components/PieceInventory.jsx";
import BuildPlannerPanel from "./components/BuildPlannerPanel.jsx";
import { getInventory } from "./api.js";

const styles = {
  app: {
    display: "flex",
    flexDirection: "column",
    height: "100vh",
    overflow: "hidden",
  },
  header: {
    background: "#0f3460",
    padding: "10px 24px",
    display: "flex",
    alignItems: "center",
    gap: 16,
    borderBottom: "2px solid #e94560",
    flexShrink: 0,
  },
  logo: { fontSize: 22, fontWeight: 900, color: "#fff", letterSpacing: 2 },
  logoAccent: { color: "#e94560" },
  subtitle: { fontSize: 12, color: "#aaa" },
  body: {
    display: "flex",
    flex: 1,
    overflow: "hidden",
    gap: 0,
  },
  leftPanel: {
    width: 380,
    flexShrink: 0,
    display: "flex",
    flexDirection: "column",
    gap: 12,
    padding: 16,
    overflowY: "auto",
    borderRight: "1px solid #1a1a2e",
  },
  rightPanel: {
    flex: 1,
    padding: 16,
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
  },
};

export default function App() {
  const inventoryRef = useRef(null);
  const [inventoryTotal, setInventoryTotal] = useState(0);

  const refreshInventory = async () => {
    inventoryRef.current?.refresh();
    const data = await getInventory();
    setInventoryTotal(data.total);
  };

  useEffect(() => {
    refreshInventory();
  }, []);

  return (
    <div style={styles.app}>
      <header style={styles.header}>
        <div>
          <div style={styles.logo}>
            <span style={styles.logoAccent}>LEGO</span> DESIGNER AI
          </div>
          <div style={styles.subtitle}>
            Classify pieces · Build your plan · Powered by local AI
          </div>
        </div>
      </header>

      <div style={styles.body}>
        <div style={styles.leftPanel}>
          <CameraFeed onPieceScanned={refreshInventory} />
          <PieceInventory ref={inventoryRef} />
        </div>

        <div style={styles.rightPanel}>
          <BuildPlannerPanel inventoryTotal={inventoryTotal} />
        </div>
      </div>
    </div>
  );
}
