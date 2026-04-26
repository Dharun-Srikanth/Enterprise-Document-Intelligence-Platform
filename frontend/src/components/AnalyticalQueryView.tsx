"use client";

import { useState } from "react";
import { api } from "@/lib/api";

export default function AnalyticalQueryView() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{
    answer: string | null;
    sources: any[] | null;
    confidence: number | null;
    error: string | null;
  } | null>(null);

  const examples = [
    "Which cost-saving ideas also reduce carbon footprint?",
    "What decisions were made in Sprint 8?",
    "Summarize the Q3 2025 financial performance",
    "Who is responsible for the seat track assembly project?",
  ];

  const handleSubmit = async (q?: string) => {
    const query = q || question;
    if (!query.trim()) return;
    if (q) setQuestion(q);
    setLoading(true);
    setResult(null);
    try {
      const res = await api.analyticalQuery(query);
      setResult(res);
    } catch (err: any) {
      setResult({
        answer: null,
        sources: null,
        confidence: null,
        error: err.message,
      });
    } finally {
      setLoading(false);
    }
  };

  const confidenceColor = (c: number) =>
    c >= 0.7
      ? "confidence-high"
      : c >= 0.4
      ? "confidence-mid"
      : "confidence-low";

  const confidenceLabel = (c: number) =>
    c >= 0.8
      ? "High confidence"
      : c >= 0.5
      ? "Moderate confidence"
      : "Low confidence";

  return (
    <div>
      {/* Example queries */}
      <div style={{ marginBottom: 16 }}>
        <span style={{ fontSize: 12, color: "var(--muted)" }}>Try: </span>
        {examples.map((ex, i) => (
          <button
            key={i}
            className="example-chip"
            onClick={() => handleSubmit(ex)}
            disabled={loading}
          >
            {ex}
          </button>
        ))}
      </div>

      {/* Input */}
      <div style={{ display: "flex", gap: 12, marginBottom: 24 }}>
        <input
          className="text-input"
          placeholder="Ask an analytical question about your documents..."
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
        />
        <button
          className="btn btn-primary"
          onClick={() => handleSubmit()}
          disabled={loading || !question.trim()}
          style={{ whiteSpace: "nowrap" }}
        >
          {loading ? <span className="spinner" /> : "Analyze"}
        </button>
      </div>

      {loading && (
        <div className="card" style={{ textAlign: "center", padding: 32 }}>
          <span className="spinner" style={{ width: 24, height: 24 }} />
          <p style={{ color: "var(--muted)", marginTop: 12, fontSize: 13 }}>
            Searching documents and synthesizing answer...
          </p>
        </div>
      )}

      {result && !loading && (
        <div>
          {result.error && (
            <div className="card" style={{ borderColor: "var(--error)" }}>
              <p style={{ color: "var(--error)", fontSize: 13 }}>
                ⚠ {result.error}
              </p>
            </div>
          )}

          {/* Confidence bar */}
          {result.confidence != null && (
            <div style={{ marginBottom: 16 }}>
              <div
                style={{
                  display: "flex",
                  justifyContent: "space-between",
                  fontSize: 12,
                  marginBottom: 4,
                }}
              >
                <span style={{ color: "var(--muted)" }}>
                  {confidenceLabel(result.confidence)}
                </span>
                <span>{Math.round(result.confidence * 100)}%</span>
              </div>
              <div className="confidence-bar">
                <div
                  className={`confidence-fill ${confidenceColor(result.confidence)}`}
                  style={{ width: `${result.confidence * 100}%` }}
                />
              </div>
            </div>
          )}

          {/* Answer */}
          {result.answer && (
            <div className="card">
              <h4
                style={{
                  fontSize: 12,
                  color: "var(--muted)",
                  marginBottom: 12,
                }}
              >
                ANSWER
              </h4>
              <div
                style={{ fontSize: 14, lineHeight: 1.7, whiteSpace: "pre-wrap" }}
              >
                {result.answer}
              </div>
            </div>
          )}

          {/* Sources — using backend fields: filename, section, preview, relevance_score */}
          {result.sources && result.sources.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <h4
                style={{
                  fontSize: 12,
                  color: "var(--muted)",
                  marginBottom: 8,
                }}
              >
                SOURCES ({result.sources.length})
              </h4>
              {result.sources.map((src: any, i: number) => (
                <div className="source-ref" key={i}>
                  <span
                    style={{ color: "var(--accent)", fontWeight: 600, flexShrink: 0 }}
                  >
                    [{i + 1}]
                  </span>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontWeight: 500, fontSize: 13 }}>
                      {src.filename || "Unknown source"}
                      {src.section && (
                        <span style={{ color: "var(--muted)", fontWeight: 400 }}>
                          {" "}
                          — {src.section}
                        </span>
                      )}
                    </div>
                    {src.preview && (
                      <div
                        style={{
                          fontSize: 12,
                          color: "var(--muted)",
                          marginTop: 4,
                          lineHeight: 1.5,
                          overflow: "hidden",
                          textOverflow: "ellipsis",
                          display: "-webkit-box",
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: "vertical",
                        }}
                      >
                        &ldquo;{src.preview}&rdquo;
                      </div>
                    )}
                    {src.relevance_score != null && (
                      <div style={{ marginTop: 4, maxWidth: 120 }}>
                        <div className="confidence-bar" style={{ height: 3 }}>
                          <div
                            className={`confidence-fill ${confidenceColor(src.relevance_score)}`}
                            style={{
                              width: `${src.relevance_score * 100}%`,
                            }}
                          />
                        </div>
                        <span
                          style={{ fontSize: 10, color: "var(--muted)" }}
                        >
                          {Math.round(src.relevance_score * 100)}% relevance
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
