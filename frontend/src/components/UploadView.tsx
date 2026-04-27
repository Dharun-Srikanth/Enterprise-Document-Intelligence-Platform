"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  CloudUpload,
  FileText,
  FileImage,
  FileType,
  CheckCircle2,
  XCircle,
  Loader2,
  Clock,
  Eye,
} from "lucide-react";
import { api } from "@/lib/api";

interface UploadedFile {
  id: string;
  filename: string;
  file_type: string;
  status: string;
  doc_category?: string | null;
  ocr_confidence?: number | null;
  error?: string;
}

export default function UploadView() {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    const pending = files.filter((f) => f.status === "pending" || f.status === "processing");
    if (pending.length === 0) { if (pollRef.current) clearInterval(pollRef.current); return; }
    pollRef.current = setInterval(async () => {
      const updates = await Promise.allSettled(pending.map((f) => api.getUploadStatus(f.id)));
      setFiles((prev) =>
        prev.map((f) => {
          const idx = pending.findIndex((p) => p.id === f.id);
          if (idx === -1) return f;
          const r = updates[idx];
          if (r.status === "fulfilled") {
            return { ...f, status: r.value.status, file_type: r.value.file_type || f.file_type, doc_category: r.value.doc_category, ocr_confidence: r.value.ocr_confidence, error: r.value.error || undefined };
          }
          return f;
        })
      );
    }, 3000);
    return () => { if (pollRef.current) clearInterval(pollRef.current); };
  }, [files]);

  const handleFiles = useCallback(async (fileList: FileList | File[]) => {
    const arr = Array.from(fileList);
    if (arr.length === 0) return;
    setUploading(true);
    try {
      const result = await api.uploadFiles(arr);
      setFiles((prev) => [
        ...result.files.map((f: any) => ({
          id: f.id, filename: f.filename, file_type: f.file_type,
          status: f.status || "pending", doc_category: f.doc_category,
          ocr_confidence: f.ocr_confidence, error: f.error,
        })),
        ...prev,
      ]);
    } catch (err: any) { console.error("Upload failed:", err); }
    finally { setUploading(false); }
  }, []);

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault(); setIsDragging(false); handleFiles(e.dataTransfer.files);
  }, [handleFiles]);

  const getFileIcon = (type: string) => {
    if (type === "component_photo") return FileImage;
    if (type === "scanned_doc") return FileType;
    return FileText;
  };

  const statusConfig: Record<string, { icon: React.ElementType; color: string; bg: string; border: string }> = {
    completed: { icon: CheckCircle2, color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/20" },
    processing: { icon: Loader2, color: "text-indigo-400", bg: "bg-indigo-500/10", border: "border-indigo-500/20" },
    failed: { icon: XCircle, color: "text-red-400", bg: "bg-red-500/10", border: "border-red-500/20" },
    pending: { icon: Clock, color: "text-[#5c5f73]", bg: "bg-white/[0.03]", border: "border-white/[0.06]" },
  };

  const typeConfig: Record<string, { label: string; color: string; bg: string; border: string }> = {
    digital_doc: { label: "Digital", color: "text-blue-400", bg: "bg-blue-500/10", border: "border-blue-500/20" },
    scanned_doc: { label: "Scanned", color: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/20" },
    component_photo: { label: "Component", color: "text-emerald-400", bg: "bg-emerald-500/10", border: "border-emerald-500/20" },
  };

  return (
    <div className="space-y-6">
      {/* Upload Zone */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4 }}
      >
        <div
          className={`upload-zone group ${isDragging ? "dragging" : ""}`}
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={onDrop}
          onClick={() => inputRef.current?.click()}
        >
          <input
            ref={inputRef} type="file" multiple className="hidden"
            onChange={(e) => e.target.files && handleFiles(e.target.files)}
            accept=".pdf,.txt,.doc,.docx,.png,.jpg,.jpeg"
          />
          {uploading ? (
            <div className="flex flex-col items-center">
              <Loader2 className="w-10 h-10 text-indigo-400 animate-spin mb-3" />
              <p className="text-sm text-[#9396a5]">Uploading files...</p>
            </div>
          ) : (
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center mb-4 group-hover:bg-indigo-500/15 transition-colors">
                <CloudUpload className="w-8 h-8 text-indigo-400" />
              </div>
              <p className="text-base font-medium text-white mb-1.5">
                Drop files here, or <span className="text-indigo-400">browse</span>
              </p>
              <p className="text-xs text-[#5c5f73]">
                PDF, TXT, DOCX, PNG, JPEG — digital docs, scanned docs, and tear-down photos
              </p>
            </div>
          )}
        </div>
      </motion.div>

      {/* Uploaded Files */}
      <AnimatePresence>
        {files.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-3"
          >
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-[#5c5f73]">
                Uploaded Files ({files.length})
              </h3>
            </div>

            {files.map((f, i) => {
              const FileIcon = getFileIcon(f.file_type);
              const sc = statusConfig[f.status] || statusConfig.pending;
              const StatusIcon = sc.icon;
              const tc = typeConfig[f.file_type];

              return (
                <motion.div
                  key={f.id}
                  initial={{ opacity: 0, x: -12 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: i * 0.05 }}
                  className="gradient-card p-4"
                >
                  <div className="flex items-center gap-4">
                    {/* File icon */}
                    <div className="w-10 h-10 rounded-lg bg-white/[0.04] border border-white/[0.06] flex items-center justify-center flex-shrink-0">
                      <FileIcon className="w-5 h-5 text-[#5c5f73]" />
                    </div>

                    {/* File info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2.5">
                        <span className="text-sm font-medium text-white truncate">{f.filename}</span>
                        {f.status === "processing" && (
                          <Loader2 className="w-3.5 h-3.5 text-indigo-400 animate-spin flex-shrink-0" />
                        )}
                      </div>
                      <div className="flex items-center gap-2 mt-1.5">
                        {tc && (
                          <span className={`badge-status ${tc.bg} ${tc.color} border ${tc.border}`}>
                            {tc.label}
                          </span>
                        )}
                        <span className={`badge-status ${sc.bg} ${sc.color} border ${sc.border}`}>
                          <StatusIcon className="w-3 h-3" />
                          {f.status}
                        </span>
                        {f.doc_category && (
                          <span className="badge-status bg-purple-500/10 text-purple-400 border border-purple-500/20">
                            {f.doc_category}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* OCR Confidence */}
                    {f.ocr_confidence != null && f.ocr_confidence > 0 && (
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <Eye className="w-3.5 h-3.5 text-[#5c5f73]" />
                        <div className="w-20">
                          <div className="flex justify-between text-[10px] text-[#5c5f73] mb-1">
                            <span>OCR</span>
                            <span>{Math.round(f.ocr_confidence * 100)}%</span>
                          </div>
                          <div className="h-1 rounded-full bg-white/[0.06] overflow-hidden">
                            <div
                              className={`h-full rounded-full transition-all duration-700 ${
                                f.ocr_confidence >= 0.7 ? "bg-emerald-400" : f.ocr_confidence >= 0.4 ? "bg-amber-400" : "bg-red-400"
                              }`}
                              style={{ width: `${f.ocr_confidence * 100}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    )}

                    {f.error && (
                      <span className="text-xs text-red-400 flex-shrink-0">{f.error}</span>
                    )}
                  </div>
                </motion.div>
              );
            })}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
