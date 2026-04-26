"use client";

import { useState, useRef, useCallback, useEffect } from "react";
import { api } from "@/lib/api";

interface UploadedFile {
  id: string;
  filename: string;
  file_type: string;
  status: string;
  doc_category?: string | null;
  ocr_confidence?: number | null;
  category_confidence?: number | null;
  error?: string;
}

export default function UploadView() {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Poll for status updates on pending/processing files
  useEffect(() => {
    const pending = files.filter(
      (f) => f.status === "pending" || f.status === "processing"
    );
    if (pending.length === 0) {
      if (pollRef.current) clearInterval(pollRef.current);
      return;
    }

    pollRef.current = setInterval(async () => {
      const updates = await Promise.allSettled(
        pending.map((f) => api.getUploadStatus(f.id))
      );
      setFiles((prev) =>
        prev.map((f) => {
          const idx = pending.findIndex((p) => p.id === f.id);
          if (idx === -1) return f;
          const r = updates[idx];
          if (r.status === "fulfilled") {
            return {
              ...f,
              status: r.value.status,
              file_type: r.value.file_type || f.file_type,
              doc_category: r.value.doc_category,
              ocr_confidence: r.value.ocr_confidence,
              error: r.value.error || undefined,
            };
          }
          return f;
        })
      );
    }, 3000);

    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [files]);

  const handleFiles = useCallback(async (fileList: FileList | File[]) => {
    const arr = Array.from(fileList);
    if (arr.length === 0) return;

    setUploading(true);
    try {
      const result = await api.uploadFiles(arr);
      setFiles((prev) => [
        ...result.files.map((f: any) => ({
          id: f.id,
          filename: f.filename,
          file_type: f.file_type,
          status: f.status || "pending",
          doc_category: f.doc_category,
          ocr_confidence: f.ocr_confidence,
          error: f.error,
        })),
        ...prev,
      ]);
    } catch (err: any) {
      console.error("Upload failed:", err);
    } finally {
      setUploading(false);
    }
  }, []);

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles]
  );

  const typeBadge = (type: string) => {
    const map: Record<string, { cls: string; label: string }> = {
      digital_doc: { cls: "badge-digital", label: "Digital" },
      scanned_doc: { cls: "badge-scanned", label: "Scanned" },
      component_photo: { cls: "badge-photo", label: "Component" },
    };
    const b = map[type] || { cls: "badge-pending", label: type || "…" };
    return <span className={`badge ${b.cls}`}>{b.label}</span>;
  };

  const statusBadge = (status: string) => {
    const cls =
      status === "completed"
        ? "badge-completed"
        : status === "processing"
        ? "badge-processing"
        : status === "failed"
        ? "badge-failed"
        : "badge-pending";
    return <span className={`badge ${cls}`}>{status}</span>;
  };

  return (
    <div>
      {/* Drop zone */}
      <div
        className={`drop-zone ${isDragging ? "active" : ""}`}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={onDrop}
        onClick={() => inputRef.current?.click()}
      >
        <input
          ref={inputRef}
          type="file"
          multiple
          style={{ display: "none" }}
          onChange={(e) => e.target.files && handleFiles(e.target.files)}
          accept=".pdf,.txt,.doc,.docx,.png,.jpg,.jpeg"
        />
        {uploading ? (
          <div>
            <span className="spinner" /> Uploading...
          </div>
        ) : (
          <div>
            <p style={{ fontSize: 18, marginBottom: 8 }}>
              📄 Drag & drop files here, or click to browse
            </p>
            <p style={{ color: "var(--muted)", fontSize: 13 }}>
              PDF, TXT, DOCX, PNG, JPEG — digital docs, scanned docs, and
              tear-down component photos
            </p>
          </div>
        )}
      </div>

      {/* Uploaded files list */}
      {files.length > 0 && (
        <div style={{ marginTop: 24 }}>
          <h3
            style={{ marginBottom: 12, fontSize: 12, color: "var(--muted)" }}
          >
            UPLOADED FILES ({files.length})
          </h3>
          {files.map((f) => (
            <div className="card file-card" key={f.id}>
              <div style={{ flex: 1 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                  <span style={{ fontWeight: 500 }}>{f.filename}</span>
                  {f.status === "processing" && (
                    <span className="spinner" style={{ width: 12, height: 12 }} />
                  )}
                </div>
                <div
                  style={{
                    marginTop: 6,
                    display: "flex",
                    gap: 8,
                    alignItems: "center",
                    flexWrap: "wrap",
                  }}
                >
                  {typeBadge(f.file_type)}
                  {statusBadge(f.status)}
                  {f.doc_category && (
                    <span className="badge badge-category">
                      {f.doc_category}
                    </span>
                  )}
                </div>
                {/* OCR confidence */}
                {f.ocr_confidence != null && f.ocr_confidence > 0 && (
                  <div style={{ marginTop: 8, maxWidth: 200 }}>
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        fontSize: 11,
                        color: "var(--muted)",
                        marginBottom: 2,
                      }}
                    >
                      <span>OCR</span>
                      <span>{Math.round(f.ocr_confidence * 100)}%</span>
                    </div>
                    <div className="confidence-bar">
                      <div
                        className={`confidence-fill ${
                          f.ocr_confidence >= 0.7
                            ? "confidence-high"
                            : f.ocr_confidence >= 0.4
                            ? "confidence-mid"
                            : "confidence-low"
                        }`}
                        style={{ width: `${f.ocr_confidence * 100}%` }}
                      />
                    </div>
                  </div>
                )}
              </div>
              {f.error && (
                <span style={{ color: "var(--error)", fontSize: 13 }}>
                  {f.error}
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
