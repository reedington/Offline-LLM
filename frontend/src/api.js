export async function getHealth() {
  return request("/health");
}

export async function getMetrics() {
  return request("/metrics");
}

export async function getDocuments() {
  return request("/documents");
}

export async function uploadDocuments({ files, useSamples }) {
  const formData = new FormData();
  formData.append("use_samples", useSamples ? "true" : "false");
  for (const file of files) {
    formData.append("files", file);
  }
  return request("/upload", { method: "POST", body: formData });
}

export async function askQuestion({ question, topK }) {
  return request("/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question, top_k: topK }),
  });
}

async function request(url, options) {
  const response = await fetch(url, options);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Request failed.");
  }
  return data;
}
