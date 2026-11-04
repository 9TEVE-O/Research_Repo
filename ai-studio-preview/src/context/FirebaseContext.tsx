import React, { createContext, useContext, useEffect, useState, useCallback, useMemo } from 'react';
import {
  User,
  onAuthStateChanged,
  signInWithPopup,
  signOut,
} from 'firebase/auth';
import {
  collection,
  doc,
  getDoc,
  setDoc,
  updateDoc,
  deleteDoc,
  query,
  where,
  onSnapshot,
  serverTimestamp,
} from 'firebase/firestore';
import {
  auth,
  db,
  googleProvider,
  handleFirestoreError,
  OperationType,
} from '../firebase';
import { INITIAL_PAPERS, Paper } from '../data/papersData';
import { INITIAL_REPOSITORIES, ScoredRepository } from '../data/reposData';

export type ActiveTab =
  | 'terminal'
  | 'discovery'
  | 'knowledge-graph'
  | 'typesafe'
  | 'reports'
  | 'guardrails';

export interface BookmarkRecord {
  id: string;
  ownerId: string;
  itemId: string;
  itemType: 'paper' | 'repository';
  title: string;
  sourceOrLanguage: string;
  url: string;
  notes: string;
  createdAt?: unknown;
  updatedAt?: unknown;
}

export interface SearchHistoryRecord {
  id: string;
  ownerId: string;
  query: string;
  contextTab: ActiveTab;
  createdAt?: unknown;
}

// Validation constants synchronized verbatim with firebase-blueprint.json & firestore.rules
export const ID_PATTERN = /^[a-zA-Z0-9_\-]+$/;
export const MAX_ID_LEN = 128;
export const MAX_DISPLAY_NAME_LEN = 100;
export const MAX_TITLE_LEN = 300;
export const MAX_URL_LEN = 500;
export const MAX_NOTES_LEN = 500;
export const MAX_ABSTRACT_LEN = 1000;
export const MAX_SUMMARY_LEN = 1000;
export const MAX_REASON_LEN = 500;
export const MAX_QUERY_LEN = 200;
export const ALLOWED_TABS: ActiveTab[] = [
  'terminal',
  'discovery',
  'knowledge-graph',
  'typesafe',
  'reports',
  'guardrails',
];

function sanitizeId(raw: string): string {
  const cleaned = raw.replace(/[^a-zA-Z0-9_\-]/g, '_').slice(0, MAX_ID_LEN);
  return cleaned.length >= 1 ? cleaned : `id_${Date.now()}`;
}

function clampString(val: string | undefined | null, minLen: number, maxLen: number, fallback = 'N/A'): string {
  const trimmed = (val ?? '').trim();
  const base = trimmed.length < minLen ? fallback : trimmed;
  return base.slice(0, maxLen);
}

interface FirebaseContextValue {
  user: User | null;
  authReady: boolean;
  profileReady: boolean;
  authError: string | null;
  signInWithGoogle: () => Promise<void>;
  signOutUser: () => Promise<void>;
  bookmarks: BookmarkRecord[];
  customPapers: Paper[];
  customRepos: ScoredRepository[];
  allPapers: Paper[];
  allRepositories: ScoredRepository[];
  searchHistory: SearchHistoryRecord[];
  isBookmarked: (itemId: string) => boolean;
  toggleBookmark: (item: {
    itemId: string;
    itemType: 'paper' | 'repository';
    title: string;
    sourceOrLanguage: string;
    url: string;
    notes?: string;
  }) => Promise<void>;
  updateBookmarkNotes: (bookmarkId: string, notes: string) => Promise<void>;
  addCustomPaper: (paper: Omit<Paper, 'id'>) => Promise<void>;
  deleteCustomPaper: (paperId: string) => Promise<void>;
  addCustomRepo: (repo: Omit<ScoredRepository, 'id'>) => Promise<void>;
  deleteCustomRepo: (repoId: string) => Promise<void>;
  recordSearchQuery: (queryText: string, contextTab: ActiveTab) => Promise<void>;
  deleteSearchHistoryItem: (searchId: string) => Promise<void>;
}

