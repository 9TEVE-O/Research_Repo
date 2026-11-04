/**
 * Firestore Security Rules Test Suite — "Dirty Dozen" Adversarial Payloads
 * Verifies that all 12 adversarial payloads specified in security_spec.md return PERMISSION_DENIED.
 */

export interface AdversarialTestCase {
  id: number;
  name: string;
  auth: { uid: string; email_verified: boolean } | null;
  operation: 'get' | 'list' | 'create' | 'update' | 'delete';
  path: string;
  payload?: Record<string, unknown>;
  expectedResult: 'PERMISSION_DENIED' | 'ALLOWED';
}

export const DIRTY_DOZEN_TESTS: AdversarialTestCase[] = [
  {
    id: 1,
    name: 'Unverified Email Spoof on User Profile Creation',
    auth: { uid: 'user_1', email_verified: false },
    operation: 'create',
    path: '/users/user_1',
    payload: {
      ownerId: 'user_1',
      displayName: 'Alice',
      activeTabPreference: 'terminal',
      createdAt: 'SERVER_TIMESTAMP',
      updatedAt: 'SERVER_TIMESTAMP',
    },
    expectedResult: 'PERMISSION_DENIED',
  },
  {
    id: 2,
    name: 'Identity Spoofing on Bookmark Create',
    auth: { uid: 'user_1', email_verified: true },
    operation: 'create',
    path: '/bookmarks/bm_1',
    payload: {
      ownerId: 'user_2',
      itemId: 'ai-1',
      itemType: 'paper',
      title: 'Spoofed Bookmark',
      sourceOrLanguage: 'arXiv',
      url: 'https://arxiv.org/abs/2601.08432',
      notes: '',
      createdAt: 'SERVER_TIMESTAMP',
      updatedAt: 'SERVER_TIMESTAMP',
    },
    expectedResult: 'PERMISSION_DENIED',
  },
  {
    id: 3,
    name: 'Shadow / Ghost Field Injection (isAdmin: true)',
    auth: { uid: 'user_1', email_verified: true },
    operation: 'create',
    path: '/users/user_1',
    payload: {
      ownerId: 'user_1',
      displayName: 'Alice',
      activeTabPreference: 'terminal',
      isAdmin: true,
      createdAt: 'SERVER_TIMESTAMP',
      updatedAt: 'SERVER_TIMESTAMP',
    },
    expectedResult: 'PERMISSION_DENIED',
  },
  {
    id: 4,
    name: 'Orphaned Write Without Existing User Profile',
    auth: { uid: 'user_no_profile', email_verified: true },
    operation: 'create',
    path: '/searchHistory/sh_1',
    payload: {
      ownerId: 'user_no_profile',
      query: 'transformers',
      contextTab: 'terminal',
      createdAt: 'SERVER_TIMESTAMP',
    },
    expectedResult: 'PERMISSION_DENIED',
  },
  {
    id: 5,
    name: 'Path ID Poisoning Attack',
    auth: { uid: 'user_1', email_verified: true },
    operation: 'create',
    path: '/bookmarks/invalid$id!@#',
    payload: {
      ownerId: 'user_1',
      itemId: 'ai-1',
      itemType: 'paper',
      title: 'Paper',
      sourceOrLanguage: 'arXiv',
      url: 'https://arxiv.org',
      notes: '',
      createdAt: 'SERVER_TIMESTAMP',
      updatedAt: 'SERVER_TIMESTAMP',
    },
    expectedResult: 'PERMISSION_DENIED',
  },
  {
    id: 6,
    name: 'Denial of Wallet Oversized String (>200 chars in query)',
    auth: { uid: 'user_1', email_verified: true },
    operation: 'create',
    path: '/searchHistory/sh_oversized',
    payload: {
      ownerId: 'user_1',
      query: 'A'.repeat(500),
      contextTab: 'terminal',
      createdAt: 'SERVER_TIMESTAMP',
    },
    expectedResult: 'PERMISSION_DENIED',
  },
  {
    id: 7,
    name: 'Client-Spoofed Past Timestamp',
    auth: { uid: 'user_1', email_verified: true },
    operation: 'create',
    path: '/searchHistory/sh_past',
    payload: {
      ownerId: 'user_1',
      query: 'vllm',
      contextTab: 'discovery',
      createdAt: '2020-01-01T00:00:00Z',
    },
    expectedResult: 'PERMISSION_DENIED',
  },
  {
    id: 8,
    name: 'Immutable Field Mutation on Update (ownerId change)',
    auth: { uid: 'user_1', email_verified: true },
    operation: 'update',
    path: '/bookmarks/bm_1',
    payload: {
      ownerId: 'user_2',
      notes: 'Hijacked',
      updatedAt: 'SERVER_TIMESTAMP',
    },
    expectedResult: 'PERMISSION_DENIED',
  },
  {
    id: 9,
    name: 'Unallowed Key Mutation on Bookmark Update (title modification)',
    auth: { uid: 'user_1', email_verified: true },
    operation: 'update',
    path: '/bookmarks/bm_1',
    payload: {
      title: 'Unauthorized Title Change',
      notes: 'Valid note',
      updatedAt: 'SERVER_TIMESTAMP',
    },
    expectedResult: 'PERMISSION_DENIED',
  },
  {
    id: 10,
    name: 'Invalid Enum Value on activeTabPreference',
    auth: { uid: 'user_1', email_verified: true },
    operation: 'create',
    path: '/users/user_1',
    payload: {
      ownerId: 'user_1',
      displayName: 'Alice',
      activeTabPreference: 'invalid_tab',
      createdAt: 'SERVER_TIMESTAMP',
      updatedAt: 'SERVER_TIMESTAMP',
    },
    expectedResult: 'PERMISSION_DENIED',
  },
  {
    id: 11,
    name: 'Cross-Tenant Profile Read',
    auth: { uid: 'user_2', email_verified: true },
    operation: 'get',
    path: '/users/user_1',
    expectedResult: 'PERMISSION_DENIED',
  },
  {
    id: 12,
    name: 'Blanket Unfiltered List Query Across All Bookmarks',
    auth: { uid: 'user_2', email_verified: true },
    operation: 'list',
    path: '/bookmarks',
    expectedResult: 'PERMISSION_DENIED',
  },
];
