import React, { useState, useMemo } from "react";
import { useFirebase } from "../context/FirebaseContext";
import {
  Play,
  Star,
  GitFork,
  ShieldAlert,
  CheckCircle2,
  Sliders,
  ExternalLink,
  Plus,
  AlertTriangle,
  Bookmark,
  BookmarkCheck,
} from "lucide-react";

interface RepoScoringPipelineProps {
  globalQuery?: string;
}

export const RepoScoringPipeline: React.FC<RepoScoringPipelineProps> = ({ globalQuery = "" }) => {
  const { user, allRepositories, addCustomRepo, isBookmarked, toggleBookmark } = useFirebase();

  const [scoreThreshold, setScoreThreshold] = useState<number>(50);
  const [topK, setTopK] = useState<number>(5);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [currentStep, setCurrentStep] = useState<number>(0);

  // New candidate form
  const [newRepoName, setNewRepoName] = useState("");
  const [newRepoDesc, setNewRepoDesc] = useState("");
  const [newRepoTopics, setNewRepoTopics] = useState("");

  const pipelineSteps = [
    { name: "Example Input", desc: "Reading bundled sample repository records, no GitHub API call" },
    { name: "Example Filter", desc: "Filtering sample fields; stars and licences are not verified" },
    { name: "Simulated Scores", desc: "Displaying example scores; no model is invoked" },
    { name: "Top-K Selection", desc: `Filtering candidates with score > ${scoreThreshold} (max ${topK})` },
    { name: "Example Policy Notes", desc: "Viewing synthetic policy notes; no scan performed" },
    { name: "Demo Summary", desc: "Displaying a local example, not a research briefing" },
  ];

  const runPipeline = async () => {
    setIsRunning(true);
    for (let step = 0; step < pipelineSteps.length; step++) {
      setCurrentStep(step);
      await new Promise((r) => setTimeout(r, 450));
    }
    setIsRunning(false);
  };

  // Top-k filtered candidates based on selector.py logic + globalQuery filtering
  const qualifyingRepos = useMemo(() => {
    const q = globalQuery.trim().toLowerCase();
    return allRepositories
      .filter((r) => r.relevance_score > scoreThreshold)
      .filter((r) => {
        if (!q) return true;
        return (
          r.name.toLowerCase().includes(q) ||
          r.full_name.toLowerCase().includes(q) ||
          r.description.toLowerCase().includes(q) ||
          r.summary.toLowerCase().includes(q) ||
          r.reason.toLowerCase().includes(q) ||
          r.language.toLowerCase().includes(q) ||
          r.topics.some((t) => t.toLowerCase().includes(q)) ||
          r.policy.privacy_summary.toLowerCase().includes(q)
        );
      })
      .sort((a, b) => b.relevance_score - a.relevance_score)
      .slice(0, topK);
  }, [allRepositories, scoreThreshold, topK, globalQuery]);

  const handleAddCandidate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRepoName.trim()) return;

    const simulatedScore = 0; // A manually added candidate has not been scored.
    const topicsArr = newRepoTopics
      .split(",")
      .map((t) => t.trim())
      .filter(Boolean);

    await addCustomRepo({
      name: newRepoName.split("/").pop() || newRepoName,
      full_name: newRepoName.includes("/") ? newRepoName : `ai-lab/${newRepoName}`,
      url: `https://github.com/${newRepoName}`,
      description: newRepoDesc || "Automated AI agent candidate for research evaluation.",
      relevance_score: simulatedScore,
      summary: `Unverified example candidate: ${newRepoName}. No source inspection performed.`,
      reason: "Unscored: no provider or local verification performed.",
      stars: 0, // Unknown; placeholder is not an observed star count
      forks: 0, // Unknown; placeholder is not an observed fork count
      language: "Python",
      license: "Unverified",
      topics: topicsArr.length > 0 ? topicsArr : ["ai", "agents", "llm"],
      updated_at: new Date().toISOString().split("T")[0],
      policy: {
        privacy_summary: "Not assessed. No privacy or security scan performed.",
        severity_counts: { high: 0, medium: 0, low: 0 },
        third_party_mentions: [],
        data_sharing_references: [],
        detected_technologies: [],
      },
    });

    setNewRepoName("");
    setNewRepoDesc("");
    setNewRepoTopics("");
  };

  return (
    <div className="w-full">
      {/* Header */}
      <div className="border-b border-[#2a2a3a] px-6 py-6 bg-gradient-to-b from-[#0f0f1a] to-[#0a0a0f]">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-emerald-400 text-xs font-semibold tracking-widest uppercase">
              ◈ RESEARCH_AGENT // SCORING & SELECTION PIPELINE
            </span>
            <span className="text-[#555] text-xs">agent.py · scoring.py · selector.py</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-normal text-[#f0ede8]">
            AI Repository Discovery & Scoring
          </h1>
          <p className="text-[#888] text-xs sm:text-sm mt-1">
            Simulated data only. No live GitHub search, LLM relevance scoring, or verified policy analysis.
          </p>
          <p role="status" className="mt-3 rounded border border-amber-700/50 bg-amber-950/30 p-3 text-xs text-amber-200">
            SIMULATED DATA · Repository rankings, scores, stars, licences and policy notes are unverified examples. This preview does not call GitHub, run an LLM, or scan repository contents.
          </p>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* Pipeline Controls & Status */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Controls Box */}
          <div className="p-5 bg-[#0c0c14] border border-[#1e1e2e] rounded col-span-1">
            <div className="text-xs text-[#7ab8ff] font-semibold tracking-wider uppercase mb-4 flex items-center gap-2">
              <Sliders className="w-4 h-4 text-[#4a9eff]" /> Pipeline Parameters
            </div>

            {/* Threshold Slider */}
            <div className="mb-4">
              <div className="flex justify-between text-xs text-[#aaa] mb-1 font-mono">
                <span>Score Threshold:</span>
                <span className="text-[#4a9eff] font-bold">{scoreThreshold}/100</span>
              </div>
              <input
                type="range"
                min="0"
                max="95"
                step="5"
                value={scoreThreshold}
                onChange={(e) => setScoreThreshold(Number(e.target.value))}
                className="w-full accent-[#4a9eff] cursor-pointer"
              />
              <div className="text-[10px] text-[#555] mt-1">
                Candidates with score ≤ threshold are excluded per selector.py
              </div>
            </div>

            {/* Top-K Selector */}
            <div className="mb-5">
              <div className="flex justify-between text-xs text-[#aaa] mb-1 font-mono">
                <span>Top-K Limit:</span>
                <span className="text-[#4a9eff] font-bold">{topK} repos</span>
              </div>
              <div className="flex gap-2">
                {[3, 5, 8, 10].map((k) => (
                  <button
                    key={k}
                    onClick={() => setTopK(k)}
                    className={`flex-1 py-1.5 text-xs font-mono border rounded ${
                      topK === k
                        ? "bg-[#1a2a4a] border-[#4a9eff] text-[#7ab8ff] font-bold"
                        : "bg-[#111118] border-[#2a2a3a] text-[#777] hover:border-[#444]"
                    }`}
                  >
                    K={k}
                  </button>
                ))}
              </div>
            </div>

            {/* Trigger Button */}
            <button
              onClick={runPipeline}
              disabled={isRunning}
              className={`w-full py-3 border text-xs tracking-widest uppercase font-semibold transition-all rounded flex items-center justify-center gap-2 ${
                isRunning
                  ? "bg-[#162a1a] border-emerald-500 text-emerald-400"
                  : "bg-[#0a2a5a] border-[#4a9eff] text-[#4a9eff] hover:bg-[#103875] hover:text-white cursor-pointer"
              }`}
            >
              <Play className={`w-3.5 h-3.5 ${isRunning ? "animate-pulse" : ""}`} />
              {isRunning ? "Running Simulation..." : "Run Simulated Pipeline"}
            </button>
          </div>

          {/* Stepper Display */}
          <div className="p-5 bg-[#0c0c14] border border-[#1e1e2e] rounded col-span-2">
            <div className="text-xs text-[#7ab8ff] font-semibold tracking-wider uppercase mb-4 flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" /> Pipeline Execution Lifecycle
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {pipelineSteps.map((step, idx) => {
                const isPast = idx < currentStep;
                const isCurrent = isRunning && idx === currentStep;
                return (
                  <div
                    key={idx}
                    className={`p-3 border rounded text-xs transition-all ${
                      isCurrent
                        ? "bg-[#1a2a4a] border-[#4a9eff] text-white shadow-[0_0_10px_rgba(74,158,255,0.2)]"
                        : isPast
                        ? "bg-[#0e1610] border-emerald-900 text-emerald-300"
                        : "bg-[#111118] border-[#222233] text-[#666]"
                    }`}
                  >
                    <div className="flex items-center gap-2 font-mono font-semibold mb-1">
                      <span className="text-[10px] w-4 h-4 rounded-full border border-current flex items-center justify-center">
                        {idx + 1}
                      </span>
                      <span>{step.name}</span>
                      {isPast && <span className="text-emerald-400 text-[10px] ml-auto">PASS ✓</span>}
                      {isCurrent && <span className="text-[#4a9eff] text-[10px] ml-auto animate-pulse">RUNNING...</span>}
                    </div>
                    <div className="text-[11px] opacity-80 leading-relaxed">
                      {step.desc}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* Ingest custom repo testbed */}
        <div className="mb-8 p-4 bg-[#0d0d16] border border-[#232338] rounded">
          <div className="text-xs text-[#aaa] font-semibold tracking-wider uppercase mb-3 flex items-center justify-between">
            <span className="flex items-center gap-2">
              <Plus className="w-3.5 h-3.5 text-[#4a9eff]" /> Inject Candidate for Scoring Test
            </span>
            <span className="text-[10px] text-[#666] font-mono">
              {user ? "Synced to Firestore customRepos" : "Local session mode"}
            </span>
          </div>
          <form onSubmit={handleAddCandidate} className="grid grid-cols-1 md:grid-cols-4 gap-3">
            <input
              type="text"
              placeholder="repo (e.g. meta-llama/llama3)"
              value={newRepoName}
              onChange={(e) => setNewRepoName(e.target.value)}
              className="bg-[#0a0a0f] border border-[#2a2a3a] text-xs text-[#e8e6e1] px-3 py-2 rounded outline-none focus:border-[#4a9eff] font-mono"
            />
            <input
              type="text"
              placeholder="Description..."
              value={newRepoDesc}
              onChange={(e) => setNewRepoDesc(e.target.value)}
              className="bg-[#0a0a0f] border border-[#2a2a3a] text-xs text-[#e8e6e1] px-3 py-2 rounded outline-none focus:border-[#4a9eff] font-mono md:col-span-2"
            />
            <div className="flex gap-2">
              <input
                type="text"
                placeholder="topics (ai, agents)"
                value={newRepoTopics}
                onChange={(e) => setNewRepoTopics(e.target.value)}
                className="bg-[#0a0a0f] border border-[#2a2a3a] text-xs text-[#e8e6e1] px-3 py-2 rounded outline-none focus:border-[#4a9eff] font-mono flex-1"
              />
              <button
                type="submit"
                disabled={!newRepoName.trim()}
                className="px-4 py-2 bg-[#1a2a4a] border border-[#4a9eff] text-[#7ab8ff] text-xs font-mono uppercase tracking-wider rounded hover:bg-[#203660] disabled:opacity-40"
              >
                Score
              </button>
            </div>
          </form>
        </div>

        {/* Qualifying Repositories Output */}
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          <div className="text-xs text-[#888] font-mono uppercase tracking-widest">
            SAMPLE CANDIDATES (UNVERIFIED SCORE &gt; {scoreThreshold}) — {qualifyingRepos.length} SELECTED (TOP {topK})
            {globalQuery && (
              <span className="ml-2 text-[#4a9eff]">
                [FILTERED BY GLOBAL SEARCH: "{globalQuery}"]
              </span>
            )}
          </div>
          <div className="text-xs text-[#555] font-mono">
            Total Ingested: {allRepositories.length}
          </div>
        </div>

        {/* Repos Grid */}
        <div className="grid grid-cols-1 gap-4">
          {qualifyingRepos.map((repo, i) => {
            const bookmarked = isBookmarked(repo.id);
            return (
              <div
                key={repo.id}
                className="p-5 bg-[#0c0c14] border border-[#1e1e2e] hover:border-[#2a2a3a] rounded transition-all"
              >
                <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
                  <div className="flex-1">
                    {/* Top line with score badge */}
                    <div className="flex flex-wrap items-center gap-3 mb-2">
                      <span className="text-xs font-mono text-[#555] font-bold">
                        #{i + 1}
                      </span>
                      <a
                        href={repo.url}
                        target="_blank"
                        rel="noreferrer"
                        className="text-base text-[#4a9eff] hover:underline font-medium font-mono flex items-center gap-1.5"
                      >
                        {repo.full_name}
                        <ExternalLink className="w-3.5 h-3.5" />
                      </a>

                      {/* Score badge */}
                      <span
                        className={`text-xs px-2.5 py-0.5 border rounded font-mono font-bold ${
                          repo.relevance_score >= 90
                            ? "bg-emerald-950/60 border-emerald-500 text-emerald-400"
                            : repo.relevance_score >= 70
                            ? "bg-blue-950/60 border-blue-500 text-blue-400"
                            : "bg-amber-950/60 border-amber-500 text-amber-400"
                        }`}
                      >
                        ⭐ {repo.relevance_score}/100
                      </span>

                      <span className="text-[11px] text-[#888] border border-[#2a2a3a] px-2 py-0.5 rounded font-mono">
                        {repo.language}
                      </span>
                      <span className="text-[11px] text-[#666] font-mono">
                        {repo.license}
                      </span>

                      {user && (
                        <button
                          type="button"
                          onClick={() =>
                            toggleBookmark({
                              itemId: repo.id,
                              itemType: "repository",
                              title: repo.full_name,
                              sourceOrLanguage: repo.language,
                              url: repo.url,
                            })
                          }
                          className={`ml-auto px-2.5 py-0.5 text-[11px] border rounded font-mono flex items-center gap-1 transition-colors ${
                            bookmarked
                              ? "bg-emerald-950/60 border-emerald-600 text-emerald-400"
                              : "bg-[#111118] border-[#2a2a3a] text-[#777] hover:text-[#ccc]"
                          }`}
                        >
                          {bookmarked ? (
                            <>
                              <BookmarkCheck className="w-3 h-3" /> Bookmarked
                            </>
                          ) : (
                            <>
                              <Bookmark className="w-3 h-3" /> Bookmark
                            </>
                          )}
                        </button>
                      )}
                    </div>

                    {/* Summary */}
                    <p className="text-xs sm:text-sm text-[#ccc] leading-relaxed mb-3 font-sans">
                      {repo.summary}
                    </p>

                    {/* Reason */}
                    <div className="p-3 bg-[#11111a] border-l-2 border-[#4a9eff] rounded-r text-xs text-[#8bb4db] mb-3 font-mono">
                      <span className="font-semibold text-[#4a9eff]">💡 Why this repo? </span>
                      {repo.reason}
                    </div>

                    {/* Topics and stats */}
                    <div className="flex flex-wrap items-center gap-3 text-xs text-[#666] font-mono">
                      <span className="flex items-center gap-1 text-[#aaa]">
                        <Star className="w-3.5 h-3.5 text-amber-400" />
                        {repo.stars.toLocaleString()}
                      </span>
                      <span className="flex items-center gap-1 text-[#aaa]">
                        <GitFork className="w-3.5 h-3.5" />
                        {repo.forks.toLocaleString()}
                      </span>
                      <span className="text-[#444]">|</span>
                      {repo.topics.map((t, idx) => (
                        <span key={idx} className="text-[#667] text-[11px]">
                          #{t}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Policy & Terms Box */}
                  <div className="w-full md:w-72 bg-[#09090f] p-3.5 border border-[#1a1a28] rounded">
                    <div className="text-[10px] text-[#888] tracking-widest uppercase font-mono mb-2 flex items-center justify-between">
                      <span className="flex items-center gap-1">
                        <ShieldAlert className="w-3 h-3 text-amber-400" /> POLICY SCAN
                      </span>
                      <span className="text-[#555]">policy_analysis.py</span>
                    </div>
                    <div className="text-xs text-[#aaa] font-sans leading-tight mb-2">
                      {repo.policy.privacy_summary}
                    </div>
                    <div className="flex items-center gap-2 text-[10px] font-mono mb-2">
                      <span className="text-rose-400">High: {repo.policy.severity_counts.high}</span>
                      <span className="text-amber-400">Med: {repo.policy.severity_counts.medium}</span>
                      <span className="text-emerald-400">Low: {repo.policy.severity_counts.low}</span>
                    </div>
                    {repo.policy.third_party_mentions.length > 0 && (
                      <div className="text-[10px] text-[#556] truncate font-mono">
                        Deps: {repo.policy.third_party_mentions.join(", ")}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}

          {qualifyingRepos.length === 0 && (
            <div className="p-12 text-center border border-[#1e1e2e] bg-[#0c0c14] rounded">
              <AlertTriangle className="w-8 h-8 text-amber-400 mx-auto mb-3" />
              <div className="text-sm text-[#ccc] mb-1">
                {globalQuery
                  ? `No repositories matched "${globalQuery}" above threshold ${scoreThreshold}`
                  : `No repositories qualified above score threshold ${scoreThreshold}`}
              </div>
              <p className="text-xs text-[#666]">
                Per selector.py rules, candidates with score ≤ threshold are excluded. Lower the threshold slider or clear the global search query.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
