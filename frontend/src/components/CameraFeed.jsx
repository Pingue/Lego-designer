import React, { useRef, useEffect, useState, useCallback } from "react";
import { classifyImage, addToInventory } from "../api.js";

const CONFIDENCE_THRESHOLD = 0.75;
const MARGIN_THRESHOLD = 0.20;  // top-1 must beat top-2 by this much

const styles = {
  container: {
    background: "#16213e",
    borderRadius: 12,
    padding: 16,
    display: "flex",
    flexDirection: "column",
    gap: 12,
  },
  title: { fontSize: 16, fontWeight: 700, color: "#e94560", letterSpacing: 1 },
  videoWrapper: {
    position: "relative",
    borderRadius: 8,
    overflow: "hidden",
    background: "#0f0f1a",
    aspectRatio: "4/3",
  },
  video: { width: "100%", height: "100%", objectFit: "cover", display: "block" },
  overlay: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    background: "rgba(0,0,0,0.6)",
    padding: "6px 10px",
    fontSize: 13,
  },
  controls: { display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" },
  btnPrimary: {
    background: "#e94560",
    color: "#fff",
    border: "none",
    borderRadius: 6,
    padding: "8px 18px",
    fontWeight: 700,
    cursor: "pointer",
    fontSize: 14,
  },
  btnSecondary: {
    background: "#0f3460",
    color: "#e0e0e0",
    border: "none",
    borderRadius: 6,
    padding: "8px 14px",
    cursor: "pointer",
    fontSize: 13,
  },
  toggleLabel: { fontSize: 13, color: "#aaa", display: "flex", alignItems: "center", gap: 6 },
  slider: { width: 80 },
  result: { fontSize: 13, color: "#ffd700", minHeight: 18 },
  errorText: { fontSize: 13, color: "#ff6b6b" },
};

export default function CameraFeed({ onPieceScanned }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const intervalRef = useRef(null);

  const [cameraOn, setCameraOn] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [conveyorMode, setConveyorMode] = useState(false);
  const [intervalSec, setIntervalSec] = useState(3);
  const [lastResult, setLastResult] = useState(null);
  const [error, setError] = useState("");

  const startCamera = async () => {
    setError("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: "environment", width: { ideal: 640 }, height: { ideal: 480 } },
      });
      videoRef.current.srcObject = stream;
      await videoRef.current.play();
      setCameraOn(true);
    } catch (e) {
      setError(`Camera error: ${e.message}`);
    }
  };

  const stopCamera = () => {
    const stream = videoRef.current?.srcObject;
    stream?.getTracks().forEach((t) => t.stop());
    if (videoRef.current) videoRef.current.srcObject = null;
    setCameraOn(false);
    setConveyorMode(false);
  };

  const captureFrame = useCallback(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas || video.readyState < 2) return null;
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    canvas.getContext("2d").drawImage(video, 0, 0);
    // Strip the "data:image/jpeg;base64," prefix
    return canvas.toDataURL("image/jpeg", 0.85).split(",")[1];
  }, []);

  const scanOnce = useCallback(async () => {
    const frame = captureFrame();
    if (!frame) return;
    setScanning(true);
    try {
      const result = await classifyImage(frame);
      setLastResult(result);
      const margin = result.top3.length >= 2
        ? result.confidence - result.top3[1].confidence
        : result.confidence;
      if (result.confidence >= CONFIDENCE_THRESHOLD && margin >= MARGIN_THRESHOLD) {
        await addToInventory(result.label, result.confidence);
        onPieceScanned?.();
      }
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally {
      setScanning(false);
    }
  }, [captureFrame, onPieceScanned]);

  // Conveyor belt auto-scan
  useEffect(() => {
    if (conveyorMode && cameraOn) {
      intervalRef.current = setInterval(scanOnce, intervalSec * 1000);
    } else {
      clearInterval(intervalRef.current);
    }
    return () => clearInterval(intervalRef.current);
  }, [conveyorMode, cameraOn, intervalSec, scanOnce]);

  const confidenceColor = (c) => {
    if (c >= 0.8) return "#4caf50";
    if (c >= 0.5) return "#ffd700";
    return "#ff6b6b";
  };

  return (
    <div style={styles.container}>
      <div style={styles.title}>CAMERA FEED</div>

      <div style={styles.videoWrapper}>
        <video ref={videoRef} style={styles.video} muted playsInline />
        <canvas ref={canvasRef} style={{ display: "none" }} />
        {lastResult && (
          <div style={styles.overlay}>
            <span style={{ color: confidenceColor(lastResult.confidence), fontWeight: 700 }}>
              {lastResult.label}
            </span>
            {" "}
            <span style={{ color: "#aaa" }}>
              {(lastResult.confidence * 100).toFixed(1)}%
            </span>
          </div>
        )}
      </div>

      {error && <div style={styles.errorText}>{error}</div>}

      <div style={styles.controls}>
        {!cameraOn ? (
          <button style={styles.btnPrimary} onClick={startCamera}>Start Camera</button>
        ) : (
          <>
            <button
              style={{ ...styles.btnPrimary, opacity: scanning ? 0.6 : 1 }}
              onClick={scanOnce}
              disabled={scanning}
            >
              {scanning ? "Scanning…" : "Scan Piece"}
            </button>

            <label style={styles.toggleLabel}>
              <input
                type="checkbox"
                checked={conveyorMode}
                onChange={(e) => setConveyorMode(e.target.checked)}
              />
              Conveyor Belt
            </label>

            {conveyorMode && (
              <label style={styles.toggleLabel}>
                Every&nbsp;
                <input
                  type="range"
                  min={1}
                  max={10}
                  value={intervalSec}
                  style={styles.slider}
                  onChange={(e) => setIntervalSec(Number(e.target.value))}
                />
                &nbsp;{intervalSec}s
              </label>
            )}

            <button style={styles.btnSecondary} onClick={stopCamera}>Stop</button>
          </>
        )}
      </div>

      {lastResult && (
        <div style={styles.result}>
          Last: <strong>{lastResult.label}</strong> &nbsp;
          <span style={{ color: confidenceColor(lastResult.confidence) }}>
            {(lastResult.confidence * 100).toFixed(1)}% confidence
          </span>
          {(() => {
            const margin = lastResult.top3?.length >= 2
              ? lastResult.confidence - lastResult.top3[1].confidence : lastResult.confidence;
            if (lastResult.confidence < CONFIDENCE_THRESHOLD)
              return <span style={{ color: "#ff6b6b" }}> (low confidence — not added)</span>;
            if (margin < MARGIN_THRESHOLD)
              return <span style={{ color: "#ff6b6b" }}> (ambiguous — not added)</span>;
            return null;
          })()}
        </div>
      )}
    </div>
  );
}
