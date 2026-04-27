"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowLeft,
  RefreshCw,
  FileText,
  FileImage,
  FileType,
  Tag,
  Layers,
  Eye,
  ChevronDown,
  ChevronRight,
  Cog,
  DollarSign,
  Leaf,
} from "lucide-react";
import { api } from "@/lib/api";

interface DocSummary {
  id: string; filename: string; file_type: string;
  doc_category: string | null; processing_status: string;
  ocr_confidence: number | null; created_at: string;
}
interface DocDetail {
  id: string; filename: string; file_type: string;
  doc_category: string | null; doc_category_secondary: string | null;
  category_confidence: number | null; clean_text: string | null;
  ocr_confidence: number | null; processing_status: string;
  entities: any[]; components: any[]; chunks: any[]; created_at: string;
}

export default function DocumentsView() {
  const [documents, setDocuments] = useState<DocSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<DocDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  useEffect(() => { loadDocuments(); }, []);

  const loadDocuments = async () => {
    setLoading(true);
    try { const res = await api.listDocuments(); setDocuments(res.documents || []); }
    catch { setDocuments([]); }
    finally { setLoading(false); }
  };

  const selectDoc = async (id: string) => {
    setDetailLoading(true); setSelected(null);
    try { setSelected(await api.getDocument(id)); }
    catch { setSelected(null); }
    finally { setDetailLoading(false); }
  };

  const typeConfig: Record<string, { label: string; color: string; bg: string; border: string; icon: React.ElementType }> = {
    digital_doc: { label: "Digital", color: "text-blue-400", bg: "bg-blue-500/10", border: "border-blue-500/20", icon: FileText },
    scanned_doc: { label: "Scanned", color: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/20", icon: FileType },
    component_photo: { label: "Component", color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/20", icon: FileImage },
  };

  const statusConfig: Record<string, { color: string; bg: string; border: string }> = {
    completed: { color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/20" },
    processing: { color: "text-indigo-400", bg: "bg-indigo-500/10", border: "border-indigo-500/20" },
    failed: { color: "text-red-400", bg: "bg-red-500/10", border: "border-red-500/20" },
    pending: { color: "text-[#5c5f73]", bg: "bg-white/[0.03]", border: "border-white/[0.06]" },
  };

  if (selected) {
    return (
      <AnimatePresence mode="wait">
        <motion.div
          key="detail"
          initial={{ opacity: 0, x: 12 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -12 }}
          transition={{ duration: 0.3 }}
        >
          <button
            onClick={() => setSelected(null)}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-[#9396a5] hover:text-white hover:bg-white/[0.04] transition-all mb-5"
          >
            <ArrowLeft className="w-4 h-4" /> Back to documents
          </button>
          <DocumentDetail doc={selected} typeConfig={typeConfig} statusConfig={statusConfig} />
        </motion.div>
      </AnimatePresence>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-[#5c5f73]">
          All Documents ({documents.length})
        </h3>
        <button
          onClick={loadDocuments}
          className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs text-[#9396a5] hover:text-white hover:bg-white/[0.04] border border-white/[0.06] transition-all"
        >
          <RefreshCw className="w-3 h-3" /> Refresh
        </button>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="gradient-card h-16 animate-pulse" />
          ))}
        </div>
      ) : documents.length === 0 ? (
        <div className="gradient-card p-16 text-center">
          <FileText className="w-10 h-10 text-[#5c5f73] mx-auto mb-3" />
          <p className="text-[#5c5f73]">No documents yet. Upload some files to get started.</p>
        </div>
      ) : (
        <div className="gradient-card overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/[0.06]">
                {["Filename", "Type", "Category", "Status", "OCR", "Uploaded"].map((h) => (
                  <th key={h} className="text-left py-3 px-4 text-[11px] font-semibold uppercase tracking-wider text-[#5c5f73]">{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {documents.map((d, i) => {
                const tc = typeConfig[d.file_type] || typeConfig.digital_doc;
                const sc = statusConfig[d.processing_status] || statusConfig.pending;
                return (
                  <motion.tr
                    key={d.id}
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.03 }}
                    onClick={() => selectDoc(d.id)}
                    className="border-b border-white/[0.04] table-row-hover cursor-pointer group"
                  >
                    <td className="py-3 px-4">
                      <span className="font-medium text-white group-hover:text-indigo-300 transition-colors">{d.filename}</span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`badge-status ${tc.bg} ${tc.color} border ${tc.border}`}>{tc.label}</span>
                    </td>
                    <td className="py-3 px-4">
                      {d.doc_category ? (
                        <span className="badge-status bg-purple-500/10 text-purple-400 border border-purple-500/20">{d.doc_category}</span>
                      ) : <span className="text-[#5c5f73]">—</span>}
                    </td>
                    <td className="py-3 px-4">
                      <span className={`badge-status ${sc.bg} ${sc.color} border ${sc.border}`}>{d.processing_status}</span>
                    </td>
                    <td className="py-3 px-4">
                      {d.ocr_confidence != null ? (
                        <span className="text-xs text-[#9396a5]">{Math.round(d.ocr_confidence * 100)}%</span>
                      ) : <span className="text-[#5c5f73]">—</span>}
                    </td>
                    <td className="py-3 px-4 text-xs text-[#5c5f73]">
                      {d.created_at ? new Date(d.created_at).toLocaleDateString() : "—"}
                    </td>
                  </motion.tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {detailLoading && (
        <div className="gradient-card p-8 text-center">
          <div className="w-6 h-6 border-2 border-indigo-500/30 border-t-indigo-400 rounded-full animate-spin mx-auto" />
          <p className="text-sm text-[#5c5f73] mt-3">Loading document details...</p>
        </div>
      )}
    </div>
  );
}

function DocumentDetail({ doc, typeConfig, statusConfig }: {
  doc: DocDetail;
  typeConfig: Record<string, any>;
  statusConfig: Record<string, any>;
}) {
  const [showText, setShowText] = useState(false);
  const tc = typeConfig[doc.file_type] || typeConfig.digital_doc;
  const sc = statusConfig[doc.processing_status] || statusConfig.pending;

  const entityColors: Record<string, string> = {
    person: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    organization: "bg-violet-500/10 text-violet-400 border-violet-500/20",
    org: "bg-violet-500/10 text-violet-400 border-violet-500/20",
    money: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    date: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    location: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
    gpe: "bg-cyan-500/10 text-cyan-400 border-cyan-500/20",
    percent: "bg-pink-500/10 text-pink-400 border-pink-500/20",
  };

  return (
    <div className="space-y-4">
      {/* Header Card */}
      <div className="gradient-card p-6">
        <div className="flex items-start justify-between">
          <div>
            <h2 className="text-xl font-bold text-white mb-3">{doc.filename}</h2>
            <div className="flex items-center gap-2 flex-wrap">
              <span className={`badge-status ${tc.bg} ${tc.color} border ${tc.border}`}>{tc.label}</span>
              <span className={`badge-status ${sc.bg} ${sc.color} border ${sc.border}`}>{doc.processing_status}</span>
              {doc.doc_category && <span className="badge-status bg-purple-500/10 text-purple-400 border border-purple-500/20">{doc.doc_category}</span>}
              {doc.doc_category_secondary && <span className="badge-status bg-white/[0.03] text-[#5c5f73] border border-white/[0.06]">{doc.doc_category_secondary}</span>}
            </div>
          </div>
          <div className="text-right space-y-1 text-xs text-[#5c5f73]">
            {doc.category_confidence != null && <div>Classification: {Math.round(doc.category_confidence * 100)}%</div>}
            {doc.ocr_confidence != null && doc.ocr_confidence > 0 && <div>OCR: {Math.round(doc.ocr_confidence * 100)}%</div>}
          </div>
        </div>
      </div>

      {/* Entities */}
      {doc.entities && doc.entities.length > 0 && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }} className="gradient-card p-5">
          <div className="flex items-center gap-2 mb-4">
            <Tag className="w-3.5 h-3.5 text-indigo-400" />
            <h4 className="text-xs font-semibold uppercase tracking-wider text-[#5c5f73]">Entities ({doc.entities.length})</h4>
          </div>
          <div className="flex flex-wrap gap-2">
            {doc.entities.map((e: any, i: number) => {
              const ec = entityColors[(e.entity_type || "").toLowerCase()] || "bg-white/[0.03] text-[#9396a5] border-white/[0.06]";
              return (
                <span key={i} className={`badge-status border ${ec}`} title={`${e.entity_type} — ${e.confidence ? Math.round(e.confidence * 100) + '%' : 'N/A'}`}>
                  {e.entity_value || e.value}
                </span>
              );
            })}
          </div>
        </motion.div>
      )}

      {/* Components */}
      {doc.components && doc.components.length > 0 && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.2 }} className="gradient-card p-5">
          <div className="flex items-center gap-2 mb-4">
            <Cog className="w-3.5 h-3.5 text-emerald-400" />
            <h4 className="text-xs font-semibold uppercase tracking-wider text-[#5c5f73]">Components ({doc.components.length})</h4>
          </div>
          <div className="space-y-3">
            {doc.components.map((c: any, i: number) => (
              <div key={i} className="p-4 rounded-lg bg-white/[0.02] border border-white/[0.04]">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-white">{(c.component_type || "").replace(/_/g, " ")}</span>
                    {c.material && <span className="text-sm text-[#5c5f73]">({c.material.replace(/_/g, " ")})</span>}
                  </div>
                  {c.is_flagged && <span className="badge-status bg-amber-500/10 text-amber-400 border border-amber-500/20">Flagged</span>}
                </div>
                <div className="flex gap-6 mt-3 text-sm">
                  {c.estimated_cost_mid != null && <span className="flex items-center gap-1 text-emerald-400"><DollarSign className="w-3 h-3" />{Number(c.estimated_cost_mid).toFixed(2)}</span>}
                  {c.carbon_footprint_kg_co2e != null && <span className="flex items-center gap-1 text-amber-400"><Leaf className="w-3 h-3" />{Number(c.carbon_footprint_kg_co2e).toFixed(2)} kg CO₂</span>}
                  {c.overall_confidence != null && <span className="text-[#5c5f73]">Confidence: {Math.round(c.overall_confidence * 100)}%</span>}
                </div>
              </div>
            ))}
          </div>
        </motion.div>
      )}

      {/* Extracted Text */}
      {doc.clean_text && (
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.3 }} className="gradient-card p-5">
          <button
            onClick={() => setShowText(!showText)}
            className="flex items-center justify-between w-full group"
          >
            <div className="flex items-center gap-2">
              <Layers className="w-3.5 h-3.5 text-indigo-400" />
              <h4 className="text-xs font-semibold uppercase tracking-wider text-[#5c5f73]">
                Extracted Text ({doc.clean_text.length.toLocaleString()} chars)
              </h4>
            </div>
            {showText ? <ChevronDown className="w-4 h-4 text-[#5c5f73]" /> : <ChevronRight className="w-4 h-4 text-[#5c5f73]" />}
          </button>
          <AnimatePresence>
            {showText && (
              <motion.pre
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: "auto", opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.3 }}
                className="mt-4 text-xs leading-relaxed text-[#9396a5] whitespace-pre-wrap max-h-[400px] overflow-auto font-mono bg-white/[0.02] rounded-lg p-4"
              >
                {doc.clean_text}
              </motion.pre>
            )}
          </AnimatePresence>
        </motion.div>
      )}
    </div>
  );
}
