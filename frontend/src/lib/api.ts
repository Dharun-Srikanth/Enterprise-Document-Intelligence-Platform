const API_BASE = process.env.NEXT_PUBLIC_API_URL || "";

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers: {
      ...options?.headers,
    },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  // Health
  health: () => request<{ status: string }>("/api/health"),

  // Upload
  uploadFiles: (files: File[]) => {
    const formData = new FormData();
    files.forEach((f) => formData.append("files", f));
    return request<{ uploaded: number; files: any[] }>("/api/upload", {
      method: "POST",
      body: formData,
    });
  },

  getUploadStatus: (id: string) =>
    request<{
      id: string;
      filename: string;
      file_type: string;
      status: string;
      doc_category: string | null;
      ocr_confidence: number | null;
      error: string | null;
    }>(`/api/upload/status/${id}`),

  // Documents
  listDocuments: () =>
    request<{ total: number; documents: any[] }>("/api/documents"),

  getDocument: (id: string) => request<any>(`/api/documents/${id}`),

  listComponents: () =>
    request<{ total: number; components: any[] }>("/api/components"),

  // Queries
  structuredQuery: (question: string) =>
    request<{
      question: string;
      sql: string | null;
      results: any[] | null;
      assumptions: string[] | null;
      error: string | null;
    }>("/api/query/structured", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    }),

  analyticalQuery: (question: string) =>
    request<{
      question: string;
      answer: string | null;
      sources: any[] | null;
      confidence: number | null;
      error: string | null;
    }>("/api/query/analytical", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    }),
};
