"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Play,
  Code2,
  Table2,
  Lightbulb,
  AlertCircle,
  Loader2,
  Sparkles,
} from "lucide-react";
import { api } from "@/lib/api";

export default function StructuredQueryView() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{
    sql: string | null; results: any[] | null;
    assumptions: string[] | null; error: string | null;
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
    setLoading(true); setResult(null);
    try { setResult(await api.structuredQuery(query)); }
    catch (err: any) { setResult({ sql: null, results: null, assumptions: null, error: err.message }); }
    finally { setLoading(false); }
  };

  return (
    <div className="space-y-6">
      {/* Example Chips */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        className="flex flex-wrap gap-2"
      >
        <span className="flex items-center gap-1.5 text-xs text-[#5c5f73]">
          <Sparkles className="w-3 h-3 text-indigo-400" /> Try:
        </span>
        {examples.map((ex, i) => (
          <button
            key={i}
            className="chip"
            onClick={() => handleSubmit(ex)}
            disabled={loading}
          >
            {ex}
          </button>
        ))}
      </motion.div>

      {/* Input */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, delay: 0.1 }}
        className="flex gap-3"
      >
        <div className="relative flex-1">
          <input
            className="input-glow pr-4"
            placeholder="Ask a data question — generates SQL automatically..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
          />
        </div>
        <button
          onClick={() => handleSubmit()}
          disabled={loading || !question.trim()}
          className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-indigo-500 text-white text-sm font-medium hover:from-indigo-500 hover:to-indigo-400 disabled:opacity-40 disabled:cursor-not-allowed transition-all btn-glow flex-shrink-0"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
          Run Query
        </button>
      </motion.div>

      {/* Loading */}
      {loading && (
        <div className="gradient-card p-10 text-center">
          <div className="w-8 h-8 border-2 border-indigo-500/30 border-t-indigo-400 rounded-full animate-spin mx-auto" />
          <p className="text-sm text-[#5c5f73] mt-4">Generating SQL and executing query...</p>
        </div>
      )}

      {/* Results */}
      <AnimatePresence>
        {result && !loading && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.4 }}
            className="space-y-4"
          >
            {/* Error */}
            {result.error && (
              <div className="gradient-card p-4 border-l-2 border-red-500">
                <div className="flex items-start gap-3">
                  <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                  <p className="text-sm text-red-400">{result.error}</p>
                </div>
              </div>
            )}

            {/* Generated SQL */}
            {result.sql && (
              <div className="gradient-card p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Code2 className="w-3.5 h-3.5 text-indigo-400" />
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-[#5c5f73]">Generated SQL</h4>
                </div>
                <div className="bg-[#0d0e1a] rounded-lg p-4 border border-white/[0.04] overflow-x-auto">
                  <pre className="text-sm font-mono leading-relaxed text-indigo-300 whitespace-pre-wrap">
                    {result.sql}
                  </pre>
                </div>
              </div>
            )}

            {/* Assumptions */}
            {result.assumptions && result.assumptions.length > 0 && (
              <div className="gradient-card p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Lightbulb className="w-3.5 h-3.5 text-amber-400" />
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-[#5c5f73]">Assumptions</h4>
                </div>
                <ul className="space-y-1.5">
                  {result.assumptions.map((a, i) => (
                    <li key={i} className="flex items-start gap-2 text-sm text-[#9396a5]">
                      <span className="text-amber-400/60 mt-1">•</span>
                      {a}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Results Table */}
            {result.results && result.results.length > 0 && (
              <div className="gradient-card p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Table2 className="w-3.5 h-3.5 text-emerald-400" />
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-[#5c5f73]">
                    Results ({result.results.length} rows)
                  </h4>
                </div>
                <div className="overflow-x-auto rounded-lg border border-white/[0.04]">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="bg-white/[0.02]">
                        {Object.keys(result.results[0]).map((key) => (
                          <th key={key} className="text-left py-2.5 px-4 text-[11px] font-semibold uppercase tracking-wider text-[#5c5f73] border-b border-white/[0.04]">
                            {key}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {result.results.map((row, i) => (
                        <tr key={i} className="border-b border-white/[0.03] table-row-hover">
                          {Object.values(row).map((val: any, j) => (
                            <td key={j} className="py-2.5 px-4 text-[#9396a5]">
                              {val?.toString() ?? "—"}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {result.results && result.results.length === 0 && !result.error && (
              <div className="gradient-card p-10 text-center">
                <Table2 className="w-8 h-8 text-[#5c5f73] mx-auto mb-3" />
                <p className="text-sm text-[#5c5f73]">Query executed successfully but returned no results.</p>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
