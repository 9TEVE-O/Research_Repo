import React, { useState, useEffect, useRef, useMemo } from 'react';
import {
  Search,
  X,
  BookOpen,
  GitPullRequest,
  ExternalLink,
  Bookmark,
  BookmarkCheck,
  Clock,
  Sparkles,
  ArrowRight,
  Trash2,
} from 'lucide-react';
import { ActiveTab, useFirebase } from '../context/FirebaseContext';
import { Paper } from '../data/papersData';
import { ScoredRepository } from '../data/reposData';

interface GlobalSearchBarProps {
  activeTab: ActiveTab;
  onSelectTab: (tab: ActiveTab) => void;
  globalQuery: string;
  onGlobalQueryChange: (q: string) => void;
}

type SearchScope = 'context' | 'all' | 'papers' | 'repos';

const TAB_CONTEXT_LABELS: Record<ActiveTab, { badge: string; primarySource: 'papers' | 'repos' | 'both'; desc: string }> = {
  terminal: {
    badge: 'CTX: ARXIV & PAPERS',
    primarySource: 'papers',
    desc: 'Prioritizing arXiv & academic papers from current terminal tab',
  },
  discovery: {
    badge: 'CTX: REPOSITORIES',
    primarySource: 'repos',
    desc: 'Prioritizing scored GitHub repositories & policy scans from current tab',
  },
  'knowledge-graph': {
    badge: 'CTX: GRAPH & REPOS',
    primarySource: 'both',
    desc: 'Searching papers & repositories linked to knowledge graph entities',
  },
  typesafe: {
    badge: 'CTX: EVIDENCE SOURCES',
    primarySource: 'both',
    desc: 'Searching verifiable claims across papers & repositories',
  },
  reports: {
    badge: 'CTX: REPORT & PAPERS',
    primarySource: 'both',
    desc: 'Searching daily report repositories & academic whitepapers',
  },
  guardrails: {
    badge: 'CTX: PIPELINE & REPOS',
    primarySource: 'repos',
    desc: 'Searching agent repositories & workflow papers',
  },
};

