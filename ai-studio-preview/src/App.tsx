import React, { useState } from "react";
import { AcademicTerminal } from "./components/AcademicTerminal";
import { RepoScoringPipeline } from "./components/RepoScoringPipeline";
import { KnowledgeGraphViewer } from "./components/KnowledgeGraphViewer";
import { TypeSafeClassifier } from "./components/TypeSafeClassifier";
import { ReportViewer } from "./components/ReportViewer";
import { GuardrailsViewer } from "./components/GuardrailsViewer";
import { GlobalSearchBar } from "./components/GlobalSearchBar";
import { FirebaseProvider, useFirebase, ActiveTab } from "./context/FirebaseContext";
import { FIREBASE_ENABLED } from "./firebase";
import {
  Terminal,
  GitPullRequest,
  Network,
  ShieldCheck,
  FileText,
  Cpu,
  LogIn,
  LogOut,
  BookmarkCheck,
  ExternalLink,
  Trash2,
  X,
} from "lucide-react";

function AppShell() {
  const [activeTab, setActiveTab] = useState<ActiveTab>("terminal");
  const [globalQuery, setGlobalQuery] = useState<string>("");
  const [showBookmarksModal, setShowBookmarksModal] = useState<boolean>(false);
  const [editingNoteId, setEditingNoteId] = useState<string | null>(null);
  const [noteDraft, setNoteDraft] = useState<string>("");

  const {
    user,
    authReady,
    signInWithGoogle,
    signOutUser,
    bookmarks,
    toggleBookmark,
    updateBookmarkNotes,
  } = useFirebase();

  const navItems = [
    {
      id: "terminal" as const,
      label: "Academic Terminal",
      sublabel: "arXiv · MIT · IEEE",
      icon: Terminal,
      color: "text-[#4a9eff]",
    },
    {
      id: "discovery" as const,
      label: "Repo Scoring Agent",
      sublabel: "0–100 relevance score",
      icon: GitPullRequest,
      color: "text-emerald-400",
    },
    {
      id: "knowledge-graph" as const,
      label: "Knowledge Graph",
      sublabel: "Triples & provenance audit",
      icon: Network,
      color: "text-[#a78bfa]",
    },
    {
      id: "typesafe" as const,
      label: "TypeSafe Evidence",
      sublabel: "Claim classification",
      icon: ShieldCheck,
      color: "text-[#38bdf8]",
    },
    {
      id: "reports" as const,
      label: "Reports & Whitepaper",
      sublabel: "Markdown & ACM paper",
      icon: FileText,
      color: "text-amber-400",
    },
    {
      id: "guardrails" as const,
      label: "Pipeline Guardrails",
      sublabel: "Invariant enforcement",
      icon: Cpu,
      color: "text-rose-400",
    },
  ];

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-[#e8e6e1] font-mono flex flex-col">
      {/* Top Global Navigation Bar */}
      <header className="border-b border-[#1e1e2e] bg-[#0c0c14]/95 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-14 gap-2">
            {/* Logo / App identifier */}
            <div className="flex items-center gap-2 shrink-0">
              <span className="text-[#4a9eff] text-sm sm:text-base font-bold tracking-widest flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-[#4a9eff] shadow-[0_0_8px_#4a9eff] animate-pulse"></span>
                RESEARCH_REPO
              </span>
            </div>

            {/* Global Search Bar with Active Tab Context */}
            <GlobalSearchBar
              activeTab={activeTab}
              onSelectTab={(tab) => setActiveTab(tab)}
              globalQuery={globalQuery}
              onGlobalQueryChange={setGlobalQuery}
            />

            {/* Right Actions: Bookmarks, Auth, GitHub */}
            <div className="flex items-center gap-2 text-xs shrink-0">
              {user && (
                <button
                  type="button"
                  onClick={() => setShowBookmarksModal(true)}
                  className="px-2.5 py-1.5 rounded bg-[#142036] hover:bg-[#1b2c4b] text-[#7ab8ff] border border-[#2b4470] flex items-center gap-1.5 transition-colors"
                  title="View saved bookmarks in Firestore"
                >
                  <BookmarkCheck className="w-3.5 h-3.5 text-emerald-400" />
                  <span className="hidden md:inline">Saved</span>
                  <span className="px-1 rounded bg-[#0a0a0f] text-[10px] text-emerald-400">
                    {bookmarks.length}
                  </span>
                </button>
              )}

              {FIREBASE_ENABLED && authReady && (
                user ? (
                  <div className="flex items-center gap-2">
                    <span className="hidden xl:inline text-[11px] text-[#999] truncate max-w-[120px]">
                      {user.displayName || user.email}
                    </span>
                    <button
                      type="button"
                      onClick={signOutUser}
                      className="px-2.5 py-1.5 rounded bg-[#161622] hover:bg-[#222234] text-[#bbb] border border-[#2a2a3a] flex items-center gap-1 transition-colors"
                      title="Sign out"
                    >
                      <LogOut className="w-3.5 h-3.5 text-rose-400" />
                      <span className="hidden sm:inline">Sign Out</span>
                    </button>
                  </div>
                ) : (
                  <button
                    type="button"
                    onClick={signInWithGoogle}
                    className="px-3 py-1.5 rounded bg-[#0a2a5a] hover:bg-[#103875] text-[#7ab8ff] hover:text-white border border-[#4a9eff] flex items-center gap-1.5 transition-colors font-semibold"
                  >
                    <LogIn className="w-3.5 h-3.5" />
                    <span>Sign In</span>
                  </button>
                )
              )}

              <a
                href="https://github.com/9TEVE-O/Research_Repo"
                target="_blank"
                rel="noreferrer"
                className="text-[#888] hover:text-[#fff] hidden sm:flex items-center gap-1.5 transition-colors px-2 py-1"
                title="View GitHub Repository"
              >
                <svg className="w-4 h-4 fill-current" viewBox="0 0 24 24">
                  <path
                    fillRule="evenodd"
                    clipRule="evenodd"
                    d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"
                  />
                </svg>
              </a>
            </div>
          </div>

          {/* Module Navigation Tabs */}
          <div className="flex overflow-x-auto scrollbar-none border-t border-[#181824] gap-1 -mb-[1px]">
            {navItems.map((item) => {
              const active = activeTab === item.id;
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveTab(item.id)}
                  className={`flex items-center gap-2 px-3.5 py-2.5 text-xs font-mono whitespace-nowrap transition-all border-b-2 ${
                    active
                      ? "border-[#4a9eff] text-[#f0ede8] bg-[#12121f]"
                      : "border-transparent text-[#777] hover:text-[#bbb] hover:bg-[#0f0f18]"
                  }`}
                >
                  <Icon className={`w-3.5 h-3.5 ${active ? item.color : "text-[#555]"}`} />
                  <span className="font-semibold">{item.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </header>

      <div role="status" className="border-b border-amber-700/50 bg-amber-950/30 px-4 py-2 text-center text-xs text-amber-200">
        REVIEW ONLY · Simulated research data; no verified citations, live search, provider scores or model evaluations. Firebase disconnected.
      </div>

      {/* Main Content Area */}
      <main className="flex-1">
        {activeTab === "terminal" && <AcademicTerminal globalQuery={globalQuery} />}
        {activeTab === "discovery" && <RepoScoringPipeline globalQuery={globalQuery} />}
        {activeTab === "knowledge-graph" && <KnowledgeGraphViewer />}
        {activeTab === "typesafe" && <TypeSafeClassifier />}
        {activeTab === "reports" && <ReportViewer />}
        {activeTab === "guardrails" && <GuardrailsViewer />}
      </main>

      {/* Saved Bookmarks Modal (Firestore Persistence) */}
      {showBookmarksModal && (
        <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#0c0c14] border border-[#2a2a3a] rounded-md max-w-2xl w-full max-h-[80vh] flex flex-col shadow-2xl">
            <div className="p-4 border-b border-[#1e1e2e] flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm font-bold text-[#f0ede8]">
                <BookmarkCheck className="w-4 h-4 text-emerald-400" />
                Saved Research Bookmarks ({bookmarks.length})
              </div>
              <button
                type="button"
                onClick={() => setShowBookmarksModal(false)}
                className="text-[#777] hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="p-4 overflow-y-auto space-y-3 flex-1">
              {bookmarks.length === 0 ? (
                <div className="py-12 text-center text-xs text-[#666]">
                  No bookmarks saved yet. Use the Global Search Bar or click "Save / Bookmark" on any arXiv paper or repository.
                </div>
              ) : (
                bookmarks.map((bm) => (
                  <div
                    key={bm.id}
                    className="p-3.5 bg-[#10101a] border border-[#1e1e2e] rounded space-y-2"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <span className="text-[10px] uppercase px-1.5 py-0.5 rounded bg-[#1a2a4a] text-[#7ab8ff] mr-2">
                          {bm.itemType}
                        </span>
                        <span className="text-[10px] text-[#888]">{bm.sourceOrLanguage}</span>
                        <div className="text-xs sm:text-sm text-[#f0ede8] font-medium mt-1">
                          {bm.title}
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <a
                          href={bm.url}
                          target="_blank"
                          rel="noreferrer"
                          className="text-xs text-[#4a9eff] hover:underline flex items-center gap-1"
                        >
                          Open <ExternalLink className="w-3 h-3" />
                        </a>
                        <button
                          type="button"
                          onClick={() =>
                            toggleBookmark({
                              itemId: bm.itemId,
                              itemType: bm.itemType,
                              title: bm.title,
                              sourceOrLanguage: bm.sourceOrLanguage,
                              url: bm.url,
                            })
                          }
                          className="text-[#666] hover:text-rose-400 p-1"
                          title="Delete bookmark"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>

                    {/* Research Note Editor */}
                    {editingNoteId === bm.id ? (
                      <div className="flex gap-2 pt-1">
                        <input
                          type="text"
                          value={noteDraft}
                          onChange={(e) => setNoteDraft(e.target.value)}
                          placeholder="Add research note (max 500 chars)..."
                          maxLength={500}
                          className="flex-1 bg-[#090910] border border-[#2a2a3a] text-xs text-[#ddd] px-2.5 py-1 rounded outline-none focus:border-[#4a9eff]"
                        />
                        <button
                          type="button"
                          onClick={async () => {
                            await updateBookmarkNotes(bm.id, noteDraft);
                            setEditingNoteId(null);
                          }}
                          className="px-2.5 py-1 bg-emerald-950 border border-emerald-600 text-emerald-400 text-xs rounded"
                        >
                          Save
                        </button>
                        <button
                          type="button"
                          onClick={() => setEditingNoteId(null)}
                          className="px-2 py-1 text-xs text-[#777]"
                        >
                          Cancel
                        </button>
                      </div>
                    ) : (
                      <div className="flex items-center justify-between text-[11px] text-[#888] pt-1 border-t border-[#181824]">
                        <span className="italic">
                          {bm.notes ? `"${bm.notes}"` : "No research annotation attached."}
                        </span>
                        <button
                          type="button"
                          onClick={() => {
                            setEditingNoteId(bm.id);
                            setNoteDraft(bm.notes || "");
                          }}
                          className="text-[#4a9eff] hover:underline text-[10px]"
                        >
                          {bm.notes ? "Edit Note" : "+ Add Note"}
                        </button>
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="border-t border-[#1e1e2e] py-6 px-6 bg-[#08080c] mt-auto">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-[#555] font-mono">
          <div>Research_Repo — Automated AI & Academic Intelligence Suite</div>
          <div className="flex items-center gap-4 text-[11px]">
            <span>arXiv · MIT · Harvard · IEEE · ACM</span>
            <span>·</span>
            <span>Firebase disconnected · review only</span>
            <span>·</span>
            <span>MIT License</span>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default function App() {
  return (
    <FirebaseProvider>
      <AppShell />
    </FirebaseProvider>
  );
}
