// src/api.js
const BACKEND_PORT = import.meta.env.VITE_BACKEND_PORT || "8765";
const BACKEND_HOST = import.meta.env.VITE_BACKEND_HOST || window.location.hostname;

export const BACKEND_URL = `http://${BACKEND_HOST}:${BACKEND_PORT}`;
export const BACKEND_URL_V1 = import.meta.env.VITE_BACKEND_URL_V1;

// Dashboard: obtener métricas agregadas
export async function getDashboardMetrics() {
  const res = await fetch(`${BACKEND_URL}/api/v1/dashboard/metrics`);
  if (!res.ok) throw new Error("Error al obtener métricas del dashboard");
  return await res.json();
}

export async function simpleSearch(
  query,
  llmModel,
  topK = 20,
  maxLlmChunks = 20,
  userEmail
) {
  const params = new URLSearchParams({ query });
  if (llmModel) params.append("llm_model", llmModel);
  if (topK) params.append("top_k", topK);
  if (maxLlmChunks) params.append("max_llm_chunks", maxLlmChunks);
  if (userEmail) params.append("user_email", userEmail);
  const res = await fetch(`${BACKEND_URL}/api/v1/search?${params.toString()}`);
  return res.json();
}

export async function synthesizeFinal(payload) {
  const res = await fetch(`${BACKEND_URL}/api/v1/synthesize/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return res.json();
}

export async function synthesizeFinalStream(payload, onChunk) {
  const res = await fetch(`${BACKEND_URL}/api/v1/synthesize/stream`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.body) return;
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let done = false;
  while (!done) {
    const { value, done: doneReading } = await reader.read();
    done = doneReading;
    if (value) {
      const chunk = decoder.decode(value);
      onChunk(chunk); // Solo el fragmento nuevo
    }
  }
}

export async function chatWithBackend(messages, userEmail) {
  const res = await fetch(`${BACKEND_URL}/api/v1/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, user_email: userEmail }),
  });
  return res.json();
}

export async function simpleSearchWithProgress(
  query,
  llmModel,
  topK = 20,
  maxLlmChunks = 20,
  onProgress
) {
  const params = new URLSearchParams({ query });
  if (llmModel) params.append("llm_model", llmModel);
  if (topK) params.append("top_k", topK);
  if (maxLlmChunks) params.append("max_llm_chunks", maxLlmChunks);
  const total = maxLlmChunks;
  let fakeResults = null;
  for (let i = 1; i <= total; i++) {
    await new Promise((res) => setTimeout(res, 120));
    onProgress && onProgress(i, total);
    if (i === total) {
      const res = await fetch(
        `${BACKEND_URL}/api/v1/search?${params.toString()}`
      );
      fakeResults = await res.json();
    }
  }
  return fakeResults;
}

export function simpleSearchWS({
  query,
  llmModel,
  topK = 20,
  maxLlmChunks = 20,
  dataset_ids,
  document_ids,
  userEmail,
  embedding_provider,
  onProgress,
  onDone,
  onError,
}) {
  const wsProtocol = window.location.protocol === "https:" ? "wss" : "ws";
  const wsHost = BACKEND_HOST;
  const wsPort = BACKEND_PORT;
  const wsUrl = `${wsProtocol}://${wsHost}:${wsPort}/api/v1/search/ws/search_progress`;
  const ws = new WebSocket(wsUrl);
  ws.onopen = () => {
    const payload = {
      query,
      llm_model: llmModel,
      top_k: topK,
      max_llm_chunks: maxLlmChunks,
      user_email: userEmail,
    };
    if (dataset_ids) payload.dataset_ids = dataset_ids;
    if (document_ids) payload.document_ids = document_ids;
    if (embedding_provider) payload.embedding_provider = embedding_provider;
    ws.send(JSON.stringify(payload));
  };
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.type === "progress") {
      onProgress && onProgress(data);
    } else if (data.type === "done") {
      onDone && onDone(data);
      ws.close();
    } else if (data.type === "error") {
      onError && onError(data.message);
      ws.close();
    }
  };
  ws.onerror = () => {
    onError && onError("Error de conexión WebSocket");
    ws.close();
  };
  return ws;
}

export async function sendFeedback(payload) {
  const res = await fetch(`${BACKEND_URL}/api/v1/search/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  let data;
  try {
    data = await res.json();
  } catch {
    // Si la respuesta no es JSON, devolver el texto plano para debug
    const text = await res.text();
    return { status: "error", detail: `Respuesta no JSON: ${text}` };
  }
  return data;
}

export async function getDocumentsByCollection(kb_id) {
  const res = await fetch(
    `${BACKEND_URL}/api/v1/search/documents_by_collection/${kb_id}`
  );
  return res.json();
}

export async function fetchData({
  url,
  method = "GET",
  body = null,
  headers = {},
  params = null,
}) {
  // Construir la URL con parámetros si se proporcionan
  let finalUrl = BACKEND_URL_V1 + url;

  if (params && typeof params === "object") {
    const queryParams = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (Array.isArray(value)) {
        value.forEach((val) => queryParams.append(key, val));
      } else {
        queryParams.append(key, value);
      }
    });
    finalUrl += `?${queryParams.toString()}`;
  }

  const config = {
    method,
    headers: {
      "Content-Type": "application/json",
      ...headers,
    },
  };

  // Agregar body si el método lo permite
  if (["POST", "PUT", "PATCH"].includes(method.toUpperCase()) && body) {
    config.body = JSON.stringify(body);
  }

  try {
    const response = await fetch(finalUrl, config);
    if (!response.ok) {
      throw new Error(`Error: ${response.status} - ${response.statusText}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Fetch error:", error);
    throw error;
  }
}
