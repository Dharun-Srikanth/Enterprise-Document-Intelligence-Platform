"use client";

import { useState, useEffect } from "react";
import UploadView from "@/components/UploadView";
import StructuredQueryView from "@/components/StructuredQueryView";
import AnalyticalQueryView from "@/components/AnalyticalQueryView";
import DocumentsView from "@/components/DocumentsView";
import DashboardView from "@/components/DashboardView";
import { api } from "@/lib/api";

type Tab = "dashboard" | "upload" | "documents" | "structured" | "analytical";

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>("dashboard");
  const [backendStatus, setBackendStatus] = useState<
    "checking" | "ok" | "error"
  >("checking");

  useEffect(() => {
    api
      .health()
      .then(() => setBackendStatus("ok"))
      .catch(() => setBackendStatus("error"));
  }, []);

  const tabs: { key: Tab; label: string; icon: string }[] = [
    { key: "dashboard", label: "Dashboard", icon: "📊" },
    { key: "upload", label: "Upload", icon: "📤" },
    { key: "documents", label: "Documents", icon: "📄" },
    { key: "structured", label: "SQL Query", icon: "🔍" },
    { key: "analytical", label: "RAG Query", icon: "🧠" },
  ];

  return (
    <div className="container" style={{ paddingTop: 24, paddingBottom: 48 }}>
      {/* Header */}
      <div
        style={{
          marginBottom: 24,
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        <div>
          <h1 style={{ fontSize: 22, fontWeight: 700 }}>
            Document Intelligence Platform
          </h1>
          <p style={{ color: "var(--muted)", fontSize: 13, marginTop: 4 }}>
            Enterprise document analysis with sustainability analytics
          </p>
        </div>
        <div>
          {backendStatus === "checking" && (
            <span style={{ color: "var(--muted)", fontSize: 12 }}>
              <span className="spinner" /> Connecting...
            </span>
          )}
          {backendStatus === "ok" && (
            <span style={{ color: "var(--success)", fontSize: 12 }}>
              ● Backend connected
            </span>
          )}
          {backendStatus === "error" && (
            <span style={{ color: "var(--error)", fontSize: 12 }}>
              ● Backend unavailable
            </span>
          )}
        </div>
      </div>

      {/* Tabs */}
      <div className="nav-tabs">
        {tabs.map((t) => (
          <button
            key={t.key}
            className={`nav-tab ${activeTab === t.key ? "active" : ""}`}
            onClick={() => setActiveTab(t.key)}
          >
            <span style={{ marginRight: 6 }}>{t.icon}</span>
            {t.label}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      {activeTab === "dashboard" && <DashboardView />}
      {activeTab === "upload" && <UploadView />}
      {activeTab === "documents" && <DocumentsView />}
      {activeTab === "structured" && <StructuredQueryView />}
      {activeTab === "analytical" && <AnalyticalQueryView />}
    </div>
  );
}
