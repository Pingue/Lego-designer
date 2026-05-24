import axios from "axios";

const api = axios.create({ baseURL: "" });

export async function classifyImage(base64jpeg) {
  const { data } = await api.post("/classify", { image: base64jpeg });
  return data;
}

export async function addToInventory(label, confidence) {
  const { data } = await api.post("/inventory/add", { label, confidence });
  return data;
}

export async function getInventory() {
  const { data } = await api.get("/inventory");
  return data;
}

export async function clearInventory() {
  const { data } = await api.delete("/inventory");
  return data;
}

/**
 * Opens an SSE connection to /build-plan?prompt=...
 * Calls onChunk(text) for each token, onDone() when finished, onError(err) on failure.
 * Returns a cleanup function that closes the connection.
 */
export function streamBuildPlan(prompt, onChunk, onDone, onError) {
  const url = `/build-plan?prompt=${encodeURIComponent(prompt)}`;
  const es = new EventSource(url);

  es.onmessage = (e) => {
    if (e.data === "[DONE]") {
      es.close();
      onDone();
    } else {
      // Restore newlines escaped by the server
      onChunk(e.data.replace(/\\n/g, "\n"));
    }
  };

  es.onerror = (err) => {
    es.close();
    onError(err);
  };

  return () => es.close();
}
