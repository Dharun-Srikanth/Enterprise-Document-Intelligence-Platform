"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";

interface DocSummary {
  id: string;
  filename: string;
  file_type: string;
  doc_category: string | null;
  processing_status: string;
  ocr_confidence: number | null;
  created_at: string;
}

interface DocDetail {
  id: string;
  filename: string;
  file_type: string;
  doc_category: string | null;
  doc_category_secondary: string | null;
  category_confidence: number | null;
  clean_text: string | null;
  ocr_confidence: number | null;
  processing_status: string;
  entities: any[];
  components: any[];
  chunks: any[];
  created_at: string;
}

export default function DocumentsView() {
  const [documents, setDocuments] = useState<DocSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<DocDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => {
    loadDocuments();
  }, []);

  const loadDocuments = async () => {
    setLoading(true);
    try {
      const res = await api.listDocuments();
      setDocuments(res.documents || []);
    } catch {
      setDocuments([]);
    } finally {
      setLoading(false);
    }
  };

  const selectDoc = async (id: string) => {
    setDetailLoading(true);
    setSelected(null);
    try {
      const doc = await api.getDocument(id);
      setSelected(doc);
    } catch {
      setSelected(null);
    } finally {
      setDetailLoading(false);
    }
  };

  const typeBadge = (type: string) => {
    const map: Record<string, { cls: string; label: string }> = {
      digital_doc: { cls: "badge-digital", label: "Digital" },
      scanned_doc: { cls: "badge-scanned", label: "Scanned" },
      component_photo: { cls: "badge-photo", label: "Component" },
    };
    const b = map[type] || { cls: "badge-pending", label: type };
    return <span className={`badge ${b.cls}`}>{b.label}</span>;
  };

  const statusBadge = (s: string) => {
    const cls =
      s === "completed"
        ? "badge-completed"
        : s === "processing"
        ? "badge-processing"
        : s === "failed"
        ? "badge-failed"
        : "badge-pending";
    return <span className={`badge ${cls}`}>{s}</span>;
  };

  if (selected) {
    return (
      <div>
        <button
          className="btn"
          onClick={() => setSelected(null)}
          style={{
            background: "var(--card-bg)",
            border: "1px solid var(--border)",
            color: "var(--fg)",
            marginBottom: 16,
          }}
        >
          ← Back to documents
        </button>
        <DocumentDetail doc={selected} typeBadge={typeBadge} statusBadge={statusBadge} />
      </div>
    );
  }

  return (
    <div>
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: 16,
        }}
      >
        <h3 style={{ fontSize: 14, color: "var(--muted)" }}>
          ALL DOCUMENTS ({documents.length})
        </h3>
        <button
          className="btn"
          onClick={loadDocuments}
          style={{
            background: "var(--card-bg)",
            border: "1px solid var(--border)",
            color: "var(--fg)",
            fontSize: 13,
          }}
        >
          ↻ Refresh
        </button>
      </div>

      {loading ? (
        <div style={{ textAlign: "center", padding: 48 }}>
          <span className="spinner" style={{ width: 24, height: 24 }} />
        </div>
      ) : documents.length === 0 ? (
        <div className="card" style={{ textAlign: "center", padding: 48 }}>
          <p style={{ color: "var(--muted)" }}>
            No documents yet. Upload some files to get started.
          </p>
        </div>
      ) : (
        <div style={{ overflowX: "auto" }}>
          <table className="results-table">
            <thead>
              <tr>
                <th>Filename</th>
                <th>Type</th>
                <th>Category</th>
                <th>Status</th>
                <th>OCR</th>
                <th>Uploaded</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((d) => (
                <tr
                  key={d.id}
                  onClick={() => selectDoc(d.id)}
                  style={{ cursor: "pointer" }}
                  className="doc-row"
                >
                  <td style={{ fontWeight: 500 }}>{d.filename}</td>
                  <td>{typeBadge(d.file_type)}</td>
                  <td>
                    {d.doc_category ? (
                      <span className="badge badge-category">
                        {d.doc_category}
                      </span>
                    ) : (
                      "—"
                    )}
                  </td>
                  <td>{statusBadge(d.processing_status)}</td>
                  <td>
                    {d.ocr_confidence != null
                      ? `${Math.round(d.ocr_confidence * 100)}%`
                      : "—"}
                  </td>
                  <td style={{ fontSize: 12, color: "var(--muted)" }}>
                    {d.created_at
                      ? new Date(d.created_at).toLocaleDateString()
                      : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {detailLoading && (
        <div className="card" style={{ textAlign: "center", padding: 32 }}>
          <span className="spinner" style={{ width: 24, height: 24 }} />
          <p style={{ color: "var(--muted)", marginTop: 8, fontSize: 13 }}>
            Loading document details...
          </p>
        </div>
      )}
    </div>
  );
}

function DocumentDetail({
  doc,
  typeBadge,
  statusBadge,
}: {
  doc: DocDetail;
  typeBadge: (t: string) => JSX.Element;
  statusBadge: (s: string) => JSX.Element;
}) {
  const [showText, setShowText] = useState(false);

  return (
    <div>
      {/* Header */}
      <div className="card">
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "flex-start",
          }}
        >
          <div>
            <h2 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>
              {doc.filename}
            </h2>
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              {typeBadge(doc.file_type)}
              {statusBadge(doc.processing_status)}
              {doc.doc_category && (
                <span className="badge badge-category">{doc.doc_category}</span>
              )}
              {doc.doc_category_secondary && (
                <span className="badge badge-pending">
                  {doc.doc_category_secondary}
                </span>
              )}
            </div>
          </div>
          <div style={{ textAlign: "right", fontSize: 12, color: "var(--muted)" }}>
            {doc.category_confidence != null && (
              <div>
                Classification: {Math.round(doc.category_confidence * 100)}%
              </div>
            )}
            {doc.ocr_confidence != null && doc.ocr_confidence > 0 && (
              <div>OCR: {Math.round(doc.ocr_confidence * 100)}%</div>
            )}
          </div>
        </div>
      </div>

      {/* Entities */}
      {doc.entities && doc.entities.length > 0 && (
        <div className="card">
          <h4
            style={{ fontSize: 12, color: "var(--muted)", marginBottom: 12 }}
          >
            ENTITIES ({doc.entities.length})
          </h4>
          <div
            style={{ display: "flex", flexWrap: "wrap", gap: 6 }}
          >
            {doc.entities.map((e: any, i: number) => (
              <span
                key={i}
                className={`badge badge-entity-${(e.entity_type || "").toLowerCase()}`}
                title={`${e.entity_type} — confidence: ${
                  e.confidence ? Math.round(e.confidence * 100) + "%" : "N/A"
                }`}
              >
                {e.entity_value || e.value}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Components */}
      {doc.components && doc.components.length > 0 && (
        <div className="card">
          <h4
            style={{ fontSize: 12, color: "var(--muted)", marginBottom: 12 }}
          >
            COMPONENTS ({doc.components.length})
          </h4>
          {doc.components.map((c: any, i: number) => (
            <div
              key={i}
              style={{
                padding: 12,
                background: "var(--bg)",
                borderRadius: 6,
                marginBottom: 8,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between" }}>
                <div>
                  <span style={{ fontWeight: 600 }}>
                    {(c.component_type || "").replace(/_/g, " ")}
                  </span>
                  {c.material && (
                    <span style={{ color: "var(--muted)", marginLeft: 8 }}>
                      ({c.material.replace(/_/g, " ")})
                    </span>
                  )}
                </div>
                {c.is_flagged && (
                  <span className="badge badge-failed">⚠ Flagged</span>
                )}
              </div>
              <div
                style={{
                  display: "flex",
                  gap: 24,
                  marginTop: 8,
                  fontSize: 13,
                  color: "var(--muted)",
                }}
              >
                {c.estimated_cost_mid != null && (
                  <span>
                    Cost: ${Number(c.estimated_cost_mid).toFixed(2)}
                  </span>
                )}
                {c.carbon_footprint_kg_co2e != null && (
                  <span>
                    CO₂: {Number(c.carbon_footprint_kg_co2e).toFixed(2)} kg
                  </span>
                )}
                {c.overall_confidence != null && (
                  <span>
                    Confidence: {Math.round(c.overall_confidence * 100)}%
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Extracted text */}
      {doc.clean_text && (
        <div className="card">
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: showText ? 12 : 0,
            }}
          >
            <h4 style={{ fontSize: 12, color: "var(--muted)" }}>
              EXTRACTED TEXT ({doc.clean_text.length.toLocaleString()} chars)
            </h4>
            <button
              className="btn"
              onClick={() => setShowText(!showText)}
              style={{
                background: "none",
                border: "1px solid var(--border)",
                color: "var(--muted)",
                fontSize: 12,
                padding: "4px 12px",
              }}
            >
              {showText ? "Hide" : "Show"}
            </button>
          </div>
          {showText && (
            <pre
              style={{
                fontSize: 12,
                lineHeight: 1.6,
                color: "var(--muted)",
                whiteSpace: "pre-wrap",
                maxHeight: 400,
                overflow: "auto",
              }}
            >
              {doc.clean_text}
            </pre>
          )}
        </div>
      )}
    </div>
  );
}
