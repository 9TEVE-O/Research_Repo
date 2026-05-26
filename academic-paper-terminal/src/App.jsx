import { useState, useCallback } from "react";

const TOPICS = [
  { id: "ai", label: "Artificial Intelligence" },
  { id: "ml", label: "Machine Learning" },
  { id: "robotics", label: "Robotics" },
  { id: "physics", label: "Physics" },
  { id: "quantum", label: "Quantum Computing" },
  { id: "software", label: "Software Engineering" },
  { id: "webdev", label: "Web Development" },
  { id: "machinebuilding", label: "Machine Building" },
];

export default function App() {
  const [selectedTopics, setSelectedTopics] = useState([]);
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [activeFilter, setActiveFilter] = useState("all");
  const [searchedTopics, setSearchedTopics] = useState([]);

  const toggleTopic = (id) => {
    setSelectedTopics(prev =>
      prev.includes(id) ? prev.filter(t => t !== id) : [...prev, id]
    );
  };

  const fetchPapers = useCallback(async () => {
    if (selectedTopics.length === 0) return;
    setLoading(true);
    setError(null);
    setPapers([]);
    setSearchedTopics([...selectedTopics]);

    const topicsToFetch = TOPICS.filter(t => selectedTopics.includes(t.id));

    for (const topic of topicsToFetch) {
      try {
        const response = await fetch("/api/papers", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ topicLabel: topic.label }),
        });

        if (!response.ok) throw new Error(`API error ${response.status}`);
        const data = await response.json();

        const textBlocks = data.content?.filter(b => b.type === "text") || [];
        const rawText = textBlocks.map(b => b.text).join("");

        let parsed = [];
        try {
          const match = rawText.match(/\[[\s\S]*\]/);
          if (match) parsed = JSON.parse(match[0]);
        } catch {
          try { parsed = JSON.parse(rawText); } catch { parsed = []; }
        }

        const tagged = parsed.map((p, i) => ({
          ...p,
          id: `${topic.id}-${i}`,
          topic: topic.id,
          topicLabel: topic.label,
        }));
        setPapers(prev => [...prev, ...tagged]);
      } catch (err) {
        console.error(`Failed to fetch ${topic.label}:`, err);
        setError(err.message);
      }
    }

    setLoading(false);
  }, [selectedTopics]);

  const filtered = activeFilter === "all"
    ? papers
    : papers.filter(p => p.topic === activeFilter);

  const topicCounts = papers.reduce((acc, p) => {
    acc[p.topic] = (acc[p.topic] || 0) + 1;
    return acc;
  }, {});

  return (
    <div style={{
      minHeight: "100vh",
      background: "#0a0a0f",
      color: "#e8e6e1",
      fontFamily: "'Courier New', 'Lucida Console', monospace",
      padding: "0",
    }}>
      {/* Header */}
      <div style={{
        borderBottom: "1px solid #2a2a3a",
        padding: "28px 40px 24px",
        background: "linear-gradient(180deg, #0f0f1a 0%, #0a0a0f 100%)",
        position: "sticky",
        top: 0,
        zIndex: 10,
      }}>
        <div style={{ maxWidth: 1100, margin: "0 auto" }}>
          <div style={{ display: "flex", alignItems: "baseline", gap: 16, marginBottom: 4 }}>
            <span style={{ color: "#4a9eff", fontSize: 11, letterSpacing: 4, textTransform: "uppercase" }}>
              ◈ RESEARCH_TERMINAL
            </span>
            <span style={{ color: "#444", fontSize: 10 }}>v2.0 // academic intelligence layer</span>
          </div>
          <h1 style={{ margin: 0, fontSize: 26, fontWeight: "normal", color: "#f0ede8", letterSpacing: 1 }}>
            Academic Paper Intelligence
          </h1>
          <p style={{ margin: "6px 0 0", color: "#666", fontSize: 12, letterSpacing: 0.5 }}>
            arXiv · MIT · Harvard · IEEE · ACM — live retrieval
          </p>
        </div>
      </div>

      <div style={{ maxWidth: 1100, margin: "0 auto", padding: "32px 40px" }}>
        {/* Topic selector */}
        <div style={{ marginBottom: 32 }}>
          <div style={{ fontSize: 10, color: "#555", letterSpacing: 3, textTransform: "uppercase", marginBottom: 14 }}>
            ▸ SELECT RESEARCH DOMAINS
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
            {TOPICS.map(topic => {
              const active = selectedTopics.includes(topic.id);
              return (
                <button
                  key={topic.id}
                  onClick={() => toggleTopic(topic.id)}
                  style={{
                    padding: "8px 16px",
                    background: active ? "#1a2a4a" : "#111118",
                    border: `1px solid ${active ? "#4a9eff" : "#2a2a3a"}`,
                    color: active ? "#7ab8ff" : "#666",
                    cursor: "pointer",
                    fontSize: 12,
                    letterSpacing: 0.5,
                    transition: "all 0.15s",
                    fontFamily: "inherit",
                  }}
                >
                  {active ? "■" : "□"} {topic.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Fetch button */}
        <div style={{ marginBottom: 36 }}>
          <button
            onClick={fetchPapers}
            disabled={selectedTopics.length === 0 || loading}
            style={{
              padding: "12px 32px",
              background: selectedTopics.length === 0 || loading ? "#111118" : "#0a2a5a",
              border: `1px solid ${selectedTopics.length === 0 || loading ? "#2a2a3a" : "#4a9eff"}`,
              color: selectedTopics.length === 0 || loading ? "#333" : "#4a9eff",
              cursor: selectedTopics.length === 0 || loading ? "not-allowed" : "pointer",
              fontSize: 12,
              letterSpacing: 2,
              textTransform: "uppercase",
              fontFamily: "inherit",
              transition: "all 0.15s",
            }}
          >
            {loading
              ? `⟳ FETCHING PAPERS... (${papers.length} found)`
              : `▶ FETCH PAPERS (${selectedTopics.length} domain${selectedTopics.length !== 1 ? "s" : ""})`
            }
          </button>
          {selectedTopics.length === 0 && (
            <span style={{ marginLeft: 16, color: "#444", fontSize: 11 }}>
              select at least one domain
            </span>
          )}
        </div>

        {/* Results */}
        {papers.length > 0 && (
          <>
            {/* Filter bar */}
            <div style={{ marginBottom: 24, display: "flex", gap: 8, flexWrap: "wrap" }}>
              <span style={{ fontSize: 10, color: "#555", letterSpacing: 3, textTransform: "uppercase", alignSelf: "center", marginRight: 4 }}>
                FILTER:
              </span>
              <button
                onClick={() => setActiveFilter("all")}
                style={{
                  padding: "4px 12px",
                  background: activeFilter === "all" ? "#1a1a2a" : "transparent",
                  border: `1px solid ${activeFilter === "all" ? "#666" : "#2a2a3a"}`,
                  color: activeFilter === "all" ? "#ccc" : "#555",
                  cursor: "pointer",
                  fontSize: 11,
                  fontFamily: "inherit",
                }}
              >
                ALL ({papers.length})
              </button>
              {searchedTopics.map(tid => {
                const topic = TOPICS.find(t => t.id === tid);
                const count = topicCounts[tid] || 0;
                return (
                  <button
                    key={tid}
                    onClick={() => setActiveFilter(tid)}
                    style={{
                      padding: "4px 12px",
                      background: activeFilter === tid ? "#1a2a4a" : "transparent",
                      border: `1px solid ${activeFilter === tid ? "#4a9eff" : "#2a2a3a"}`,
                      color: activeFilter === tid ? "#7ab8ff" : "#555",
                      cursor: "pointer",
                      fontSize: 11,
                      fontFamily: "inherit",
                    }}
                  >
                    {topic?.label} ({count})
                  </button>
                );
              })}
            </div>

            {/* Paper cards */}
            <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
              {filtered.map((paper, i) => (
                <PaperCard key={paper.id || i} paper={paper} index={i} />
              ))}
            </div>
          </>
        )}

        {/* Empty state */}
        {!loading && papers.length === 0 && selectedTopics.length > 0 && (
          <div style={{ color: "#444", fontSize: 13, padding: "40px 0", textAlign: "center" }}>
            Press FETCH PAPERS to retrieve results
          </div>
        )}

        {error && (
          <div style={{
            padding: "16px 20px",
            border: "1px solid #5a1a1a",
            background: "#1a0a0a",
            color: "#ff6b6b",
            fontSize: 12,
            marginTop: 20,
          }}>
            ✕ ERROR: {error}
          </div>
        )}
      </div>
    </div>
  );
}

function PaperCard({ paper, index }) {
  const [expanded, setExpanded] = useState(false);

  const sourceColor = {
    "arXiv": "#f5a623",
    "MIT": "#e74c3c",
    "Harvard": "#9b59b6",
    "IEEE": "#3498db",
    "ACM": "#27ae60",
  };

  const src = paper.source?.split("/")?.[0]?.trim() || paper.source || "—";
  const color = sourceColor[src] || "#666";

  return (
    <div
      style={{
        border: "1px solid #1e1e2e",
        borderLeft: `3px solid ${color}`,
        background: expanded ? "#0f0f1a" : "#0c0c14",
        padding: "16px 20px",
        cursor: "pointer",
        transition: "background 0.1s",
      }}
      onClick={() => setExpanded(!expanded)}
    >
      <div style={{ display: "flex", gap: 12, alignItems: "flex-start" }}>
        <span style={{ color: "#333", fontSize: 10, minWidth: 28, paddingTop: 2 }}>
          {String(index + 1).padStart(2, "0")}
        </span>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 6 }}>
            <span style={{
              color,
              fontSize: 10,
              letterSpacing: 1,
              textTransform: "uppercase",
              border: `1px solid ${color}33`,
              padding: "1px 6px",
            }}>
              {src}
            </span>
            {paper.topicLabel && (
              <span style={{ fontSize: 10, border: "1px solid #1a3a6a", padding: "1px 6px", color: "#4a7aaa" }}>
                {paper.topicLabel}
              </span>
            )}
            {paper.date && (
              <span style={{ color: "#444", fontSize: 10 }}>{paper.date}</span>
            )}
            <span style={{ marginLeft: "auto", color: "#333", fontSize: 10 }}>
              {expanded ? "▲" : "▼"}
            </span>
          </div>
          <div style={{ fontSize: 13, color: "#d8d5d0", lineHeight: 1.5, marginBottom: 4 }}>
            {paper.title || "Untitled"}
          </div>
          {paper.authors && (
            <div style={{ fontSize: 11, color: "#555" }}>{paper.authors}</div>
          )}
          {expanded && (
            <div style={{ marginTop: 14, paddingTop: 14, borderTop: "1px solid #1e1e2e" }}>
              {paper.abstract && (
                <p style={{ fontSize: 12, color: "#888", lineHeight: 1.7, margin: "0 0 12px" }}>
                  {paper.abstract}
                </p>
              )}
              {paper.tags?.length > 0 && (
                <div style={{ display: "flex", gap: 6, flexWrap: "wrap", marginBottom: 12 }}>
                  {paper.tags.map((tag, i) => (
                    <span key={i} style={{
                      fontSize: 10,
                      color: "#556",
                      border: "1px solid #1e1e2e",
                      padding: "2px 8px",
                    }}>
                      {tag}
                    </span>
                  ))}
                </div>
              )}
              {paper.url && (
                <a
                  href={paper.url}
                  target="_blank"
                  rel="noreferrer"
                  onClick={e => e.stopPropagation()}
                  style={{
                    fontSize: 11,
                    color: "#4a9eff",
                    textDecoration: "none",
                    borderBottom: "1px solid #4a9eff44",
                  }}
                >
                  ↗ {paper.url}
                </a>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
