"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  LayoutDashboard,
  Upload,
  FileText,
  Database,
  BrainCircuit,
  Zap,
  ChevronRight,
} from "lucide-react";
import UploadView from "@/components/UploadView";
import StructuredQueryView from "@/components/StructuredQueryView";
import AnalyticalQueryView from "@/components/AnalyticalQueryView";
import DocumentsView from "@/components/DocumentsView";
import DashboardView from "@/components/DashboardView";
import { api } from "@/lib/api";

type Tab = "dashboard" | "upload" | "documents" | "structured" | "analytical";

const navItems: { key: Tab; label: string; icon: React.ElementType; desc: string }[] = [
  { key: "dashboard", label: "Dashboard", icon: LayoutDashboard, desc: "Overview & analytics" },
  { key: "upload", label: "Upload", icon: Upload, desc: "Ingest documents" },
  { key: "documents", label: "Documents", icon: FileText, desc: "Browse & inspect" },
  { key: "structured", label: "SQL Query", icon: Database, desc: "Natural language → SQL" },
  { key: "analytical", label: "RAG Query", icon: BrainCircuit, desc: "AI-powered analysis" },
];

export default function Home() {
  const [activeTab, setActiveTab] = useState<Tab>("dashboard");
  const [backendStatus, setBackendStatus] = useState<"checking" | "ok" | "error">("checking");

  useEffect(() => {
    api.health().then(() => setBackendStatus("ok")).catch(() => setBackendStatus("error"));
  }, []);

  return (
    <div className="flex h-screen bg-mesh">
      {/* Sidebar */}
      <aside className="w-[260px] flex-shrink-0 border-r border-white/[0.06] bg-[#08090e]/80 backdrop-blur-xl flex flex-col">
        {/* Logo */}
        <div className="px-5 pt-6 pb-8">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-[15px] font-bold tracking-tight text-white">DocIntell</h1>
              <p className="text-[11px] text-[#5c5f73] font-medium">Enterprise Intelligence</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 px-3 space-y-1">
          <p className="px-3 mb-2 text-[10px] font-semibold uppercase tracking-[0.15em] text-[#5c5f73]">
            Navigation
          </p>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.key;
            return (
              <button
                key={item.key}
                onClick={() => setActiveTab(item.key)}
                className={`nav-item w-full group ${isActive ? "active" : ""}`}
              >
                <Icon className={`w-[18px] h-[18px] flex-shrink-0 transition-colors ${isActive ? "text-indigo-400" : "text-[#5c5f73] group-hover:text-[#9396a5]"}`} />
                <div className="flex-1 text-left">
                  <span className="block">{item.label}</span>
                  <span className={`block text-[11px] font-normal mt-0.5 transition-colors ${isActive ? "text-indigo-300/60" : "text-[#5c5f73]"}`}>
                    {item.desc}
                  </span>
                </div>
                {isActive && (
                  <ChevronRight className="w-3.5 h-3.5 text-indigo-400/60" />
                )}
              </button>
            );
          })}
        </nav>

        {/* Backend Status */}
        <div className="px-5 py-4 border-t border-white/[0.06]">
          <div className="flex items-center gap-2.5">
            <div className="relative">
              <div className={`w-2 h-2 rounded-full ${
                backendStatus === "ok" ? "bg-emerald-400" :
                backendStatus === "error" ? "bg-red-400" : "bg-amber-400"
              }`} />
              {backendStatus === "ok" && (
                <div className="absolute inset-0 w-2 h-2 rounded-full bg-emerald-400 animate-ping opacity-40" />
              )}
            </div>
            <span className="text-[12px] text-[#5c5f73]">
              {backendStatus === "ok" ? "Backend connected" :
               backendStatus === "error" ? "Backend offline" : "Connecting..."}
            </span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-[1200px] mx-auto px-8 py-8">
          {/* Page Header */}
          <motion.div
            key={activeTab + "-header"}
            initial={{ opacity: 0, y: -8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="mb-8"
          >
            <h2 className="text-2xl font-bold text-white tracking-tight">
              {navItems.find((n) => n.key === activeTab)?.label}
            </h2>
            <p className="text-sm text-[#5c5f73] mt-1">
              {navItems.find((n) => n.key === activeTab)?.desc}
            </p>
          </motion.div>

          {/* Page Content */}
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.3 }}
            >
              {activeTab === "dashboard" && <DashboardView />}
              {activeTab === "upload" && <UploadView />}
              {activeTab === "documents" && <DocumentsView />}
              {activeTab === "structured" && <StructuredQueryView />}
              {activeTab === "analytical" && <AnalyticalQueryView />}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>
    </div>
  );
}
