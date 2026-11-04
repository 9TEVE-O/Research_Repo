import React, { useState, useCallback, useMemo, useEffect } from "react";
import { TOPICS, Paper } from "../data/papersData";
import { useFirebase } from "../context/FirebaseContext";
import {
  Search,
  ExternalLink,
  Bookmark,
  BookmarkCheck,
  Copy,
  Check,
  Filter,
  RefreshCw,
  BookOpen,
} from "lucide-react";

interface AcademicTerminalProps {
  globalQuery?: string;
}

export const AcademicTerminal: React.FC<AcademicTerminalProps> = ({ globalQuery = "" }) => {
  const { user, allPapers, addCustomPaper, isBookmarked, toggleBookmark } = useFirebase();

  const [selectedTopics, setSelectedTopics] = useState<string[]>([
    "ai",
    "ml",
    "software",
    "llm-systems",
  ]);
  const [papers, setPapers] = useState<Paper[]>(allPapers);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [activeFilter, setActiveFilter] = useState<string>("all");
  const [searchedTopics, setSearchedTopics] = useState<string[]>([
    "ai",
    "ml",
    "software",
    "llm-systems",
  ]);
  const [searchQuery, setSearchQuery] = useState<string>(globalQuery);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [customQuery, setCustomQuery] = useState<string>("");

  // Sync local papers when Firestore allPapers updates
  useEffect(() => {
    setPapers(allPapers);
  }, [allPapers]);

  // Sync local searchQuery when globalQuery from header changes
  useEffect(() => {
    setSearchQuery(globalQuery);
  }, [globalQuery]);

  const toggleTopic = (id: string) => {
    setSelectedTopics((prev) =>
      prev.includes(id) ? prev.filter((t) => t !== id) : [...prev, id]
    );
  };

  const selectAllTopics = () => {
    setSelectedTopics(TOPICS.map((t) => t.id));
  };

  const clearTopics = () => {
    setSelectedTopics([]);
  };

  const fetchPapers = useCallback(async () => {
    if (selectedTopics.length === 0) return;
    setLoading(true);
    setError(null);
    setSearchedTopics([...selectedTopics]);

    await new Promise((resolve) => setTimeout(resolve, 600));

    const results = allPapers.filter((p) =>
      selectedTopics.includes(p.topic)
    );

    setPapers(results);
    setLoading(false);
  }, [selectedTopics, allPapers]);

  const handleCustomSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!customQuery.trim()) return;

    const q = customQuery.trim();
    const targetTopic = selectedTopics[0] || "ai";
    const topicLabel =
      TOPICS.find((t) => t.id === targetTopic)?.label || "Artificial Intelligence";

    await addCustomPaper({
      topic: targetTopic,
      topicLabel,
      title: `Synthetic sample topic: ${q} (not a publication)`,
      authors: "Synthetic example; no authors verified",
      source: "Synthetic example (not arXiv)",
      date: "Not verified",
      abstract: `Synthetic sample record for ${q}. No paper retrieval or verification was performed.`,
      url: `https://arxiv.org/search/?query=${encodeURIComponent(q)}&searchtype=all`,
      tags: [q.toLowerCase().replace(/\s+/g, "-"), "synthetic-data", "not-verified"],
      citations: 0,
      doi: "",
    });

    setCustomQuery("");
  };

  const copyBibtex = (paper: Paper, e: React.MouseEvent) => {
    e.stopPropagation();
    const citeKey = `${paper.authors
      .split(",")[0]
      .replace(/[^a-zA-Z]/g, "")
      .toLowerCase()}${paper.date.replace(/[^0-9]/g, "")}`;
    const bibtex = `@article{${citeKey},
  title={${paper.title}},
  author={${paper.authors}},
  journal={${paper.source}},
  year={${paper.date.match(/\d{4}/)?.[0] || "unknown"}},
  url={${paper.url}},
  note={UNVERIFIED SYNTHETIC DEMO RECORD: not a validated bibliographic citation}
}`;
    navigator.clipboard.writeText(bibtex);
    setCopiedId(paper.id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filteredPapers = useMemo(() => {
    let result =
      activeFilter === "all"
        ? papers
        : papers.filter((p) => p.topic === activeFilter);
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(
        (p) =>
          p.title.toLowerCase().includes(q) ||
          p.abstract.toLowerCase().includes(q) ||
          p.authors.toLowerCase().includes(q) ||
          p.source.toLowerCase().includes(q) ||
          p.tags.some((t) => t.toLowerCase().includes(q))
      );
    }
    return result;
  }, [papers, activeFilter, searchQuery]);

  const topicCounts = useMemo(() => {
    return papers.reduce<Record<string, number>>((acc, p) => {
      acc[p.topic] = (acc[p.topic] || 0) + 1;
      return acc;
    }, {});
  }, [papers]);

  return (
    <div className="w-full">
      {/* Sub-header Banner */}
      <div className="border-b border-[#2a2a3a] px-6 py-6 bg-gradient-to-b from-[#0f0f1a] to-[#0a0a0f]">
        <div className="max-w-6xl mx-auto">
          <div className="flex flex-wrap items-baseline gap-3 mb-1">
            <span className="text-[#4a9eff] text-xs font-semibold tracking-widest uppercase flex items-center gap-1.5">
              <span className="inline-block w-2 h-2 rounded-full bg-[#4a9eff] animate-pulse"></span>
              ◈ RESEARCH_TERMINAL
            </span>
            <span className="text-[#555] text-xs">v2.0 // academic intelligence layer</span>
            <span className="ml-auto text-xs text-[#7ab8ff] bg-[#1a2a4a] px-2 py-0.5 border border-[#4a9eff33] rounded">
              Index: arXiv · MIT · Harvard · IEEE · ACM
            </span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-normal text-[#f0ede8] tracking-wide">
            Academic Paper Intelligence
          </h1>
          <p className="text-[#888] text-xs sm:text-sm mt-1 tracking-wider">
            Synthetic data demonstration. No live retrieval or verified citations.
          </p>
          <p role="status" className="mt-3 rounded border border-amber-700/50 bg-amber-950/30 p-3 text-xs text-amber-200">
            SYNTHETIC DATA · Preloaded paper records are examples, not independently verified publications. Generated examples are not scholarly citations. No academic search provider is contacted.
          </p>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* Research Domain Selector */}
        <div className="mb-8 p-5 bg-[#0c0c14] border border-[#1e1e2e] rounded">
          <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
            <div className="text-[11px] text-[#666] tracking-widest uppercase flex items-center gap-2">
              <span className="text-[#4a9eff]">▸</span> SELECT RESEARCH DOMAINS ({selectedTopics.length} selected)
            </div>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={selectAllTopics}
                className="text-[10px] text-[#7ab8ff] hover:underline uppercase tracking-wider"
              >
                Select All
              </button>
              <span className="text-[#333]">|</span>
              <button
                type="button"
                onClick={clearTopics}
                className="text-[10px] text-[#888] hover:underline uppercase tracking-wider"
              >
                Clear
              </button>
            </div>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-2">
            {TOPICS.map((topic) => {
              const active = selectedTopics.includes(topic.id);
              return (
                <button
                  key={topic.id}
                  onClick={() => toggleTopic(topic.id)}
                  className={`px-3 py-2 text-left text-xs transition-all flex items-center gap-2 border rounded ${
                    active
                      ? "bg-[#1a2a4a] border-[#4a9eff] text-[#7ab8ff] font-medium shadow-[0_0_8px_rgba(74,158,255,0.15)]"
                      : "bg-[#111118] border-[#2a2a3a] text-[#777] hover:border-[#444] hover:text-[#aaa]"
                  }`}
                >
                  <span className="text-[#4a9eff] text-sm leading-none font-mono">
                    {active ? "■" : "□"}
                  </span>
                  <span className="truncate">{topic.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Action Controls & Custom Query */}
        <div className="mb-8 flex flex-col md:flex-row items-stretch md:items-center gap-3">
          <button
            onClick={fetchPapers}
            disabled={selectedTopics.length === 0 || loading}
            className={`px-6 py-3 border text-xs tracking-widest uppercase font-semibold transition-all flex items-center justify-center gap-2 rounded ${
              selectedTopics.length === 0 || loading
                ? "bg-[#111118] border-[#2a2a3a] text-[#444] cursor-not-allowed"
                : "bg-[#0a2a5a] border-[#4a9eff] text-[#4a9eff] hover:bg-[#103875] hover:text-[#fff] cursor-pointer shadow-[0_0_12px_rgba(74,158,255,0.25)]"
            }`}
          >
            {loading ? (
              <>
                <RefreshCw className="w-3.5 h-3.5 animate-spin text-[#4a9eff]" />
                ⟳ LOADING SAMPLE RECORDS... ({papers.length} indexed)
              </>
            ) : (
              <>
                <span>▶</span> LOAD SAMPLE PAPERS ({selectedTopics.length} DOMAINS)
              </>
            )}
          </button>

          {/* Real-time search inside current indexed papers */}
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#555]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Filter sample records by keywords, title, author, or tags..."
              className="w-full bg-[#0c0c14] border border-[#2a2a3a] focus:border-[#4a9eff] text-xs text-[#e8e6e1] pl-9 pr-3 py-3 rounded outline-none placeholder-[#444] font-mono transition-colors"
            />
          </div>

          {/* Quick query custom paper synthesizer (persisted to Firestore when signed in) */}
          <form onSubmit={handleCustomSearch} className="flex gap-2">
            <input
              type="text"
              value={customQuery}
              onChange={(e) => setCustomQuery(e.target.value)}
              placeholder="Create synthetic demo topic..."
              className="bg-[#0c0c14] border border-[#2a2a3a] focus:border-[#4a9eff] text-xs text-[#e8e6e1] px-3 py-3 rounded outline-none placeholder-[#444] font-mono w-44"
            />
            <button
              type="submit"
              disabled={!customQuery.trim()}
              className="px-3 py-3 bg-[#162238] border border-[#304875] text-[#7ab8ff] text-xs hover:bg-[#1e3258] disabled:opacity-40 disabled:cursor-not-allowed rounded uppercase tracking-wider"
              title={user ? "Add and persist paper to Firestore" : "Add simulated paper for topic"}
            >
              + Add
            </button>
          </form>
        </div>

        {/* Filter bar */}
        {papers.length > 0 && (
          <div className="mb-6 flex items-center gap-2 flex-wrap pb-3 border-b border-[#1e1e2e]">
            <span className="text-[10px] text-[#555] tracking-widest uppercase flex items-center gap-1.5 mr-2">
              <Filter className="w-3 h-3 text-[#4a9eff]" /> FILTER:
            </span>
            <button
              onClick={() => setActiveFilter("all")}
              className={`px-3 py-1 text-xs border rounded transition-all ${
                activeFilter === "all"
                  ? "bg-[#1a1a2a] border-[#888] text-[#fff] font-medium"
                  : "bg-transparent border-[#2a2a3a] text-[#666] hover:text-[#aaa]"
              }`}
            >
              ALL ({papers.length})
            </button>
            {searchedTopics.map((tid) => {
              const topic = TOPICS.find((t) => t.id === tid);
              const count = topicCounts[tid] || 0;
              return (
                <button
                  key={tid}
                  onClick={() => setActiveFilter(tid)}
                  className={`px-3 py-1 text-xs border rounded transition-all ${
                    activeFilter === tid
                      ? "bg-[#1a2a4a] border-[#4a9eff] text-[#7ab8ff] font-medium"
                      : "bg-transparent border-[#2a2a3a] text-[#555] hover:border-[#444] hover:text-[#888]"
                  }`}
                >
                  {topic?.label || tid} ({count})
                </button>
              );
            })}
            <div className="ml-auto text-[11px] text-[#666]">
              Showing {filteredPapers.length} of {papers.length} publications
            </div>
          </div>
        )}

        {/* Paper cards list */}
        {filteredPapers.length > 0 ? (
          <div className="flex flex-col gap-2.5">
            {filteredPapers.map((paper, index) => (
              <PaperCard
                key={paper.id || index}
                paper={paper}
                index={index}
                copied={copiedId === paper.id}
                onCopyBibtex={(e) => copyBibtex(paper, e)}
                userSignedIn={!!user}
                bookmarked={isBookmarked(paper.id)}
                onToggleBookmark={(e) => {
                  e.stopPropagation();
                  toggleBookmark({
                    itemId: paper.id,
                    itemType: "paper",
                    title: paper.title,
                    sourceOrLanguage: paper.source,
                    url: paper.url,
                  });
                }}
              />
            ))}
          </div>
        ) : (
          !loading && (
            <div className="p-12 text-center border border-[#1e1e2e] bg-[#0c0c14] rounded">
              <BookOpen className="w-8 h-8 text-[#444] mx-auto mb-3" />
              <div className="text-sm text-[#777] mb-1">
                {searchQuery
                  ? `No papers match the search term "${searchQuery}"`
                  : "No publications retrieved for current selection."}
              </div>
              <p className="text-xs text-[#555]">
                Adjust your domain selections above or clear the global search query.
              </p>
            </div>
          )
        )}

        {error && (
          <div className="mt-6 p-4 border border-[#5a1a1a] bg-[#1a0a0a] text-[#ff6b6b] text-xs rounded">
            ✕ ERROR: {error}
          </div>
        )}
      </div>
    </div>
  );
};

interface PaperCardProps {
  paper: Paper;
  index: number;
  copied: boolean;
  onCopyBibtex: (e: React.MouseEvent) => void;
  userSignedIn: boolean;
  bookmarked: boolean;
  onToggleBookmark: (e: React.MouseEvent) => void;
}

const PaperCard: React.FC<PaperCardProps> = ({
  paper,
  index,
  copied,
  onCopyBibtex,
  userSignedIn,
  bookmarked,
  onToggleBookmark,
}) => {
  const [expanded, setExpanded] = useState<boolean>(false);

  const sourceColors: Record<string, string> = {
    arXiv: "#f5a623",
    MIT: "#e74c3c",
    Harvard: "#9b59b6",
    IEEE: "#3498db",
    ACM: "#27ae60",
  };

  const src = paper.source?.split("/")?.[0]?.trim() || paper.source || "—";
  const color = sourceColors[src] || "#666";

  return (
    <div
      onClick={() => setExpanded(!expanded)}
      className={`border border-[#1e1e2e] rounded transition-all cursor-pointer p-4 sm:p-5 ${
        expanded ? "bg-[#0f0f1a] border-[#2a2a3a]" : "bg-[#0c0c14] hover:bg-[#0e0e18]"
      }`}
      style={{ borderLeft: `3px solid ${color}` }}
    >
      <div className="flex gap-3 sm:gap-4 items-start">
        <span className="text-[#444] text-[11px] font-mono min-w-[28px] pt-0.5 select-none">
          {String(index + 1).padStart(2, "0")}
        </span>

        <div className="flex-1 min-w-0">
          {/* Metadata badges row */}
          <div className="flex flex-wrap items-center gap-2 mb-1.5">
            <span
              className="text-[10px] tracking-wider uppercase px-2 py-0.5 border rounded font-mono font-medium"
              style={{
                color,
                borderColor: `${color}44`,
                backgroundColor: `${color}11`,
              }}
            >
              {src}
            </span>

            {paper.topicLabel && (
              <span className="text-[10px] border border-[#1a3a6a] px-2 py-0.5 text-[#4a7aaa] bg-[#0c1a2e] rounded font-mono">
                {paper.topicLabel}
              </span>
            )}

            {paper.date && (
              <span className="text-[#555] text-[11px] font-mono">
                {paper.date}
              </span>
            )}

            {paper.citations !== undefined && (
              <span className="text-[10px] text-[#777] border border-[#2a2a3a] px-1.5 py-0.5 rounded">
                ★ {paper.citations} citations
              </span>
            )}

            <div className="ml-auto flex items-center gap-2">
              {userSignedIn && (
                <button
                  type="button"
                  onClick={onToggleBookmark}
                  className={`px-2 py-0.5 text-[10px] border rounded font-mono flex items-center gap-1 transition-colors ${
                    bookmarked
                      ? "bg-emerald-950/60 border-emerald-600 text-emerald-400"
                      : "bg-[#111118] border-[#2a2a3a] text-[#777] hover:text-[#ccc]"
                  }`}
                >
                  {bookmarked ? (
                    <>
                      <BookmarkCheck className="w-3 h-3" /> Saved
                    </>
                  ) : (
                    <>
                      <Bookmark className="w-3 h-3" /> Save
                    </>
                  )}
                </button>
              )}
              <span className="text-[#555] text-xs font-mono">
                {expanded ? "▲ collapse" : "▼ expand"}
              </span>
            </div>
          </div>

          {/* Paper Title */}
          <h3 className="text-sm sm:text-base text-[#e8e6e1] font-medium leading-snug mb-1">
            {paper.title || "Untitled Publication"}
          </h3>

          {/* Authors */}
          {paper.authors && (
            <div className="text-xs text-[#666] mb-2 font-mono">
              {paper.authors}
            </div>
          )}

          {/* Expanded Drawer */}
          {expanded && (
            <div className="mt-4 pt-4 border-t border-[#1e1e2e] space-y-3">
              {paper.abstract && (
                <div>
                  <div className="text-[10px] text-[#555] tracking-widest uppercase mb-1">
                    ABSTRACT / SUMMARY:
                  </div>
                  <p className="text-xs sm:text-[13px] text-[#999] leading-relaxed font-sans">
                    {paper.abstract}
                  </p>
                </div>
              )}

              {/* Tags */}
              {paper.tags && paper.tags.length > 0 && (
                <div className="flex flex-wrap gap-1.5 pt-1">
                  {paper.tags.map((tag, i) => (
                    <span
                      key={i}
                      className="text-[10px] text-[#778] border border-[#222233] bg-[#12121e] px-2 py-0.5 rounded font-mono"
                    >
                      #{tag}
                    </span>
                  ))}
                </div>
              )}

              {/* Action buttons */}
              <div className="flex flex-wrap items-center gap-4 pt-2 text-xs">
                {paper.url && (
                  <a
                    href={paper.url}
                    target="_blank"
                    rel="noreferrer"
                    onClick={(e) => e.stopPropagation()}
                    className="text-[#4a9eff] hover:underline flex items-center gap-1 border-b border-[#4a9eff44] pb-0.5 font-mono"
                  >
                    <ExternalLink className="w-3.5 h-3.5" />
                    Open Source Document ({src})
                  </a>
                )}

                <button
                  type="button"
                  onClick={onCopyBibtex}
                  className="text-[#888] hover:text-[#ccc] flex items-center gap-1 font-mono transition-colors"
                >
                  {copied ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-400" />
                      <span className="text-emerald-400">Copied BibTeX!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" />
                      <span>Copy BibTeX</span>
                    </>
                  )}
                </button>

                {paper.doi && (
                  <span className="text-[#555] font-mono text-[11px] ml-auto">
                    DOI: {paper.doi}
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
