"use client";

import { useState } from "react";
import { api } from "@/lib/api";

export default function StructuredQueryView() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{
    sql: string | null;
    results: any[] | null;
    assumptions: string[] | null;
    error: string | null;
  } | null>(null);

  const examples = [
    "Total component cost for the seat track assembly?",
    "List all people mentioned across documents",
    "Which components have the highest carbon footprint?",
    "Show all documents classified as financial reports",
    "Compare material costs across all components",
  ];

  const handleSubmit = async (q?: string) => {
    const query = q || question;
    if (!query.trim()) return;
    if (q) setQuestion(q);
    setLoading(true);
    setResult(null);
    try {
      const res = await api.structuredQuery(query);
      setResult(res);
    } catch (err: any) {
      setResult({
        sql: null,
        results: null,
        assumptions: null,
        error: err.message,
      });
    } finally {
      setLoading(false);
    }
  };

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
          placeholder="Ask a structured data question (generates SQL)..."
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
          {loading ? <span className="spinner" /> : "Run Query"}
        </button>
      </div>

      {loading && (
        <div className="card" style={{ textAlign: "center", padding: 32 }}>
          <span className="spinner" style={{ width: 24, height: 24 }} />
          <p style={{ color: "var(--muted)", marginTop: 12, fontSize: 13 }}>
            Generating SQL and executing query...
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

          {result.sql && (
            <div style={{ marginBottom: 16 }}>
              <h4
                style={{
                  fontSize: 12,
                  color: "var(--muted)",
                  marginBottom: 8,
                }}
              >
                GENERATED SQL
              </h4>
              <div className="sql-display">{result.sql}</div>
            </div>
          )}

          {result.assumptions && result.assumptions.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <h4
                style={{
                  fontSize: 12,
                  color: "var(--muted)",
                  marginBottom: 8,
                }}
              >
                ASSUMPTIONS
              </h4>
              <ul
                style={{
                  paddingLeft: 20,
                  fontSize: 13,
                  color: "var(--muted)",
                }}
              >
                {result.assumptions.map((a, i) => (
                  <li key={i} style={{ marginBottom: 4 }}>
                    {a}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {result.results && result.results.length > 0 && (
            <div>
              <h4
                style={{
                  fontSize: 12,
                  color: "var(--muted)",
                  marginBottom: 8,
                }}
              >
                RESULTS ({result.results.length} rows)
              </h4>
              <div style={{ overflowX: "auto" }}>
                <table className="results-table">
                  <thead>
                    <tr>
                      {Object.keys(result.results[0]).map((key) => (
                        <th key={key}>{key}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {result.results.map((row, i) => (
                      <tr key={i}>
                        {Object.values(row).map((val: any, j) => (
                          <td key={j}>{val?.toString() ?? "—"}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {result.results && result.results.length === 0 && !result.error && (
            <div className="card" style={{ textAlign: "center", padding: 24 }}>
              <p style={{ color: "var(--muted)" }}>
                Query executed successfully but returned no results.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
