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

function safeUrl(url) {
  return typeof url === 'string' && /^https:\/\//i.test(url) ? url : null;
}

function normaliseTitle(title) {
  return (title || '')
    .toLowerCase()
    .replace(/[^\w\s]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

function generateBibtex(papers) {
  return papers.map(paper => {
    const firstAuthor = (paper.authors || '').split(',')[0].trim();
    const lastName = firstAuthor.split(' ').pop() || 'Unknown';
    const year = (paper.date || '').match(/\d{4}/)?.[0] || 'XXXX';
    const key = `${lastName}${year}`;
    const esc = s => (s || '').replace(/[{}\\]/g, '\\$&');
    const note = [
      paper.abstract ? `Abstract: ${paper.abstract}` : '',
      paper.source   ? `Source: ${paper.source}`     : '',
    ].filter(Boolean).join('. ');
    return [
      `@misc{${key},`,
      `  title  = {${esc(paper.title)}},`,
      `  author = {${esc(paper.authors)}},`,
      `  year   = {${year}},`,
      paper.url ? `  url    = {${paper.url}},` : null,
      `  note   = {${esc(note)}}`,
      `}`,
    ].filter(line => line !== null).join('\n');
  }).join('\n\n');
}

export default function App() {
  const [selectedTopics, setSelectedTopics] = useState([]);
  const [papers, setPapers] = useState([]);
  const [topicStatus, setTopicStatus] = useState({});
  const [topicErrors, setTopicErrors] = useState({});
  const [activeFilter, setActiveFilter] = useState("all");
  const [searchedTopics, setSearchedTopics] = useState([]);

  const loading = Object.values(topicStatus).some(s => s === 'loading');

  const toggleTopic = (id) => {
    setSelectedTopics(prev =>
      prev.includes(id) ? prev.filter(t => t !== id) : [...prev, id]
    );
  };

  const fetchPapers = useCallback(async () => {
    if (selectedTopics.length === 0) return;

    const initialStatus = {};
    selectedTopics.forEach(id => { initialStatus[id] = 'idle'; });
    setTopicStatus(initialStatus);
    setTopicErrors({});
    setPapers([]);
    setSearchedTopics([...selectedTopics]);

    const topicsToFetch = TOPICS.filter(t => selectedTopics.includes(t.id));

    for (const topic of topicsToFetch) {
      setTopicStatus(prev => ({ ...prev, [topic.id]: 'loading' }));
      try {
        const response = await fetch("/api/papers", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ topicLabel: topic.label }),
        });

        if (!response.ok) {
          const err = await response.json().catch(() => ({}));
          throw new Error(err.error || `HTTP ${response.status}`);
        }

        const { papers: fetched = [] } = await response.json();
        const tagged = fetched.map((p, i) => ({
          ...p,
          id: `${topic.id}-${i}`,
          topic: topic.id,
          topicLabel: topic.label,
        }));

        setPapers(prev => {
          const seen = new Set(prev.map(p => normaliseTitle(p.title)));
          const unique = tagged.filter(p => {
            const norm = normaliseTitle(p.title);
            if (seen.has(norm)) return false;
            seen.add(norm);
            return true;
          });
          return [...prev, ...unique];
        });

        setTopicStatus(prev => ({ ...prev, [topic.id]: 'done' }));
      } catch (err) {
        console.error(`Failed to fetch ${topic.label}:`, err);
        setTopicStatus(prev => ({ ...prev, [topic.id]: 'error' }));
        setTopicErrors(prev => ({ ...prev, [topic.id]: err.message }));
      }
    }
  }, [selectedTopics]);

  const filtered = activeFilter === "all"
    ? papers
    : papers.filter(p => p.topic === activeFilter);

  const topicCounts = papers.reduce((acc, p) => {
    acc[p.topic] = (acc[p.topic] || 0) + 1;
    return acc;
  }, {});

  const exportBibtex = useCallback(() => {
    const bib = generateBibtex(filtered);
    const blob = new Blob([bib], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'papers.bib';
    a.click();
    URL.revokeObjectURL(url);
  }, [filtered]);

  return (
    <div style={{
      minHeight: "100vh",
      background: "#0a0a0f",
      color: "#e8e6e1",
      fontFamily: "'Courier New', 'Lucida Console', monospace",
      padding: "0",
    }}>
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
            <span style={{ color: "#444", fontSize: 10 }}>v2.2 // academic intelligence layer</span>
          </div>
          <h1 style={{ margin: 0, fontSize: 26, fontWeight: "normal", color: "#f0ede8", letterSpacing: 1 }}>
            Academic Paper Intelligence
          </h1>
          <p style={{ margin: "6px 0 0", color: "#666", fontSize: 12, letterSpacing: 0.5 }}>
            arXiv · MIT · Harvard · IEEE · ACM — live retrieval
          </p>
          <p style={{ margin: "6px 0 0", color: "#5a4a2a", fontSize: 10, letterSpacing: 0.3 }}>
            ⚠ AI-generated results — always verify papers independently before citing
          </p>
        </div>
      </div>

      <div style={{ maxWidth: 1100, margin: "0 auto", padding: "32px 40px" }}>
        <div style={{ marginBottom: 32 }}>
          <div style={{ fontSize: 10, color: "#555", letterSpacing: 3, textTransform: "uppercase", marginBottom: 14 }}>
            ▸ SELECT RESEARCH DOMAINS
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 10 }}>
            {TOPICS.map(topic => {
              const active = selectedTopics.includes(topic.id);
              const status = topicStatus[topic.id];
              const icon = status === 'loading' ? '⟳'
                         : status === 'done'    ? '✓'
                         : status === 'error'   ? '✕'
                         : active               ? '■'
                                                : '□';
              const iconColor = status === 'done'    ? '#4a9a4a'
                              : status === 'error'   ? '#ff6b6b'
                              : status === 'loading' ? '#f5a623'
                              : undefined;
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
                  <span style={{ color: iconColor }}>{icon}</span>
                  {' '}{topic.label}
                </button>
              );
            })}
          </div>
        </div>

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
            <span style={{ marginLeft: 16, color: "#444", fontSize: 11 }}>select at least one domain</span>
          )}
        </div>

        {papers.length > 0 && (
          <>
            <div style={{ marginBottom: 12, display: "flex", gap: 8, flexWrap: "wrap", alignItems: "center" }}>
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
              <button
                onClick={exportBibtex}
                style={{
                  marginLeft: "auto",
                  padding: "4px 16px",
                  background: "#0a1a0a",
                  border: "1px solid #2a6a2a",
                  color: "#4a9a4a",
                  cursor: "pointer",
                  fontSize: 11,
                  letterSpacing: 2,
                  textTransform: "uppercase",
                  fontFamily: "inherit",
                }}
              >
                ↓ EXPORT .BIB ({filtered.length})
              </button>
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 2, marginTop: 12 }}>
              {filtered.map((paper, i) => (
                <PaperCard key={paper.id || i} paper={paper} index={i} />
              ))}
            </div>
          </>
        )}

        {!loading && papers.length === 0 && selectedTopics.length > 0 && (
          <div style={{ color: "#444", fontSize: 13, padding: "40px 0", textAlign: "center" }}>
            Press FETCH PAPERS to retrieve results
          </div>
        )}

        {Object.entries(topicErrors).map(([topicId, msg]) => {
          const topic = TOPICS.find(t => t.id === topicId);
          return (
            <div key={topicId} style={{
              padding: "10px 16px",
              border: "1px solid #5a1a1a",
              background: "#1a0a0a",
              color: "#ff6b6b",
              fontSize: 11,
              marginTop: 8,
            }}>
              ✕ {topic?.label ?? topicId}: {msg}
            </div>
          );
        })}
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
  const hasEvidence = paper.evidence_map?.length > 0;
  const href = safeUrl(paper.url);

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
          <div style={{ display: "flex", gap: 10, alignItems: "center", marginBottom: 6, flexWrap: "wrap" }}>
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
            <span style={{
              fontSize: 9,
              color: hasEvidence ? "#4a6a3a" : "#4a3a2a",
              border: `1px solid ${hasEvidence ? "#2a4a1a" : "#3a2a1a"}`,
              padding: "1px 6px",
              letterSpacing: 0.5,
            }}>
              {hasEvidence ? `● ${paper.evidence_map.length} source${paper.evidence_map.length !== 1 ? 's' : ''}` : '○ unverified'}
            </span>
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

              {hasEvidence && (
                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: 9, color: "#4a6a3a", letterSpacing: 2, textTransform: "uppercase", marginBottom: 6 }}>
                    SEARCH EVIDENCE
                  </div>
                  {paper.evidence_map.map((snippet, i) => (
                    <div key={i} style={{
                      fontSize: 11,
                      color: "#667",
                      borderLeft: "2px solid #2a4a1a",
                      paddingLeft: 10,
                      marginBottom: 6,
                      lineHeight: 1.5,
                      fontStyle: "italic",
                    }}>
                      "{snippet}"
                    </div>
                  ))}
                </div>
              )}

              {!hasEvidence && (
                <div style={{ fontSize: 10, color: "#5a3a1a", marginBottom: 12, padding: "6px 10px", border: "1px solid #3a2a1a", background: "#1a1008" }}>
                  ⚠ No web search results confirmed this paper — verify independently before use
                </div>
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

              {href && (
                <a
                  href={href}
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
                  ↗ {href}
                </a>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
