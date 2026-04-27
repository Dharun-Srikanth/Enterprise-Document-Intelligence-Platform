"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Send,
  BrainCircuit,
  Sparkles,
  FileText,
  AlertCircle,
  Loader2,
  BookOpen,
  Gauge,
} from "lucide-react";
import { api } from "@/lib/api";

export default function AnalyticalQueryView() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<{
    answer: string | null; sources: any[] | null;
    confidence: number | null; error: string | null;
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
    setLoading(true); setResult(null);
    try { setResult(await api.analyticalQuery(query)); }
    catch (err: any) { setResult({ answer: null, sources: null, confidence: null, error: err.message }); }
    finally { setLoading(false); }
  };

  const confidenceColor = (c: number) =>
    c >= 0.7 ? "text-emerald-400" : c >= 0.4 ? "text-amber-400" : "text-red-400";
  const confidenceBarColor = (c: number) =>
    c >= 0.7 ? "from-emerald-500 to-emerald-400" : c >= 0.4 ? "from-amber-500 to-amber-400" : "from-red-500 to-red-400";
  const confidenceLabel = (c: number) =>
    c >= 0.8 ? "High confidence" : c >= 0.5 ? "Moderate confidence" : "Low confidence";

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
          <Sparkles className="w-3 h-3 text-purple-400" /> Try:
        </span>
        {examples.map((ex, i) => (
          <button key={i} className="chip" onClick={() => handleSubmit(ex)} disabled={loading}>
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
          <BrainCircuit className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-[#5c5f73]" />
          <input
            className="input-glow pl-11"
            placeholder="Ask an analytical question about your documents..."
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
          />
        </div>
        <button
          onClick={() => handleSubmit()}
          disabled={loading || !question.trim()}
          className="flex items-center gap-2 px-6 py-3 rounded-xl bg-gradient-to-r from-purple-600 to-indigo-500 text-white text-sm font-medium hover:from-purple-500 hover:to-indigo-400 disabled:opacity-40 disabled:cursor-not-allowed transition-all btn-glow flex-shrink-0"
        >
          {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          Analyze
        </button>
      </motion.div>

      {/* Loading */}
      {loading && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="gradient-card p-12 text-center"
        >
          <div className="relative w-16 h-16 mx-auto mb-4">
            <div className="absolute inset-0 rounded-full border-2 border-purple-500/20 border-t-purple-400 animate-spin" />
            <div className="absolute inset-2 rounded-full border-2 border-indigo-500/20 border-b-indigo-400 animate-spin" style={{ animationDirection: "reverse", animationDuration: "1.5s" }} />
            <BrainCircuit className="absolute inset-0 m-auto w-6 h-6 text-purple-400" />
          </div>
          <p className="text-sm text-[#9396a5]">Searching documents and synthesizing answer...</p>
          <p className="text-xs text-[#5c5f73] mt-1">Multi-hop retrieval across your corpus</p>
        </motion.div>
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

            {/* Confidence */}
            {result.confidence != null && (
              <motion.div
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.1 }}
                className="gradient-card p-5"
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <Gauge className="w-3.5 h-3.5 text-indigo-400" />
                    <span className="text-xs font-semibold uppercase tracking-wider text-[#5c5f73]">
                      {confidenceLabel(result.confidence)}
                    </span>
                  </div>
                  <span className={`text-lg font-bold ${confidenceColor(result.confidence)}`}>
                    {Math.round(result.confidence * 100)}%
                  </span>
                </div>
                <div className="h-2 rounded-full bg-white/[0.06] overflow-hidden">
                  <motion.div
                    initial={{ width: 0 }}
                    animate={{ width: `${result.confidence * 100}%` }}
                    transition={{ duration: 0.8, ease: "easeOut" }}
                    className={`h-full rounded-full bg-gradient-to-r ${confidenceBarColor(result.confidence)}`}
                  />
                </div>
              </motion.div>
            )}

            {/* Answer */}
            {result.answer && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
                className="gradient-card p-6"
              >
                <div className="flex items-center gap-2 mb-4">
                  <BookOpen className="w-3.5 h-3.5 text-purple-400" />
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-[#5c5f73]">Answer</h4>
                </div>
                <div className="text-sm leading-7 text-[#c8cad5] whitespace-pre-wrap">
                  {result.answer}
                </div>
              </motion.div>
            )}

            {/* Sources */}
            {result.sources && result.sources.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.3 }}
                className="gradient-card p-6"
              >
                <div className="flex items-center gap-2 mb-4">
                  <FileText className="w-3.5 h-3.5 text-indigo-400" />
                  <h4 className="text-xs font-semibold uppercase tracking-wider text-[#5c5f73]">
                    Sources ({result.sources.length})
                  </h4>
                </div>
                <div className="space-y-3">
                  {result.sources.map((src: any, i: number) => (
                    <div key={i} className="source-item py-3 px-4 rounded-r-lg">
                      <div className="flex items-start gap-3">
                        <span className="flex-shrink-0 w-6 h-6 rounded-md bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-xs font-bold text-indigo-400">
                          {i + 1}
                        </span>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className="text-sm font-medium text-white">
                              {src.filename || "Unknown source"}
                            </span>
                            {src.section && (
                              <span className="text-xs text-[#5c5f73]">— {src.section}</span>
                            )}
                          </div>
                          {src.preview && (
                            <p className="text-xs text-[#5c5f73] mt-1.5 leading-relaxed line-clamp-2">
                              &ldquo;{src.preview}&rdquo;
                            </p>
                          )}
                          {src.relevance_score != null && (
                            <div className="flex items-center gap-2 mt-2">
                              <div className="w-16 h-1 rounded-full bg-white/[0.06] overflow-hidden">
                                <div
                                  className={`h-full rounded-full bg-gradient-to-r ${confidenceBarColor(src.relevance_score)}`}
                                  style={{ width: `${src.relevance_score * 100}%` }}
                                />
                              </div>
                              <span className="text-[10px] text-[#5c5f73]">
                                {Math.round(src.relevance_score * 100)}% relevance
                              </span>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
