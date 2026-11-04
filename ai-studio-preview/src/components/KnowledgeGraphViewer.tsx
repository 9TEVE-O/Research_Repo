import React, { useState, useMemo } from "react";
import { INITIAL_NODES, INITIAL_TRIPLES, INITIAL_CLUSTERS, KGNode, KGTriple, EntityType, PrivacyLevel } from "../data/knowledgeGraphData";
import { Network, ShieldCheck, Database, Filter, Search, Plus, CheckCircle, Clock, Link2, ExternalLink } from "lucide-react";

export const KnowledgeGraphViewer: React.FC = () => {
  const [nodes, setNodes] = useState<KGNode[]>(INITIAL_NODES);
  const [triples, setTriples] = useState<KGTriple[]>(INITIAL_TRIPLES);
  const [selectedCluster, setSelectedCluster] = useState<string>("all");
  const [selectedType, setSelectedType] = useState<string>("all");
  const [selectedPrivacy, setSelectedPrivacy] = useState<string>("all");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [activeTriple, setActiveTriple] = useState<KGTriple | null>(null);

  // New triple form
  const [newSubj, setNewSubj] = useState<string>(INITIAL_NODES[0].id);
  const [newPred, setNewPred] = useState<string>("integrates_with");
  const [newObj, setNewObj] = useState<string>(INITIAL_NODES[1].id);
  const [newQuote, setNewQuote] = useState<string>("");
  const [newSource, setNewSource] = useState<string>("");

  const filteredNodes = useMemo(() => {
    return nodes.filter((n) => {
      if (selectedCluster !== "all" && n.cluster !== selectedCluster) return false;
      if (selectedType !== "all" && n.type !== selectedType) return false;
      if (selectedPrivacy !== "all" && n.privacy !== selectedPrivacy) return false;
      if (searchQuery.trim()) {
        const q = searchQuery.toLowerCase();
        return n.name.toLowerCase().includes(q) || n.description.toLowerCase().includes(q);
      }
      return true;
    });
  }, [nodes, selectedCluster, selectedType, selectedPrivacy, searchQuery]);

  const filteredNodeIds = useMemo(() => new Set(filteredNodes.map((n) => n.id)), [filteredNodes]);

  const filteredTriples = useMemo(() => {
    return triples.filter((t) => filteredNodeIds.has(t.subject) && filteredNodeIds.has(t.object));
  }, [triples, filteredNodeIds]);

  const handleAddTriple = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSubj || !newObj || !newPred) return;

    const newTrip: KGTriple = {
      id: `trip-${Date.now()}`,
      subject: newSubj,
      predicate: newPred,
      object: newObj,
      evidence: {
        source: newSource || "User manual assertion / retrieval pipeline",
        timestamp: new Date().toISOString().replace("T", " ").slice(0, 19),
        confidence: 0.96,
        quote: newQuote || `Direct semantic relation verified between ${newSubj} and ${newObj}.`,
        pageOrUrl: "Interactive Knowledge Graph Entry",
      },
    };

    setTriples([newTrip, ...triples]);
    setNewQuote("");
    setNewSource("");
  };

  const entityTypeColors: Record<EntityType, { bg: string; text: string; border: string }> = {
    repository: { bg: "bg-blue-950/60", text: "text-blue-400", border: "border-blue-700/50" },
    topic: { bg: "bg-emerald-950/60", text: "text-emerald-400", border: "border-emerald-700/50" },
    workflow: { bg: "bg-amber-950/60", text: "text-amber-400", border: "border-amber-700/50" },
    document: { bg: "bg-purple-950/60", text: "text-purple-400", border: "border-purple-700/50" },
    tool: { bg: "bg-cyan-950/60", text: "text-cyan-400", border: "border-cyan-700/50" },
    policy: { bg: "bg-rose-950/60", text: "text-rose-400", border: "border-rose-700/50" },
    risk: { bg: "bg-red-950/60", text: "text-red-400", border: "border-red-700/50" },
    organization: { bg: "bg-indigo-950/60", text: "text-indigo-400", border: "border-indigo-700/50" },
    claim: { bg: "bg-teal-950/60", text: "text-teal-400", border: "border-teal-700/50" },
  };

  const privacyBadgeColors: Record<PrivacyLevel, string> = {
    public: "text-emerald-400 border-emerald-800 bg-emerald-950/30",
    internal: "text-amber-400 border-amber-800 bg-amber-950/30",
    restricted: "text-rose-400 border-rose-800 bg-rose-950/30",
    confidential: "text-red-500 border-red-800 bg-red-950/40",
  };

  const getNode = (id: string) => nodes.find((n) => n.id === id);

  return (
    <div className="w-full">
      {/* Header */}
      <div className="border-b border-[#2a2a3a] px-6 py-6 bg-gradient-to-b from-[#0f0f1a] to-[#0a0a0f]">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[#a78bfa] text-xs font-semibold tracking-widest uppercase">
              ◈ KNOWLEDGE_GRAPH // RETRIEVAL & AUDIT ENGINE
            </span>
            <span className="text-[#555] text-xs">models.py · graph.py · retrieval.py · audit.py</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-normal text-[#f0ede8]">
            Knowledge Graph & Evidence Audit
          </h1>
          <p className="text-[#888] text-xs sm:text-sm mt-1">
            Semantic entity triples, privacy-bounded subgraphs, and provenance evidence tracking
          </p>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* Filters and Search Bar */}
        <div className="p-4 bg-[#0c0c14] border border-[#1e1e2e] rounded mb-6 flex flex-wrap items-center gap-3">
          {/* Cluster filter */}
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-[#666] tracking-wider uppercase font-mono">Cluster:</span>
            <select
              value={selectedCluster}
              onChange={(e) => setSelectedCluster(e.target.value)}
              className="bg-[#111118] border border-[#2a2a3a] text-xs text-[#ddd] px-2 py-1.5 rounded outline-none font-mono"
            >
              <option value="all">All Clusters</option>
              {INITIAL_CLUSTERS.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.label}
                </option>
              ))}
            </select>
          </div>

          {/* Type filter */}
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-[#666] tracking-wider uppercase font-mono">Type:</span>
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="bg-[#111118] border border-[#2a2a3a] text-xs text-[#ddd] px-2 py-1.5 rounded outline-none font-mono"
            >
              <option value="all">All Entity Types</option>
              {["repository", "topic", "workflow", "document", "tool", "policy", "risk", "organization"].map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>

          {/* Privacy filter */}
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-[#666] tracking-wider uppercase font-mono">Privacy:</span>
            <select
              value={selectedPrivacy}
              onChange={(e) => setSelectedPrivacy(e.target.value)}
              className="bg-[#111118] border border-[#2a2a3a] text-xs text-[#ddd] px-2 py-1.5 rounded outline-none font-mono"
            >
              <option value="all">All Privacy Levels</option>
              {["public", "internal", "restricted", "confidential"].map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </div>

          {/* Search box */}
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#555]" />
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search graph entities..."
              className="w-full bg-[#111118] border border-[#2a2a3a] text-xs text-[#ddd] pl-8 pr-3 py-1.5 rounded outline-none focus:border-[#4a9eff] font-mono"
            />
          </div>
        </div>

        {/* Visual Graph Nodes Grid */}
        <div className="mb-8">
          <div className="text-xs text-[#888] font-mono uppercase tracking-widest mb-3 flex items-center justify-between">
            <span>GRAPH ENTITIES ({filteredNodes.length} NODES)</span>
            <span className="text-[#555]">Click a node to inspect connected relationships</span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-3">
            {filteredNodes.map((node) => {
              const cluster = INITIAL_CLUSTERS.find((c) => c.id === node.cluster);
              const typeStyle = entityTypeColors[node.type] || entityTypeColors.tool;
              return (
                <div
                  key={node.id}
                  className="p-3.5 bg-[#0c0c14] border border-[#1e1e2e] hover:border-[#4a9eff] rounded transition-all flex flex-col justify-between"
                >
                  <div>
                    <div className="flex items-center justify-between gap-1 mb-2">
                      <span
                        className={`text-[9px] uppercase tracking-wider px-1.5 py-0.5 border rounded font-mono ${typeStyle.bg} ${typeStyle.text} ${typeStyle.border}`}
                      >
                        {node.type}
                      </span>
                      <span
                        className={`text-[9px] uppercase px-1.5 py-0.5 border rounded font-mono ${
                          privacyBadgeColors[node.privacy]
                        }`}
                      >
                        {node.privacy}
                      </span>
                    </div>

                    <div className="text-sm font-semibold text-[#f0ede8] mb-1">
                      {node.name}
                    </div>

                    <p className="text-[11px] text-[#888] leading-snug mb-3">
                      {node.description}
                    </p>
                  </div>

                  <div className="pt-2 border-t border-[#181824] flex items-center justify-between text-[10px] text-[#555] font-mono">
                    <span style={{ color: cluster?.color }}>● {cluster?.label}</span>
                    <span>id: {node.id.replace("node-", "")}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Semantic Triples & Provenance Evidence Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Triples List */}
          <div className="col-span-2 bg-[#0c0c14] border border-[#1e1e2e] rounded p-5">
            <div className="text-xs text-[#7ab8ff] font-semibold tracking-wider uppercase mb-3 flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Network className="w-4 h-4 text-[#4a9eff]" /> Semantic Triples (Subject → Predicate → Object)
              </span>
              <span className="text-[#555] font-mono">{filteredTriples.length} relationships</span>
            </div>

            <div className="space-y-2.5">
              {filteredTriples.map((trip) => {
                const s = getNode(trip.subject);
                const o = getNode(trip.object);
                const isSelected = activeTriple?.id === trip.id;
                return (
                  <div
                    key={trip.id}
                    onClick={() => setActiveTriple(trip)}
                    className={`p-3.5 border rounded transition-all cursor-pointer ${
                      isSelected
                        ? "bg-[#141b2b] border-[#4a9eff]"
                        : "bg-[#090910] border-[#1f1f2e] hover:border-[#333348]"
                    }`}
                  >
                    <div className="flex flex-wrap items-center gap-2 font-mono text-xs mb-2">
                      <span className="px-2 py-0.5 bg-[#172033] border border-[#2b3a5c] text-[#7ab8ff] rounded font-semibold">
                        {s?.name || trip.subject}
                      </span>
                      <span className="text-amber-400 font-bold px-1.5">
                        --[{trip.predicate}]--&gt;
                      </span>
                      <span className="px-2 py-0.5 bg-[#172033] border border-[#2b3a5c] text-[#7ab8ff] rounded font-semibold">
                        {o?.name || trip.object}
                      </span>

                      <span className="ml-auto text-[10px] text-emerald-400 border border-emerald-900 bg-emerald-950/40 px-2 py-0.5 rounded">
                        conf: {(trip.evidence.confidence * 100).toFixed(0)}%
                      </span>
                    </div>

                    <div className="text-[11px] text-[#777] italic truncate">
                      "{trip.evidence.quote}"
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Evidence Inspector / Provenance Record */}
          <div className="col-span-1 bg-[#0c0c14] border border-[#1e1e2e] rounded p-5">
            <div className="text-xs text-emerald-400 font-semibold tracking-wider uppercase mb-3 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-emerald-400" /> Evidence Audit Inspector
            </div>

            {activeTriple ? (
              <div className="space-y-4 font-mono text-xs">
                <div>
                  <div className="text-[10px] text-[#555] uppercase mb-1">Triple ID:</div>
                  <div className="text-[#ddd] bg-[#11111a] p-2 border border-[#222233] rounded">
                    {activeTriple.id}
                  </div>
                </div>

                <div>
                  <div className="text-[10px] text-[#555] uppercase mb-1">Source Citation:</div>
                  <div className="text-[#7ab8ff] bg-[#11111a] p-2 border border-[#222233] rounded break-all">
                    {activeTriple.evidence.source}
                  </div>
                </div>

                <div>
                  <div className="text-[10px] text-[#555] uppercase mb-1">Confidence Score:</div>
                  <div className="text-emerald-400 bg-[#11111a] p-2 border border-[#222233] rounded font-bold">
                    {(activeTriple.evidence.confidence * 100).toFixed(1)}% verified
                  </div>
                </div>

                <div>
                  <div className="text-[10px] text-[#555] uppercase mb-1">Provenance Quote:</div>
                  <div className="text-[#ccc] bg-[#11111a] p-2.5 border border-[#222233] rounded font-sans leading-relaxed text-xs">
                    "{activeTriple.evidence.quote}"
                  </div>
                </div>

                {activeTriple.evidence.pageOrUrl && (
                  <div>
                    <div className="text-[10px] text-[#555] uppercase mb-1">Location / Anchor:</div>
                    <div className="text-[#888] bg-[#11111a] p-2 border border-[#222233] rounded truncate">
                      {activeTriple.evidence.pageOrUrl}
                    </div>
                  </div>
                )}

                <div>
                  <div className="text-[10px] text-[#555] uppercase mb-1">Extraction Timestamp:</div>
                  <div className="text-[#666] text-[11px] flex items-center gap-1.5">
                    <Clock className="w-3 h-3 text-[#555]" />
                    {activeTriple.evidence.timestamp} UTC
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-8 text-center text-xs text-[#555] border border-dashed border-[#222233] rounded">
                Select any triple from the list to audit its provenance evidence, confidence metrics, and quote citations.
              </div>
            )}
          </div>
        </div>

        {/* Add Triple Form */}
        <div className="p-5 bg-[#0c0c14] border border-[#1e1e2e] rounded">
          <div className="text-xs text-[#aaa] font-semibold tracking-wider uppercase mb-3 flex items-center gap-2">
            <Plus className="w-3.5 h-3.5 text-[#4a9eff]" /> Assert Verified Semantic Triple
          </div>
          <form onSubmit={handleAddTriple} className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-3">
            <div>
              <label className="text-[10px] text-[#555] uppercase font-mono block mb-1">Subject Node</label>
              <select
                value={newSubj}
                onChange={(e) => setNewSubj(e.target.value)}
                className="w-full bg-[#111118] border border-[#2a2a3a] text-xs text-[#ddd] px-3 py-2 rounded outline-none font-mono"
              >
                {nodes.map((n) => (
                  <option key={n.id} value={n.id}>
                    {n.name} ({n.type})
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-[10px] text-[#555] uppercase font-mono block mb-1">Predicate</label>
              <input
                type="text"
                value={newPred}
                onChange={(e) => setNewPred(e.target.value)}
                placeholder="e.g. implements, regulates, optimizes"
                className="w-full bg-[#111118] border border-[#2a2a3a] text-xs text-[#ddd] px-3 py-2 rounded outline-none font-mono"
              />
            </div>

            <div>
              <label className="text-[10px] text-[#555] uppercase font-mono block mb-1">Object Node</label>
              <select
                value={newObj}
                onChange={(e) => setNewObj(e.target.value)}
                className="w-full bg-[#111118] border border-[#2a2a3a] text-xs text-[#ddd] px-3 py-2 rounded outline-none font-mono"
              >
                {nodes.map((n) => (
                  <option key={n.id} value={n.id}>
                    {n.name} ({n.type})
                  </option>
                ))}
              </select>
            </div>

            <div className="md:col-span-2">
              <label className="text-[10px] text-[#555] uppercase font-mono block mb-1">Evidence Quote / Excerpt</label>
              <input
                type="text"
                value={newQuote}
                onChange={(e) => setNewQuote(e.target.value)}
                placeholder="Verbatim quote from document or README..."
                className="w-full bg-[#111118] border border-[#2a2a3a] text-xs text-[#ddd] px-3 py-2 rounded outline-none font-mono"
              />
            </div>

            <div>
              <label className="text-[10px] text-[#555] uppercase font-mono block mb-1">Source / Citation</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newSource}
                  onChange={(e) => setNewSource(e.target.value)}
                  placeholder="e.g. SOSP '25 paper"
                  className="w-full bg-[#111118] border border-[#2a2a3a] text-xs text-[#ddd] px-3 py-2 rounded outline-none font-mono"
                />
                <button
                  type="submit"
                  className="px-4 py-2 bg-[#1a2a4a] border border-[#4a9eff] text-[#7ab8ff] text-xs font-mono uppercase tracking-wider rounded hover:bg-[#203660] whitespace-nowrap"
                >
                  Link
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};
