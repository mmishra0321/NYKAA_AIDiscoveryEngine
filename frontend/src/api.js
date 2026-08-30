const API = import.meta.env.VITE_API_BASE_URL || "";

async function request(path, options = {}) {
  const response = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || response.statusText);
  }
  return response;
}

export async function getCatalog() {
  const res = await request("/api/v1/catalog");
  return res.json();
}

export async function getPipeline() {
  const res = await request("/api/v1/pipeline/summary");
  return res.json();
}

export async function getThemes() {
  const res = await request("/api/v1/themes");
  return res.json();
}

export async function askQuestion(question) {
  const res = await request("/api/v1/ask", {
    method: "POST",
    body: JSON.stringify({ question }),
  });
  return res.json();
}

export async function exportCatalog(format) {
  const res = await request("/api/v1/export", {
    method: "POST",
    body: JSON.stringify({ format }),
  });
  const blob = await res.blob();
  const name =
    format === "json" ? "nykaa-wishlist-catalog.json" : "nykaa-wishlist-catalog.md";
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = name;
  a.click();
  URL.revokeObjectURL(url);
}

export function qLabel(id) {
  const match = String(id).match(/^q(\d+)/);
  return match ? `Q${match[1]}` : id;
}