const FirebaseContext = createContext<FirebaseContextValue | undefined>(undefined);

export const FirebaseProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [authReady, setAuthReady] = useState<boolean>(false);
  const [profileReady, setProfileReady] = useState<boolean>(false);
  const [authError, setAuthError] = useState<string | null>(null);

  const [bookmarks, setBookmarks] = useState<BookmarkRecord[]>([]);
  const [customPapers, setCustomPapers] = useState<Paper[]>([]);
  const [customRepos, setCustomRepos] = useState<ScoredRepository[]>([]);
  const [searchHistory, setSearchHistory] = useState<SearchHistoryRecord[]>([]);

  // Local session fallback when signed out
  const [localPapers, setLocalPapers] = useState<Paper[]>([]);
  const [localRepos, setLocalRepos] = useState<ScoredRepository[]>([]);

  // 1. Track Firebase Auth state and bootstrap /users/{userId}
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (currentUser) => {
      setUser(currentUser);
      setAuthReady(true);
      setAuthError(null);

      if (!currentUser) {
        setProfileReady(false);
        setBookmarks([]);
        setCustomPapers([]);
        setCustomRepos([]);
        setSearchHistory([]);
        return;
      }

      const uid = sanitizeId(currentUser.uid);
      const userDocPath = `users/${uid}`;
      const userRef = doc(db, 'users', uid);

      try {
        const snap = await getDoc(userRef);
        if (!snap.exists()) {
          await setDoc(userRef, {
            ownerId: uid,
            displayName: clampString(currentUser.displayName || 'Researcher', 1, MAX_DISPLAY_NAME_LEN, 'Researcher'),
            activeTabPreference: 'terminal',
            createdAt: serverTimestamp(),
            updatedAt: serverTimestamp(),
          });
        }
        setProfileReady(true);
      } catch (err) {
        handleFirestoreError(err, OperationType.WRITE, userDocPath);
      }
    });

    return () => unsubscribe();
  }, []);

  // 2. Attach Firestore real-time listeners once authenticated and profile exists
  useEffect(() => {
    if (!authReady || !user || !profileReady) return;
    const uid = sanitizeId(user.uid);

    // Bookmarks listener
    const bookmarksQuery = query(collection(db, 'bookmarks'), where('ownerId', '==', uid));
    const unsubBookmarks = onSnapshot(
      bookmarksQuery,
      (snapshot) => {
        const items: BookmarkRecord[] = snapshot.docs.map((d) => {
          const data = d.data();
          return {
            id: d.id,
            ownerId: String(data.ownerId || ''),
            itemId: String(data.itemId || ''),
            itemType: data.itemType === 'repository' ? 'repository' : 'paper',
            title: String(data.title || ''),
            sourceOrLanguage: String(data.sourceOrLanguage || ''),
            url: String(data.url || ''),
            notes: String(data.notes || ''),
            createdAt: data.createdAt,
            updatedAt: data.updatedAt,
          };
        });
        setBookmarks(items);
      },
      (err) => {
        handleFirestoreError(err, OperationType.LIST, 'bookmarks');
      }
    );

    // Custom Papers listener
    const papersQuery = query(collection(db, 'customPapers'), where('ownerId', '==', uid));
    const unsubPapers = onSnapshot(
      papersQuery,
      (snapshot) => {
        const items: Paper[] = snapshot.docs.map((d) => {
          const data = d.data();
          return {
            id: d.id,
            topic: String(data.topic || 'ai'),
            topicLabel: String(data.topicLabel || 'Artificial Intelligence'),
            title: String(data.title || 'Untitled'),
            authors: String(data.authors || 'Unknown'),
            source: String(data.source || 'arXiv'),
            date: String(data.date || '2026'),
            abstract: String(data.abstract || ''),
            url: String(data.url || 'https://arxiv.org'),
            doi: String(data.doi || ''),
            tags: [String(data.topic || 'ai'), 'custom-persisted', 'firestore'],
            citations: 1,
          };
        });
        setCustomPapers(items);
      },
      (err) => {
        handleFirestoreError(err, OperationType.LIST, 'customPapers');
      }
    );

    // Custom Repos listener
    const reposQuery = query(collection(db, 'customRepos'), where('ownerId', '==', uid));
    const unsubRepos = onSnapshot(
      reposQuery,
      (snapshot) => {
        const items: ScoredRepository[] = snapshot.docs.map((d) => {
          const data = d.data();
          return {
            id: d.id,
            name: String(data.name || ''),
            full_name: String(data.full_name || ''),
            url: String(data.url || ''),
            description: String(data.description || ''),
            relevance_score: Number(data.relevance_score ?? 75),
            summary: String(data.summary || ''),
            reason: String(data.reason || ''),
            language: String(data.language || 'Python'),
            stars: 1000,
            forks: 120,
            license: 'MIT',
            topics: ['ai', 'custom-persisted'],
            updated_at: new Date().toISOString().split('T')[0],
            policy: {
              privacy_summary: 'Persisted user-evaluated repository candidate.',
              severity_counts: { high: 0, medium: 0, low: 0 },
              third_party_mentions: ['GitHub'],
              data_sharing_references: ['None'],
              detected_technologies: [String(data.language || 'Python')],
            },
          };
        });
        setCustomRepos(items);
      },
      (err) => {
        handleFirestoreError(err, OperationType.LIST, 'customRepos');
      }
    );

    // Search History listener
    const historyQuery = query(collection(db, 'searchHistory'), where('ownerId', '==', uid));
    const unsubHistory = onSnapshot(
      historyQuery,
      (snapshot) => {
        const items: SearchHistoryRecord[] = snapshot.docs.map((d) => {
          const data = d.data();
          return {
            id: d.id,
            ownerId: String(data.ownerId || ''),
            query: String(data.query || ''),
            contextTab: ALLOWED_TABS.includes(data.contextTab) ? data.contextTab : 'terminal',
            createdAt: data.createdAt,
          };
        });
        setSearchHistory(items);
      },
      (err) => {
        handleFirestoreError(err, OperationType.LIST, 'searchHistory');
      }
    );

    return () => {
      unsubBookmarks();
      unsubPapers();
      unsubRepos();
      unsubHistory();
    };
  }, [authReady, user, profileReady]);

  const signInWithGoogle = useCallback(async () => {
    setAuthError(null);
    try {
      await signInWithPopup(auth, googleProvider);
    } catch (err) {
      setAuthError(err instanceof Error ? err.message : 'Sign-in failed');
    }
  }, []);

  const signOutUser = useCallback(async () => {
    setAuthError(null);
    try {
      await signOut(auth);
    } catch (err) {
      setAuthError(err instanceof Error ? err.message : 'Sign-out failed');
    }
  }, []);

  const isBookmarked = useCallback(
    (itemId: string) => {
      const cleanId = sanitizeId(itemId);
      return bookmarks.some((b) => b.itemId === cleanId);
    },
    [bookmarks]
  );

  const toggleBookmark = useCallback(
    async (item: {
      itemId: string;
      itemType: 'paper' | 'repository';
      title: string;
      sourceOrLanguage: string;
      url: string;
      notes?: string;
    }) => {
      if (!user || !profileReady) return;
      const uid = sanitizeId(user.uid);
      const cleanItemId = sanitizeId(item.itemId);
      const docId = sanitizeId(`${uid}_${cleanItemId}`);
      const existingBookmark = bookmarks.find((b) => b.itemId === cleanItemId);

      if (existingBookmark) {
        const path = `bookmarks/${existingBookmark.id}`;
        try {
          await deleteDoc(doc(db, 'bookmarks', existingBookmark.id));
        } catch (err) {
          handleFirestoreError(err, OperationType.DELETE, path);
        }
      } else {
        const path = `bookmarks/${docId}`;
        try {
          await setDoc(doc(db, 'bookmarks', docId), {
            ownerId: uid,
            itemId: cleanItemId,
            itemType: item.itemType === 'repository' ? 'repository' : 'paper',
            title: clampString(item.title, 1, MAX_TITLE_LEN, 'Untitled'),
            sourceOrLanguage: clampString(item.sourceOrLanguage, 1, 100, 'arXiv'),
            url: clampString(item.url, 1, MAX_URL_LEN, 'https://arxiv.org'),
            notes: (item.notes ?? '').trim().slice(0, MAX_NOTES_LEN),
            createdAt: serverTimestamp(),
            updatedAt: serverTimestamp(),
          });
        } catch (err) {
          handleFirestoreError(err, OperationType.CREATE, path);
        }
      }
    },
    [user, profileReady, bookmarks]
  );

  const updateBookmarkNotes = useCallback(
    async (bookmarkId: string, notes: string) => {
      if (!user || !profileReady) return;
      const cleanId = sanitizeId(bookmarkId);
      const path = `bookmarks/${cleanId}`;
      try {
        await updateDoc(doc(db, 'bookmarks', cleanId), {
          notes: notes.trim().slice(0, MAX_NOTES_LEN),
          updatedAt: serverTimestamp(),
        });
      } catch (err) {
        handleFirestoreError(err, OperationType.UPDATE, path);
      }
    },
    [user, profileReady]
  );

  const addCustomPaper = useCallback(
    async (paper: Omit<Paper, 'id'>) => {
      const generatedId = sanitizeId(`paper_${Date.now()}`);
      if (!user || !profileReady) {
        setLocalPapers((prev) => [{ ...paper, id: generatedId }, ...prev]);
        return;
      }

      const uid = sanitizeId(user.uid);
      const path = `customPapers/${generatedId}`;
      try {
        await setDoc(doc(db, 'customPapers', generatedId), {
          ownerId: uid,
          topic: clampString(paper.topic, 1, 50, 'ai'),
          topicLabel: clampString(paper.topicLabel, 1, 100, 'Artificial Intelligence'),
          title: clampString(paper.title, 1, MAX_TITLE_LEN, 'Untitled Paper'),
          authors: clampString(paper.authors, 1, 200, 'A. Researcher'),
          source: clampString(paper.source, 1, 60, 'arXiv'),
          date: clampString(paper.date, 1, 40, '2026'),
          abstract: clampString(paper.abstract, 1, MAX_ABSTRACT_LEN, 'Abstract summary.'),
          url: clampString(paper.url, 1, MAX_URL_LEN, 'https://arxiv.org'),
          doi: clampString(paper.doi || '10.48550/arXiv.2602.00001', 1, 100, '10.48550/arXiv.2602.00001'),
          createdAt: serverTimestamp(),
        });
      } catch (err) {
        handleFirestoreError(err, OperationType.CREATE, path);
      }
    },
    [user, profileReady]
  );

  const deleteCustomPaper = useCallback(
    async (paperId: string) => {
      if (!user || !profileReady) {
        setLocalPapers((prev) => prev.filter((p) => p.id !== paperId));
        return;
      }
      const cleanId = sanitizeId(paperId);
      const path = `customPapers/${cleanId}`;
      try {
        await deleteDoc(doc(db, 'customPapers', cleanId));
      } catch (err) {
        handleFirestoreError(err, OperationType.DELETE, path);
      }
    },
    [user, profileReady]
  );

  const addCustomRepo = useCallback(
    async (repo: Omit<ScoredRepository, 'id'>) => {
      const generatedId = sanitizeId(`repo_${Date.now()}`);
      if (!user || !profileReady) {
        setLocalRepos((prev) => [{ ...repo, id: generatedId }, ...prev]);
        return;
      }

      const uid = sanitizeId(user.uid);
      const path = `customRepos/${generatedId}`;
      const score = Math.max(0, Math.min(100, Math.round(repo.relevance_score)));
      try {
        await setDoc(doc(db, 'customRepos', generatedId), {
          ownerId: uid,
          name: clampString(repo.name, 1, 100, 'repo'),
          full_name: clampString(repo.full_name, 1, 200, 'ai-lab/repo'),
          url: clampString(repo.url, 1, MAX_URL_LEN, 'https://github.com'),
          description: clampString(repo.description, 1, 500, 'AI Repository candidate'),
          relevance_score: score,
          summary: clampString(repo.summary, 1, MAX_SUMMARY_LEN, 'Automated evaluation summary.'),
          reason: clampString(repo.reason, 1, MAX_REASON_LEN, 'Strong alignment with AI research.'),
          language: clampString(repo.language, 1, 60, 'Python'),
          createdAt: serverTimestamp(),
        });
      } catch (err) {
        handleFirestoreError(err, OperationType.CREATE, path);
      }
    },
    [user, profileReady]
  );

  const deleteCustomRepo = useCallback(
    async (repoId: string) => {
      if (!user || !profileReady) {
        setLocalRepos((prev) => prev.filter((r) => r.id !== repoId));
        return;
      }
      const cleanId = sanitizeId(repoId);
      const path = `customRepos/${cleanId}`;
      try {
        await deleteDoc(doc(db, 'customRepos', cleanId));
      } catch (err) {
        handleFirestoreError(err, OperationType.DELETE, path);
      }
    },
    [user, profileReady]
  );

  const recordSearchQuery = useCallback(
    async (queryText: string, contextTab: ActiveTab) => {
      const trimmed = queryText.trim();
      if (!trimmed || !user || !profileReady) return;

      const uid = sanitizeId(user.uid);
      const searchId = sanitizeId(`sh_${Date.now()}`);
      const path = `searchHistory/${searchId}`;
      const validTab: ActiveTab = ALLOWED_TABS.includes(contextTab) ? contextTab : 'terminal';

      try {
        await setDoc(doc(db, 'searchHistory', searchId), {
          ownerId: uid,
          query: clampString(trimmed, 1, MAX_QUERY_LEN, 'search'),
          contextTab: validTab,
          createdAt: serverTimestamp(),
        });
      } catch (err) {
        handleFirestoreError(err, OperationType.CREATE, path);
      }
    },
    [user, profileReady]
  );

  const deleteSearchHistoryItem = useCallback(
    async (searchId: string) => {
      if (!user || !profileReady) return;
      const cleanId = sanitizeId(searchId);
      const path = `searchHistory/${cleanId}`;
      try {
        await deleteDoc(doc(db, 'searchHistory', cleanId));
      } catch (err) {
        handleFirestoreError(err, OperationType.DELETE, path);
      }
    },
    [user, profileReady]
  );

  const allPapers = useMemo(() => {
    const dynamic = user ? customPapers : localPapers;
    return [...dynamic, ...INITIAL_PAPERS];
  }, [user, customPapers, localPapers]);

  const allRepositories = useMemo(() => {
    const dynamic = user ? customRepos : localRepos;
    return [...dynamic, ...INITIAL_REPOSITORIES];
  }, [user, customRepos, localRepos]);

  const value = useMemo(
    () => ({
      user,
      authReady,
      profileReady,
      authError,
      signInWithGoogle,
      signOutUser,
      bookmarks,
      customPapers: user ? customPapers : localPapers,
      customRepos: user ? customRepos : localRepos,
      allPapers,
      allRepositories,
      searchHistory,
      isBookmarked,
      toggleBookmark,
      updateBookmarkNotes,
      addCustomPaper,
      deleteCustomPaper,
      addCustomRepo,
      deleteCustomRepo,
      recordSearchQuery,
      deleteSearchHistoryItem,
    }),
    [
      user,
      authReady,
      profileReady,
      authError,
      signInWithGoogle,
      signOutUser,
      bookmarks,
      customPapers,
      localPapers,
      customRepos,
      localRepos,
      allPapers,
      allRepositories,
      searchHistory,
      isBookmarked,
      toggleBookmark,
      updateBookmarkNotes,
      addCustomPaper,
      deleteCustomPaper,
      addCustomRepo,
      deleteCustomRepo,
      recordSearchQuery,
      deleteSearchHistoryItem,
    ]
  );

  return <FirebaseContext.Provider value={value}>{children}</FirebaseContext.Provider>;
};

export function useFirebase() {
  const ctx = useContext(FirebaseContext);
  if (!ctx) {
    throw new Error('useFirebase must be used within a FirebaseProvider');
  }
  return ctx;
}
