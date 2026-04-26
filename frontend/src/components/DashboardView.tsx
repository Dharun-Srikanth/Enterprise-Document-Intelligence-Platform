"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";

interface Stats {
  totalDocs: number;
  byType: Record<string, number>;
  byCategory: Record<string, number>;
  byStatus: Record<string, number>;
  totalComponents: number;
  totalEntities: number;
  flaggedComponents: number;
  avgOcrConfidence: number | null;
}

export default function DashboardView() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [components, setComponents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [docsRes, compsRes] = await Promise.all([
        api.listDocuments(),
        api.listComponents(),
      ]);

      const docs = docsRes.documents || [];
      const comps = compsRes.components || [];

      const byType: Record<string, number> = {};
      const byCategory: Record<string, number> = {};
      const byStatus: Record<string, number> = {};
      let ocrSum = 0;
      let ocrCount = 0;
      let entityCount = 0;

      for (const d of docs) {
        byType[d.file_type] = (byType[d.file_type] || 0) + 1;
        if (d.doc_category)
          byCategory[d.doc_category] = (byCategory[d.doc_category] || 0) + 1;
        byStatus[d.processing_status] =
          (byStatus[d.processing_status] || 0) + 1;
        if (d.ocr_confidence != null && d.ocr_confidence > 0) {
          ocrSum += d.ocr_confidence;
          ocrCount++;
        }
        if (d.entity_count) entityCount += d.entity_count;
      }

      setStats({
        totalDocs: docs.length,
        byType,
        byCategory,
        byStatus,
        totalComponents: comps.length,
        totalEntities: entityCount,
        flaggedComponents: comps.filter((c: any) => c.is_flagged).length,
        avgOcrConfidence: ocrCount > 0 ? ocrSum / ocrCount : null,
      });
      setComponents(comps);
    } catch {
      setStats(null);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ textAlign: "center", padding: 48 }}>
        <span className="spinner" style={{ width: 24, height: 24 }} />
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="card" style={{ textAlign: "center", padding: 48 }}>
        <p style={{ color: "var(--muted)" }}>
          Could not load dashboard data. Is the backend running?
        </p>
      </div>
    );
  }

  return (
    <div>
      {/* Top-level stats */}
      <div className="stats-grid">
        <StatCard label="Documents" value={stats.totalDocs} icon="📄" />
        <StatCard label="Components" value={stats.totalComponents} icon="🔩" />
        <StatCard
          label="Flagged"
          value={stats.flaggedComponents}
          icon="⚠️"
          accent={stats.flaggedComponents > 0 ? "var(--warning)" : undefined}
        />
        <StatCard
          label="Avg OCR"
          value={
            stats.avgOcrConfidence != null
              ? `${Math.round(stats.avgOcrConfidence * 100)}%`
              : "N/A"
          }
          icon="👁"
        />
      </div>

      {/* Breakdowns */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16, marginBottom: 16 }}>
        {/* By Type */}
        <div className="card">
          <h4 style={{ fontSize: 12, color: "var(--muted)", marginBottom: 12 }}>
            BY TYPE
          </h4>
          {Object.entries(stats.byType).map(([k, v]) => (
            <div key={k} style={{ display: "flex", justifyContent: "space-between", marginBottom: 6, fontSize: 13 }}>
              <span>{k.replace(/_/g, " ")}</span>
              <span style={{ fontWeight: 600 }}>{v}</span>
            </div>
          ))}
          {Object.keys(stats.byType).length === 0 && (
            <p style={{ color: "var(--muted)", fontSize: 13 }}>No data</p>
          )}
        </div>

        {/* By Category */}
        <div className="card">
          <h4 style={{ fontSize: 12, color: "var(--muted)", marginBottom: 12 }}>
            BY CATEGORY
          </h4>
          {Object.entries(stats.byCategory).map(([k, v]) => (
            <div key={k} style={{ display: "flex", justifyContent: "space-between", marginBottom: 6, fontSize: 13 }}>
              <span>{k}</span>
              <span style={{ fontWeight: 600 }}>{v}</span>
            </div>
          ))}
          {Object.keys(stats.byCategory).length === 0 && (
            <p style={{ color: "var(--muted)", fontSize: 13 }}>No data</p>
          )}
        </div>

        {/* By Status */}
        <div className="card">
          <h4 style={{ fontSize: 12, color: "var(--muted)", marginBottom: 12 }}>
            BY STATUS
          </h4>
          {Object.entries(stats.byStatus).map(([k, v]) => (
            <div key={k} style={{ display: "flex", justifyContent: "space-between", marginBottom: 6, fontSize: 13 }}>
              <span>{k}</span>
              <span style={{ fontWeight: 600 }}>{v}</span>
            </div>
          ))}
          {Object.keys(stats.byStatus).length === 0 && (
            <p style={{ color: "var(--muted)", fontSize: 13 }}>No data</p>
          )}
        </div>
      </div>

      {/* Components table */}
      {components.length > 0 && (
        <div className="card">
          <h4 style={{ fontSize: 12, color: "var(--muted)", marginBottom: 12 }}>
            COMPONENTS OVERVIEW
          </h4>
          <div style={{ overflowX: "auto" }}>
            <table className="results-table">
              <thead>
                <tr>
                  <th>Component</th>
                  <th>Material</th>
                  <th>Est. Cost</th>
                  <th>CO₂ (kg)</th>
                  <th>Confidence</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {components.map((c: any, i: number) => (
                  <tr key={i}>
                    <td>{(c.component_type || "").replace(/_/g, " ")}</td>
                    <td>{(c.material || "—").replace(/_/g, " ")}</td>
                    <td>
                      {c.estimated_cost_mid != null
                        ? `$${Number(c.estimated_cost_mid).toFixed(2)}`
                        : "—"}
                    </td>
                    <td>
                      {c.carbon_footprint_kg_co2e != null
                        ? Number(c.carbon_footprint_kg_co2e).toFixed(2)
                        : "—"}
                    </td>
                    <td>
                      {c.overall_confidence != null
                        ? `${Math.round(c.overall_confidence * 100)}%`
                        : "—"}
                    </td>
                    <td>
                      {c.is_flagged ? (
                        <span className="badge badge-failed">⚠ Flagged</span>
                      ) : (
                        <span className="badge badge-completed">OK</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  icon,
  accent,
}: {
  label: string;
  value: string | number;
  icon: string;
  accent?: string;
}) {
  return (
    <div className="card stat-card">
      <div style={{ fontSize: 24, marginBottom: 4 }}>{icon}</div>
      <div
        style={{
          fontSize: 28,
          fontWeight: 700,
          color: accent || "var(--fg)",
        }}
      >
        {value}
      </div>
      <div style={{ fontSize: 12, color: "var(--muted)", marginTop: 2 }}>
        {label}
      </div>
    </div>
  );
}
