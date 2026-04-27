"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  FileText,
  Cog,
  AlertTriangle,
  Eye,
  TrendingUp,
  Leaf,
  DollarSign,
  BarChart3,
} from "lucide-react";
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

const fadeUp = {
  initial: { opacity: 0, y: 16 },
  animate: { opacity: 1, y: 0 },
};

export default function DashboardView() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [components, setComponents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, []);

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
      let ocrSum = 0, ocrCount = 0, entityCount = 0;
      for (const d of docs) {
        byType[d.file_type] = (byType[d.file_type] || 0) + 1;
        if (d.doc_category) byCategory[d.doc_category] = (byCategory[d.doc_category] || 0) + 1;
        byStatus[d.processing_status] = (byStatus[d.processing_status] || 0) + 1;
        if (d.ocr_confidence != null && d.ocr_confidence > 0) { ocrSum += d.ocr_confidence; ocrCount++; }
        if (d.entity_count) entityCount += d.entity_count;
      }
      setStats({ totalDocs: docs.length, byType, byCategory, byStatus, totalComponents: comps.length, totalEntities: entityCount, flaggedComponents: comps.filter((c: any) => c.is_flagged).length, avgOcrConfidence: ocrCount > 0 ? ocrSum / ocrCount : null });
      setComponents(comps);
    } catch { setStats(null); } finally { setLoading(false); }
  };

  if (loading) {
    return (
      <div className="grid grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="gradient-card h-32 animate-pulse" />
        ))}
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="gradient-card p-12 text-center">
        <p className="text-[#5c5f73]">Could not load dashboard data. Is the backend running?</p>
      </div>
    );
  }

  const statCards = [
    { label: "Documents", value: stats.totalDocs, icon: FileText, color: "from-indigo-500 to-blue-500", shadowColor: "shadow-indigo-500/20" },
    { label: "Components", value: stats.totalComponents, icon: Cog, color: "from-violet-500 to-purple-500", shadowColor: "shadow-violet-500/20" },
    { label: "Flagged", value: stats.flaggedComponents, icon: AlertTriangle, color: stats.flaggedComponents > 0 ? "from-amber-500 to-orange-500" : "from-emerald-500 to-teal-500", shadowColor: stats.flaggedComponents > 0 ? "shadow-amber-500/20" : "shadow-emerald-500/20" },
    { label: "Avg OCR", value: stats.avgOcrConfidence != null ? `${Math.round(stats.avgOcrConfidence * 100)}%` : "N/A", icon: Eye, color: "from-cyan-500 to-blue-500", shadowColor: "shadow-cyan-500/20" },
  ];

  return (
    <div className="space-y-6">
      {/* Stat Cards */}
      <div className="grid grid-cols-4 gap-4">
        {statCards.map((card, i) => {
          const Icon = card.icon;
          return (
            <motion.div
              key={card.label}
              variants={fadeUp}
              initial="initial"
              animate="animate"
              transition={{ duration: 0.4, delay: i * 0.08 }}
              className="gradient-card stat-card-hover p-5"
            >
              <div className="flex items-start justify-between mb-4">
                <div className={`w-10 h-10 rounded-lg bg-gradient-to-br ${card.color} flex items-center justify-center shadow-lg ${card.shadowColor}`}>
                  <Icon className="w-5 h-5 text-white" />
                </div>
              </div>
              <div className="text-3xl font-bold text-white tracking-tight">{card.value}</div>
              <div className="text-xs text-[#5c5f73] mt-1 font-medium">{card.label}</div>
            </motion.div>
          );
        })}
      </div>

      {/* Breakdowns Row */}
      <div className="grid grid-cols-3 gap-4">
        <BreakdownCard title="By Type" data={stats.byType} delay={0.3} />
        <BreakdownCard title="By Category" data={stats.byCategory} delay={0.4} />
        <BreakdownCard title="By Status" data={stats.byStatus} delay={0.5} />
      </div>

      {/* Components Table */}
      {components.length > 0 && (
        <motion.div
          variants={fadeUp} initial="initial" animate="animate"
          transition={{ duration: 0.4, delay: 0.6 }}
          className="gradient-card p-6"
        >
          <div className="flex items-center gap-2 mb-5">
            <Leaf className="w-4 h-4 text-emerald-400" />
            <h4 className="text-xs font-semibold uppercase tracking-wider text-[#5c5f73]">
              Components & Sustainability
            </h4>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-white/[0.06]">
                  {["Component", "Material", "Est. Cost", "CO₂ (kg)", "Confidence", "Status"].map((h) => (
                    <th key={h} className="text-left py-3 px-4 text-[11px] font-semibold uppercase tracking-wider text-[#5c5f73]">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {components.map((c: any, i: number) => (
                  <tr key={i} className="border-b border-white/[0.04] table-row-hover">
                    <td className="py-3 px-4 font-medium text-white">{(c.component_type || "").replace(/_/g, " ")}</td>
                    <td className="py-3 px-4 text-[#9396a5]">{(c.material || "—").replace(/_/g, " ")}</td>
                    <td className="py-3 px-4">
                      {c.estimated_cost_mid != null ? (
                        <span className="flex items-center gap-1 text-emerald-400">
                          <DollarSign className="w-3 h-3" />{Number(c.estimated_cost_mid).toFixed(2)}
                        </span>
                      ) : "—"}
                    </td>
                    <td className="py-3 px-4">
                      {c.carbon_footprint_kg_co2e != null ? (
                        <span className="flex items-center gap-1 text-amber-400">
                          <Leaf className="w-3 h-3" />{Number(c.carbon_footprint_kg_co2e).toFixed(2)}
                        </span>
                      ) : "—"}
                    </td>
                    <td className="py-3 px-4">
                      {c.overall_confidence != null ? (
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 rounded-full bg-white/[0.06] overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all duration-500 ${
                                c.overall_confidence >= 0.7 ? "bg-emerald-400" : c.overall_confidence >= 0.4 ? "bg-amber-400" : "bg-red-400"
                              }`}
                              style={{ width: `${c.overall_confidence * 100}%` }}
                            />
                          </div>
                          <span className="text-xs text-[#5c5f73]">{Math.round(c.overall_confidence * 100)}%</span>
                        </div>
                      ) : "—"}
                    </td>
                    <td className="py-3 px-4">
                      {c.is_flagged ? (
                        <span className="badge-status bg-amber-500/10 text-amber-400 border border-amber-500/20">Flagged</span>
                      ) : (
                        <span className="badge-status bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">OK</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </motion.div>
      )}
    </div>
  );
}

function BreakdownCard({ title, data, delay }: { title: string; data: Record<string, number>; delay: number }) {
  const entries = Object.entries(data);
  const total = entries.reduce((s, [, v]) => s + v, 0);
  return (
    <motion.div
      variants={fadeUp} initial="initial" animate="animate"
      transition={{ duration: 0.4, delay }}
      className="gradient-card p-5"
    >
      <div className="flex items-center gap-2 mb-4">
        <BarChart3 className="w-3.5 h-3.5 text-indigo-400" />
        <h4 className="text-xs font-semibold uppercase tracking-wider text-[#5c5f73]">{title}</h4>
      </div>
      {entries.length === 0 ? (
        <p className="text-sm text-[#5c5f73]">No data yet</p>
      ) : (
        <div className="space-y-3">
          {entries.map(([k, v]) => (
            <div key={k}>
              <div className="flex justify-between text-sm mb-1.5">
                <span className="text-[#9396a5]">{k.replace(/_/g, " ")}</span>
                <span className="font-semibold text-white">{v}</span>
              </div>
              <div className="h-1 rounded-full bg-white/[0.06] overflow-hidden">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: total > 0 ? `${(v / total) * 100}%` : "0%" }}
                  transition={{ duration: 0.8, delay: delay + 0.2 }}
                  className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-purple-500"
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </motion.div>
  );
}
