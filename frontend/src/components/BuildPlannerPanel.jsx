import React, { useState, useRef, useEffect } from "react";
import { streamBuildPlan, exportPdf } from "../api.js";

const styles = {
  container: {
    background: "#16213e",
    borderRadius: 12,
    padding: 16,
    display: "flex",
    flexDirection: "column",
    gap: 12,
    height: "100%",
  },
  title: { fontSize: 16, fontWeight: 700, color: "#e94560", letterSpacing: 1 },
  subtitle: { fontSize: 12, color: "#666" },
  textarea: {
    background: "#0f0f1a",
    border: "1px solid #333",
    borderRadius: 8,
    color: "#e0e0e0",
    padding: 10,
    fontSize: 14,
    resize: "vertical",
    minHeight: 72,
    fontFamily: "inherit",
    outline: "none",
  },
  controls: { display: "flex", gap: 8 },
  btnGenerate: {
    background: "#e94560",
    color: "#fff",
    border: "none",
    borderRadius: 6,
    padding: "10px 20px",
    fontWeight: 700,
    cursor: "pointer",
    fontSize: 14,
    flex: 1,
  },
  btnStop: {
    background: "#333",
    color: "#e0e0e0",
    border: "none",
    borderRadius: 6,
    padding: "10px 16px",
    cursor: "pointer",
    fontSize: 14,
  },
  outputWrapper: {
    flex: 1,
    background: "#0f0f1a",
    borderRadius: 8,
    padding: 14,
    overflowY: "auto",
    fontFamily: "'Courier New', monospace",
    fontSize: 13,
    lineHeight: 1.7,
    color: "#d0d0d0",
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
    minHeight: 200,
  },
  placeholder: { color: "#444", fontStyle: "italic" },
  cursor: {
    display: "inline-block",
    width: 8,
    height: 14,
    background: "#e94560",
    marginLeft: 2,
    verticalAlign: "text-bottom",
    animation: "blink 0.9s step-end infinite",
  },
  statusRow: { display: "flex", alignItems: "center", gap: 8, fontSize: 12, color: "#666" },
  dot: { width: 8, height: 8, borderRadius: "50%", background: "#4caf50" },
  errorText: { color: "#ff6b6b", fontSize: 13 },
  btnPdf: {
    background: "#ffd700",
    color: "#1a1a2e",
    border: "none",
    borderRadius: 6,
    padding: "10px 18px",
    fontWeight: 700,
    cursor: "pointer",
    fontSize: 13,
  },
};

// Render text with basic markdown-like formatting (bold **text**, numbered lists)
function renderPlan(text) {
  return text
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/^(\d+\.\s)/gm, '<span style="color:#e94560;font-weight:700">$1</span>');
}

export default function BuildPlannerPanel({ inventoryTotal }) {
  const [prompt, setPrompt] = useState("");
  const [planText, setPlanText] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [planDone, setPlanDone] = useState(false);
  const [exportingPdf, setExportingPdf] = useState(false);
  const [error, setError] = useState("");
  const stopRef = useRef(null);
  const outputRef = useRef(null);

  // Auto-scroll as plan streams in
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [planText]);

  // Inject blink keyframe once
  useEffect(() => {
    const style = document.createElement("style");
    style.textContent = "@keyframes blink { 50% { opacity: 0; } }";
    document.head.appendChild(style);
    return () => document.head.removeChild(style);
  }, []);

  const handleGenerate = () => {
    if (!prompt.trim()) return;
    setPlanText("");
    setError("");
    setPlanDone(false);
    setStreaming(true);

    const stop = streamBuildPlan(
      prompt,
      (chunk) => setPlanText((prev) => prev + chunk),
      () => { setStreaming(false); setPlanDone(true); },
      () => {
        setError("Connection error. Is the backend running?");
        setStreaming(false);
      },
    );
    stopRef.current = stop;
  };

  const handleStop = () => {
    stopRef.current?.();
    setStreaming(false);
  };

  const handleExportPdf = async () => {
    setExportingPdf(true);
    try {
      await exportPdf(planText, prompt);
    } catch {
      setError("PDF export failed. Is the backend running?");
    } finally {
      setExportingPdf(false);
    }
  };

  return (
    <div style={styles.container}>
      <div>
        <div style={styles.title}>BUILD PLANNER</div>
        <div style={styles.subtitle}>
          {inventoryTotal > 0
            ? `${inventoryTotal} pieces in inventory — ready to plan`
            : "Scan pieces first, then describe what you want to build"}
        </div>
      </div>

      <textarea
        style={styles.textarea}
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        placeholder="e.g. Build the most impressive medieval castle possible"
        onKeyDown={(e) => {
          if (e.key === "Enter" && e.ctrlKey) handleGenerate();
        }}
      />

      <div style={styles.controls}>
        <button
          style={{ ...styles.btnGenerate, opacity: streaming || !prompt.trim() ? 0.6 : 1 }}
          onClick={handleGenerate}
          disabled={streaming || !prompt.trim()}
        >
          {streaming ? "Generating…" : "Generate Plan"}
        </button>
        {streaming && (
          <button style={styles.btnStop} onClick={handleStop}>Stop</button>
        )}
        {planDone && planText && !streaming && (
          <button
            style={{ ...styles.btnPdf, opacity: exportingPdf ? 0.6 : 1 }}
            onClick={handleExportPdf}
            disabled={exportingPdf}
            title="Download as Lego-style PDF manual"
          >
            {exportingPdf ? "Exporting…" : "Download PDF"}
          </button>
        )}
      </div>

      {error && <div style={styles.errorText}>{error}</div>}

      <div
        ref={outputRef}
        style={styles.outputWrapper}
        dangerouslySetInnerHTML={{
          __html: planText
            ? renderPlan(planText) + (streaming ? '<span style="display:inline-block;width:8px;height:14px;background:#e94560;margin-left:2px;vertical-align:text-bottom;animation:blink 0.9s step-end infinite"></span>' : "")
            : `<span style="color:#444;font-style:italic">Your build plan will appear here as it streams from the AI…\n\nTip: Press Ctrl+Enter to generate.</span>`,
        }}
      />

      {streaming && (
        <div style={styles.statusRow}>
          <div style={styles.dot} />
          Streaming from Ollama (llama3.2)…
        </div>
      )}
    </div>
  );
}