export const GlobalSearchBar: React.FC<GlobalSearchBarProps> = ({
  activeTab,
  onSelectTab,
  globalQuery,
  onGlobalQueryChange,
}) => {
  const {
    user,
    allPapers,
    allRepositories,
    bookmarks,
    searchHistory,
    isBookmarked,
    toggleBookmark,
    recordSearchQuery,
    deleteSearchHistoryItem,
  } = useFirebase();

  const [isOpen, setIsOpen] = useState(false);
  const [scope, setScope] = useState<SearchScope>('context');
  const containerRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const tabMeta = TAB_CONTEXT_LABELS[activeTab];

  // Global keyboard shortcut Cmd+K / Ctrl+K
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        inputRef.current?.focus();
        setIsOpen(true);
      } else if (e.key === 'Escape') {
        setIsOpen(false);
        inputRef.current?.blur();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  // Close popover when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // Filter arXiv / Academic Papers
  const matchedPapers = useMemo(() => {
    const q = globalQuery.trim().toLowerCase();
    if (!q) return [];
    return allPapers.filter(
      (p) =>
        p.title.toLowerCase().includes(q) ||
        p.abstract.toLowerCase().includes(q) ||
        p.authors.toLowerCase().includes(q) ||
        p.source.toLowerCase().includes(q) ||
        p.topicLabel.toLowerCase().includes(q) ||
        p.tags.some((t) => t.toLowerCase().includes(q))
    );
  }, [allPapers, globalQuery]);

  // Filter Repository Content
  const matchedRepos = useMemo(() => {
    const q = globalQuery.trim().toLowerCase();
    if (!q) return [];
    return allRepositories.filter(
      (r) =>
        r.name.toLowerCase().includes(q) ||
        r.full_name.toLowerCase().includes(q) ||
        r.description.toLowerCase().includes(q) ||
        r.summary.toLowerCase().includes(q) ||
        r.reason.toLowerCase().includes(q) ||
        r.language.toLowerCase().includes(q) ||
        r.topics.some((t) => t.toLowerCase().includes(q)) ||
        r.policy.privacy_summary.toLowerCase().includes(q)
    );
  }, [allRepositories, globalQuery]);

  const handleSearchSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!globalQuery.trim()) return;
    if (user) {
      await recordSearchQuery(globalQuery.trim(), activeTab);
    }
    setIsOpen(true);
  };

  const handleSelectPaper = async (paper: Paper) => {
    if (user && globalQuery.trim()) {
      await recordSearchQuery(globalQuery.trim(), activeTab);
    }
    onSelectTab('terminal');
    setIsOpen(false);
  };

  const handleSelectRepo = async (repo: ScoredRepository) => {
    if (user && globalQuery.trim()) {
      await recordSearchQuery(globalQuery.trim(), activeTab);
    }
    onSelectTab('discovery');
    setIsOpen(false);
  };

  const showPapers =
    scope === 'all' ||
    scope === 'papers' ||
    (scope === 'context' && (tabMeta.primarySource === 'papers' || tabMeta.primarySource === 'both'));

  const showRepos =
    scope === 'all' ||
    scope === 'repos' ||
    (scope === 'context' && (tabMeta.primarySource === 'repos' || tabMeta.primarySource === 'both'));

  // Also show secondary cross-index matches in 'context' mode so users can search across both while prioritizing active tab
  const secondaryPapers = scope === 'context' && tabMeta.primarySource === 'repos' ? matchedPapers : [];
  const secondaryRepos = scope === 'context' && tabMeta.primarySource === 'papers' ? matchedRepos : [];

  return (
    <div ref={containerRef} className="relative flex-1 max-w-xl mx-2 sm:mx-4">
      <form onSubmit={handleSearchSubmit} className="relative flex items-center">
        <Search className="w-3.5 h-3.5 text-[#4a9eff] absolute left-3 pointer-events-none" />
        <input
          ref={inputRef}
          type="text"
          value={globalQuery}
          onFocus={() => setIsOpen(true)}
          onChange={(e) => {
            onGlobalQueryChange(e.target.value);
            if (!isOpen) setIsOpen(true);
          }}
          placeholder={`Search arXiv papers & repos (${tabMeta.badge})...`}
          className="w-full bg-[#090910] border border-[#252538] focus:border-[#4a9eff] text-xs text-[#e8e6e1] pl-8 pr-36 py-1.5 rounded outline-none placeholder-[#555] font-mono transition-all shadow-inner"
        />

        {/* Context Badge & Clear / Shortcut */}
        <div className="absolute right-2 flex items-center gap-1.5">
          {globalQuery && (
            <button
              type="button"
              onClick={() => {
                onGlobalQueryChange('');
                inputRef.current?.focus();
              }}
              className="text-[#666] hover:text-[#ccc] p-0.5"
              title="Clear search"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
          <span
            onClick={() => setIsOpen(true)}
            className="hidden sm:inline-block text-[10px] px-1.5 py-0.5 rounded bg-[#142036] text-[#7ab8ff] border border-[#2b4470] font-mono cursor-pointer select-none"
            title={tabMeta.desc}
          >
            {tabMeta.badge}
          </span>
          <kbd className="hidden lg:inline-block text-[10px] text-[#555] bg-[#11111a] border border-[#222233] px-1 py-0.2 rounded font-mono">
            ⌘K
          </kbd>
        </div>
      </form>

      {/* Dropdown Search Palette */}
      {isOpen && (
        <div className="absolute left-0 right-0 mt-2 bg-[#0c0c14] border border-[#2a2a3a] rounded-md shadow-2xl z-50 max-h-[78vh] flex flex-col overflow-hidden">
          {/* Scope Selector Header */}
          <div className="p-2.5 bg-[#10101a] border-b border-[#1e1e2e] flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-1">
              {(
                [
                  { id: 'context', label: `Active Context (${activeTab})` },
                  { id: 'all', label: 'All Sources' },
                  { id: 'papers', label: `arXiv & Papers (${matchedPapers.length})` },
                  { id: 'repos', label: `Repositories (${matchedRepos.length})` },
                ] as { id: SearchScope; label: string }[]
              ).map((s) => (
                <button
                  key={s.id}
                  type="button"
                  onClick={() => setScope(s.id)}
                  className={`px-2 py-1 text-[10px] font-mono rounded border transition-all ${
                    scope === s.id
                      ? 'bg-[#1a2a4a] border-[#4a9eff] text-[#7ab8ff] font-semibold'
                      : 'bg-[#0c0c14] border-[#222233] text-[#777] hover:text-[#bbb]'
                  }`}
                >
                  {s.label}
                </button>
              ))}
            </div>
            <span className="text-[10px] text-[#555] font-mono hidden sm:inline">
              {tabMeta.desc}
            </span>
          </div>

          {/* Results Body */}
          <div className="overflow-y-auto p-3 space-y-4 divide-y divide-[#181824]">
            {globalQuery.trim() === '' ? (
              /* Empty Query State: Recent Contextual Searches & Saved Bookmarks */
              <div className="space-y-4">
                {/* Recent Searches */}
                <div>
                  <div className="text-[10px] text-[#666] uppercase tracking-widest font-mono mb-2 flex items-center gap-1.5">
                    <Clock className="w-3 h-3 text-[#4a9eff]" />
                    Recent Contextual Searches {user ? '(Synced to Firestore)' : '(Sign in to persist)'}
                  </div>
                  {searchHistory.length > 0 ? (
                    <div className="flex flex-wrap gap-1.5">
                      {searchHistory.slice(0, 8).map((item) => (
                        <div
                          key={item.id}
                          className="inline-flex items-center gap-1.5 px-2.5 py-1 bg-[#11111a] border border-[#232338] hover:border-[#4a9eff] rounded text-xs font-mono group"
                        >
                          <button
                            type="button"
                            onClick={() => {
                              onGlobalQueryChange(item.query);
                              onSelectTab(item.contextTab);
                            }}
                            className="text-[#ccc] group-hover:text-[#7ab8ff] flex items-center gap-1.5"
                          >
                            <span>{item.query}</span>
                            <span className="text-[9px] text-[#555] px-1 bg-[#0a0a0f] rounded">
                              {item.contextTab}
                            </span>
                          </button>
                          <button
                            type="button"
                            onClick={() => deleteSearchHistoryItem(item.id)}
                            className="text-[#444] hover:text-rose-400"
                            title="Remove from history"
                          >
                            <Trash2 className="w-3 h-3" />
                          </button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-xs text-[#555] font-mono">
                      Type above to search across {allPapers.length} academic papers (arXiv, MIT, Harvard, IEEE, ACM) and {allRepositories.length} scored AI repositories.
                    </div>
                  )}
                </div>

                {/* Quick Filter Suggestions */}
                <div className="pt-3">
                  <div className="text-[10px] text-[#666] uppercase tracking-widest font-mono mb-2 flex items-center gap-1.5">
                    <Sparkles className="w-3 h-3 text-amber-400" /> Quick Research Queries
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {['arXiv', 'vLLM', 'multi-agent', 'quantization', 'AutoGen', 'surface-codes', 'guardrails', 'LoRA'].map(
                      (term) => (
                        <button
                          key={term}
                          type="button"
                          onClick={() => onGlobalQueryChange(term)}
                          className="px-2 py-1 text-[11px] font-mono bg-[#111118] border border-[#222233] hover:border-[#4a9eff] text-[#888] hover:text-[#7ab8ff] rounded transition-colors"
                        >
                          #{term}
                        </button>
                      )
                    )}
                  </div>
                </div>

                {/* Saved Bookmarks Preview */}
                {bookmarks.length > 0 && (
                  <div className="pt-3">
                    <div className="text-[10px] text-emerald-400 uppercase tracking-widest font-mono mb-2 flex items-center gap-1.5">
                      <BookmarkCheck className="w-3 h-3" /> Your Saved Bookmarks ({bookmarks.length})
                    </div>
                    <div className="space-y-1.5">
                      {bookmarks.slice(0, 4).map((bm) => (
                        <div
                          key={bm.id}
                          className="p-2 bg-[#101018] border border-[#1e1e2e] rounded flex items-center justify-between text-xs font-mono"
                        >
                          <div className="truncate pr-2">
                            <span className="text-[9px] uppercase px-1.5 py-0.5 rounded bg-[#1a2a4a] text-[#7ab8ff] mr-2">
                              {bm.itemType}
                            </span>
                            <span className="text-[#ddd]">{bm.title}</span>
                          </div>
                          <a
                            href={bm.url}
                            target="_blank"
                            rel="noreferrer"
                            className="text-[#4a9eff] hover:underline shrink-0 flex items-center gap-1 text-[11px]"
                          >
                            Open <ExternalLink className="w-3 h-3" />
                          </a>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : (
              /* Active Query Results */
              <>
                {/* Primary Context Section: If activeTab === 'discovery', show Repositories first; else show Papers first */}
                {tabMeta.primarySource === 'repos' ? (
                  <>
                    {showRepos && (
                      <RepoResultsSection
                        repos={matchedRepos}
                        isPrimaryContext={scope === 'context'}
                        onSelectRepo={handleSelectRepo}
                        userSignedIn={!!user}
                        isBookmarked={isBookmarked}
                        onToggleBookmark={toggleBookmark}
                      />
                    )}
                    {showPapers && (
                      <PaperResultsSection
                        papers={matchedPapers}
                        isPrimaryContext={false}
                        onSelectPaper={handleSelectPaper}
                        userSignedIn={!!user}
                        isBookmarked={isBookmarked}
                        onToggleBookmark={toggleBookmark}
                      />
                    )}
                    {secondaryPapers.length > 0 && (
                      <PaperResultsSection
                        papers={secondaryPapers}
                        isPrimaryContext={false}
                        onSelectPaper={handleSelectPaper}
                        userSignedIn={!!user}
                        isBookmarked={isBookmarked}
                        onToggleBookmark={toggleBookmark}
                      />
                    )}
                  </>
                ) : (
                  <>
                    {showPapers && (
                      <PaperResultsSection
                        papers={matchedPapers}
                        isPrimaryContext={scope === 'context'}
                        onSelectPaper={handleSelectPaper}
                        userSignedIn={!!user}
                        isBookmarked={isBookmarked}
                        onToggleBookmark={toggleBookmark}
                      />
                    )}
                    {showRepos && (
                      <RepoResultsSection
                        repos={matchedRepos}
                        isPrimaryContext={scope === 'context' && tabMeta.primarySource === 'both'}
                        onSelectRepo={handleSelectRepo}
                        userSignedIn={!!user}
                        isBookmarked={isBookmarked}
                        onToggleBookmark={toggleBookmark}
                      />
                    )}
                    {secondaryRepos.length > 0 && (
                      <RepoResultsSection
                        repos={secondaryRepos}
                        isPrimaryContext={false}
                        onSelectRepo={handleSelectRepo}
                        userSignedIn={!!user}
                        isBookmarked={isBookmarked}
                        onToggleBookmark={toggleBookmark}
                      />
                    )}
                  </>
                )}

                {matchedPapers.length === 0 && matchedRepos.length === 0 && (
                  <div className="py-8 text-center text-xs text-[#666] font-mono">
                    No matching arXiv papers or repositories found for "{globalQuery}".
                  </div>
                )}
              </>
            )}
          </div>

          {/* Footer Bar */}
          <div className="px-3 py-2 bg-[#090910] border-t border-[#1e1e2e] flex items-center justify-between text-[10px] text-[#666] font-mono">
            <span>
              Matches: <strong className="text-[#4a9eff]">{matchedPapers.length}</strong> papers ·{' '}
              <strong className="text-emerald-400">{matchedRepos.length}</strong> repositories
            </span>
            <span>Press Enter to log search · Esc to close</span>
          </div>
        </div>
      )}
    </div>
  );
};

interface PaperResultsSectionProps {
  papers: Paper[];
  isPrimaryContext: boolean;
  onSelectPaper: (paper: Paper) => void;
  userSignedIn: boolean;
  isBookmarked: (id: string) => boolean;
  onToggleBookmark: (item: {
    itemId: string;
    itemType: 'paper' | 'repository';
    title: string;
    sourceOrLanguage: string;
    url: string;
  }) => Promise<void>;
}

const PaperResultsSection: React.FC<PaperResultsSectionProps> = ({
  papers,
  isPrimaryContext,
  onSelectPaper,
  userSignedIn,
  isBookmarked,
  onToggleBookmark,
}) => {
  if (papers.length === 0) return null;
  return (
    <div className="pt-2 first:pt-0">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] text-[#4a9eff] uppercase tracking-widest font-mono font-semibold flex items-center gap-1.5">
          <BookOpen className="w-3.5 h-3.5" />
          arXiv & Academic Papers ({papers.length})
        </span>
        {isPrimaryContext && (
          <span className="text-[9px] px-1.5 py-0.5 bg-[#142036] text-[#7ab8ff] border border-[#2b4470] rounded font-mono">
            ACTIVE TAB CONTEXT
          </span>
        )}
      </div>
      <div className="space-y-1.5">
        {papers.slice(0, 6).map((paper) => {
          const saved = isBookmarked(paper.id);
          return (
            <div
              key={paper.id}
              onClick={() => onSelectPaper(paper)}
              className="p-2.5 bg-[#10101a] hover:bg-[#161a2c] border border-[#1e1e2e] hover:border-[#4a9eff] rounded cursor-pointer transition-all flex items-start justify-between gap-3"
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-[9px] uppercase px-1.5 py-0.5 rounded bg-amber-950/50 text-amber-400 border border-amber-700/40 font-mono">
                    {paper.source}
                  </span>
                  <span className="text-[10px] text-[#7ab8ff] font-mono">{paper.topicLabel}</span>
                  <span className="text-[10px] text-[#555] font-mono">{paper.date}</span>
                </div>
                <div className="text-xs text-[#f0ede8] font-medium truncate">{paper.title}</div>
                <div className="text-[11px] text-[#777] truncate">{paper.authors}</div>
              </div>

              <div className="flex items-center gap-1.5 shrink-0">
                {userSignedIn && (
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onToggleBookmark({
                        itemId: paper.id,
                        itemType: 'paper',
                        title: paper.title,
                        sourceOrLanguage: paper.source,
                        url: paper.url,
                      });
                    }}
                    className={`p-1.5 rounded border transition-colors ${
                      saved
                        ? 'bg-emerald-950/60 border-emerald-600 text-emerald-400'
                        : 'bg-[#0c0c14] border-[#2a2a3a] text-[#666] hover:text-[#ccc]'
                    }`}
                    title={saved ? 'Remove bookmark' : 'Bookmark paper to Firestore'}
                  >
                    {saved ? <BookmarkCheck className="w-3.5 h-3.5" /> : <Bookmark className="w-3.5 h-3.5" />}
                  </button>
                )}
                <ArrowRight className="w-3.5 h-3.5 text-[#555]" />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

interface RepoResultsSectionProps {
  repos: ScoredRepository[];
  isPrimaryContext: boolean;
  onSelectRepo: (repo: ScoredRepository) => void;
  userSignedIn: boolean;
  isBookmarked: (id: string) => boolean;
  onToggleBookmark: (item: {
    itemId: string;
    itemType: 'paper' | 'repository';
    title: string;
    sourceOrLanguage: string;
    url: string;
  }) => Promise<void>;
}

const RepoResultsSection: React.FC<RepoResultsSectionProps> = ({
  repos,
  isPrimaryContext,
  onSelectRepo,
  userSignedIn,
  isBookmarked,
  onToggleBookmark,
}) => {
  if (repos.length === 0) return null;
  return (
    <div className="pt-3 first:pt-0">
      <div className="flex items-center justify-between mb-2">
        <span className="text-[10px] text-emerald-400 uppercase tracking-widest font-mono font-semibold flex items-center gap-1.5">
          <GitPullRequest className="w-3.5 h-3.5" />
          Scored Repositories & Content ({repos.length})
        </span>
        {isPrimaryContext && (
          <span className="text-[9px] px-1.5 py-0.5 bg-emerald-950/60 text-emerald-400 border border-emerald-700/50 rounded font-mono">
            ACTIVE TAB CONTEXT
          </span>
        )}
      </div>
      <div className="space-y-1.5">
        {repos.slice(0, 6).map((repo) => {
          const saved = isBookmarked(repo.id);
          return (
            <div
              key={repo.id}
              onClick={() => onSelectRepo(repo)}
              className="p-2.5 bg-[#10101a] hover:bg-[#14221e] border border-[#1e1e2e] hover:border-emerald-500/60 rounded cursor-pointer transition-all flex items-start justify-between gap-3"
            >
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs text-[#4a9eff] font-mono font-semibold">
                    {repo.full_name}
                  </span>
                  <span className="text-[10px] px-1.5 py-0.2 rounded bg-emerald-950/60 border border-emerald-600/50 text-emerald-400 font-mono">
                    ⭐ {repo.relevance_score}/100
                  </span>
                  <span className="text-[10px] text-[#777] font-mono">{repo.language}</span>
                </div>
                <div className="text-xs text-[#ccc] truncate">{repo.description}</div>
              </div>

              <div className="flex items-center gap-1.5 shrink-0">
                {userSignedIn && (
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      onToggleBookmark({
                        itemId: repo.id,
                        itemType: 'repository',
                        title: repo.full_name,
                        sourceOrLanguage: repo.language,
                        url: repo.url,
                      });
                    }}
                    className={`p-1.5 rounded border transition-colors ${
                      saved
                        ? 'bg-emerald-950/60 border-emerald-600 text-emerald-400'
                        : 'bg-[#0c0c14] border-[#2a2a3a] text-[#666] hover:text-[#ccc]'
                    }`}
                    title={saved ? 'Remove bookmark' : 'Bookmark repository to Firestore'}
                  >
                    {saved ? <BookmarkCheck className="w-3.5 h-3.5" /> : <Bookmark className="w-3.5 h-3.5" />}
                  </button>
                )}
                <ArrowRight className="w-3.5 h-3.5 text-[#555]" />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
