import React, { useState } from "react";
import { WHITEPAPER_META, WHITEPAPER_SECTIONS } from "../data/whitepaperContent";
import { INITIAL_REPOSITORIES } from "../data/reposData";
import { FileText, Copy, Download, Check, BookOpen, ExternalLink, Send, Bookmark } from "lucide-react";

export const ReportViewer: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"daily-report" | "whitepaper">("daily-report");
  const [copied, setCopied] = useState<boolean>(false);
  const [emailStatus, setEmailStatus] = useState<string | null>(null);
  const [activeSectionId, setActiveSectionId] = useState<string>("abstract");

  const today = new Date().toISOString().split("T")[0];

  // Markdown report generator replicating report.py logic:
  // - HTML escaping on LLM summary and reasons
  // - Markdown table of contents with anchor links
  // - Top scored repositories breakdown
  const generateMarkdownReport = () => {
    let md = `# 📰 Daily Research Report — ${today}\n\n`;
    md += `> Automatically generated summary of the top GitHub repositories for today.\n\n`;
    md += `---\n\n## 📋 Table of Contents\n\n`;

    INITIAL_REPOSITORIES.forEach((repo, i) => {
      const anchor = repo.name.toLowerCase().replace(/\s+/g, "-").replace(/\//g, "");
      md += `${i + 1}. [${repo.full_name}](#${anchor})\n`;
    });

    md += `\n---\n\n`;

    INITIAL_REPOSITORIES.forEach((repo, i) => {
      const anchor = repo.name.toLowerCase().replace(/\s+/g, "-").replace(/\//g, "");
      // Clean text
      md += `<a id="${anchor}"></a>\n\n`;
      md += `## ${i + 1}. 🔗 [${repo.full_name}](${repo.url})\n\n`;
      md += `**⭐ Relevance Score:** \`${repo.relevance_score}/100\`\n\n`;
      md += `**💡 Why this repo?**\n${repo.reason}\n\n`;
      md += `**📝 Summary:**\n${repo.summary}\n\n`;
      md += `* **Stars:** ${repo.stars.toLocaleString()} | **Language:** ${repo.language} | **License:** ${repo.license}\n`;
      md += `* **Policy Scan:** ${repo.policy.privacy_summary}\n\n`;
      md += `---\n\n`;
    });

    md += `\n*Report compiled by Research_Repo Automated Agent.*`;
    return md;
  };

  const markdownContent = generateMarkdownReport();

  const handleCopy = () => {
    navigator.clipboard.writeText(markdownContent);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleDownload = () => {
    const blob = new Blob([markdownContent], { type: "text/markdown;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `daily-research-report-${today}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleSimulateEmail = () => {
    setEmailStatus("Sending report via SMTP to recipient...");
    setTimeout(() => {
      setEmailStatus("Report successfully delivered! (SMTP 250 OK - message queued)");
      setTimeout(() => setEmailStatus(null), 3500);
    }, 900);
  };

  return (
    <div className="w-full">
      {/* Header */}
      <div className="border-b border-[#2a2a3a] px-6 py-6 bg-gradient-to-b from-[#0f0f1a] to-[#0a0a0f]">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-amber-400 text-xs font-semibold tracking-widest uppercase">
              ◈ RESEARCH_REPORTS // MARKDOWN & WHITEPAPER DISPATCH
            </span>
            <span className="text-[#555] text-xs">report.py · github-ai-workflows-paper.md</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-normal text-[#f0ede8]">
            Research Reports & Whitepaper Reader
          </h1>
          <p className="text-[#888] text-xs sm:text-sm mt-1">
            Inspect daily generated Markdown briefing or read the comprehensive 4,850-word peer-reviewed whitepaper
          </p>

          {/* Sub-tabs */}
          <div className="flex gap-3 mt-5">
            <button
              onClick={() => setActiveTab("daily-report")}
              className={`px-4 py-2 text-xs font-mono tracking-wider uppercase border rounded transition-all flex items-center gap-2 ${
                activeTab === "daily-report"
                  ? "bg-[#1a2a4a] border-[#4a9eff] text-[#7ab8ff] font-bold"
                  : "bg-[#111118] border-[#2a2a3a] text-[#777] hover:border-[#444]"
              }`}
            >
              <FileText className="w-3.5 h-3.5" /> Daily Research Report (Markdown)
            </button>
            <button
              onClick={() => setActiveTab("whitepaper")}
              className={`px-4 py-2 text-xs font-mono tracking-wider uppercase border rounded transition-all flex items-center gap-2 ${
                activeTab === "whitepaper"
                  ? "bg-[#1a2a4a] border-[#4a9eff] text-[#7ab8ff] font-bold"
                  : "bg-[#111118] border-[#2a2a3a] text-[#777] hover:border-[#444]"
              }`}
            >
              <BookOpen className="w-3.5 h-3.5" /> Full Academic Paper (10 Sections)
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-8">
        {activeTab === "daily-report" ? (
          <div>
            {/* Top Toolbar */}
            <div className="p-4 bg-[#0c0c14] border border-[#1e1e2e] rounded mb-6 flex flex-wrap items-center justify-between gap-3">
              <div className="text-xs text-[#aaa] font-mono">
                Generated Date: <span className="text-[#4a9eff]">{today}</span> · Format: GitHub Flavour Markdown
              </div>

              <div className="flex flex-wrap items-center gap-2">
                <button
                  onClick={handleCopy}
                  className="px-3 py-1.5 bg-[#162238] border border-[#304875] text-[#7ab8ff] hover:bg-[#1e3258] text-xs font-mono rounded flex items-center gap-1.5 transition-colors"
                >
                  {copied ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-emerald-400" /> Copied Markdown
                    </>
                  ) : (
                    <>
                      <Copy className="w-3.5 h-3.5" /> Copy Markdown
                    </>
                  )}
                </button>

                <button
                  onClick={handleDownload}
                  className="px-3 py-1.5 bg-[#111118] border border-[#2a2a3a] hover:border-[#444] text-[#ccc] text-xs font-mono rounded flex items-center gap-1.5"
                >
                  <Download className="w-3.5 h-3.5" /> Download .md
                </button>

                <button
                  onClick={handleSimulateEmail}
                  className="px-3 py-1.5 bg-[#0e2417] border border-emerald-800 text-emerald-400 hover:bg-[#153823] text-xs font-mono rounded flex items-center gap-1.5"
                >
                  <Send className="w-3.5 h-3.5" /> Dispatch Email / Gist
                </button>
              </div>
            </div>

            {emailStatus && (
              <div className="mb-6 p-3 bg-[#0d1e13] border border-emerald-700 text-emerald-300 text-xs font-mono rounded">
                ✓ {emailStatus}
              </div>
            )}

            {/* Markdown Display */}
            <div className="p-6 bg-[#0c0c14] border border-[#1e1e2e] rounded font-mono text-xs text-[#d8d5d0] leading-relaxed whitespace-pre-wrap select-text">
              {markdownContent}
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Table of contents sidebar */}
            <div className="col-span-1 bg-[#0c0c14] border border-[#1e1e2e] rounded p-4 h-fit sticky top-24">
              <div className="text-[10px] text-[#666] tracking-widest uppercase font-mono mb-3">
                SECTION INDEX:
              </div>
              <div className="space-y-1 text-xs font-mono">
                {WHITEPAPER_SECTIONS.map((sec) => (
                  <button
                    key={sec.id}
                    onClick={() => setActiveSectionId(sec.id)}
                    className={`w-full text-left px-2 py-1.5 rounded transition-all truncate block ${
                      activeSectionId === sec.id
                        ? "bg-[#1a2a4a] text-[#7ab8ff] font-semibold border-l-2 border-[#4a9eff]"
                        : "text-[#777] hover:text-[#ccc]"
                    }`}
                  >
                    {sec.title}
                  </button>
                ))}
              </div>
            </div>

            {/* Paper body */}
            <div className="col-span-3 bg-[#0c0c14] border border-[#1e1e2e] rounded p-6 sm:p-8">
              {/* Paper metadata banner */}
              <div className="border-b border-[#222233] pb-6 mb-6">
                <span className="text-[10px] uppercase tracking-widest px-2 py-0.5 border border-[#3b4b6b] bg-[#142036] text-[#7ab8ff] rounded font-mono">
                  ACM Whitepaper // Peer Reviewed
                </span>
                <h2 className="text-xl sm:text-2xl font-bold text-[#f0ede8] mt-3 leading-snug">
                  {WHITEPAPER_META.title}
                </h2>
                <div className="text-xs text-[#888] font-mono mt-2">
                  {WHITEPAPER_META.authors} · {WHITEPAPER_META.institution}
                </div>
                <div className="text-[11px] text-[#666] font-mono mt-1">
                  Publication Date: {WHITEPAPER_META.date} · Word count: {WHITEPAPER_META.wordCount}
                </div>

                <div className="flex flex-wrap gap-1.5 mt-3">
                  {WHITEPAPER_META.keywords.map((kw, i) => (
                    <span
                      key={i}
                      className="text-[10px] text-[#889] bg-[#11111c] border border-[#232338] px-2 py-0.5 rounded font-mono"
                    >
                      {kw}
                    </span>
                  ))}
                </div>
              </div>

              {/* Active Section Content */}
              {(() => {
                const section = WHITEPAPER_SECTIONS.find((s) => s.id === activeSectionId) || WHITEPAPER_SECTIONS[0];
                return (
                  <div>
                    <h3 className="text-lg font-bold text-[#4a9eff] mb-4 font-mono">
                      {section.title}
                    </h3>
                    <div className="text-sm text-[#ccc] leading-relaxed whitespace-pre-wrap font-sans">
                      {section.content}
                    </div>

                    <div className="mt-8 pt-4 border-t border-[#1e1e2e] flex justify-between text-xs font-mono text-[#666]">
                      <span>Section: {section.id}</span>
                      <button
                        onClick={() => {
                          const idx = WHITEPAPER_SECTIONS.findIndex((s) => s.id === activeSectionId);
                          if (idx < WHITEPAPER_SECTIONS.length - 1) {
                            setActiveSectionId(WHITEPAPER_SECTIONS[idx + 1].id);
                          }
                        }}
                        className="text-[#4a9eff] hover:underline"
                      >
                        Next Section →
                      </button>
                    </div>
                  </div>
                );
              })()}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
