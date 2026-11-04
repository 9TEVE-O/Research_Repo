# Security Specification (`security_spec.md`)

## 1. Data Invariants
1. **Identity Isolation (`ownerId`)**: Every document in `/users/{userId}`, `/bookmarks/{bookmarkId}`, `/customPapers/{paperId}`, `/customRepos/{repoId}`, and `/searchHistory/{searchId}` MUST have `ownerId == request.auth.uid`. Users can only read, create, update, or delete their own documents.
2. **Email Verification Mandate**: Every read and write operation requires `request.auth != null && request.auth.token.email_verified == true`.
3. **Parent Consistency Invariant**: Creating a document in `/bookmarks`, `/customPapers`, `/customRepos`, or `/searchHistory` requires that `/users/$(request.auth.uid)` already exists in Firestore (`exists(/databases/$(database)/documents/users/$(request.auth.uid))`).
4. **Strict Key & Size Enforcement**: Every create operation enforces `hasAll` and `hasOnly` for exact schema keys, string `.size()` bounds matching `firebase-blueprint.json`, and regex validation on IDs (`^[a-zA-Z0-9_\-]+$`).
5. **Immutable Ownership & Creation Timestamps**: `ownerId` and `createdAt` can never be modified after creation (`incoming().ownerId == existing().ownerId && incoming().createdAt == existing().createdAt`).
6. **Server Timestamp Enforcement**: All `createdAt` fields on create must equal `request.time`, and all `updatedAt` fields on create/update must equal `request.time`.
7. **Query Enforcer (No Blanket Reads)**: `list` operations on `/bookmarks`, `/customPapers`, `/customRepos`, and `/searchHistory` strictly enforce `resource.data.ownerId == request.auth.uid`. `list` is completely forbidden on `/users`.

---

## 2. The "Dirty Dozen" Adversarial Payloads

1. **Unverified Email Spoof (`Payload 1`)**:
   - Auth: `{ uid: "user_1", token: { email_verified: false } }`
   - Target: `POST /users/user_1`
   - Expected: `PERMISSION_DENIED`

2. **Identity Spoofing on Create (`Payload 2`)**:
   - Auth: `{ uid: "user_1", token: { email_verified: true } }`
   - Target: `POST /bookmarks/bm_1`
   - Data: `{ ownerId: "user_2", itemId: "ai-1", itemType: "paper", title: "Paper", sourceOrLanguage: "arXiv", url: "https://arxiv.org", notes: "", createdAt: SERVER_TIME, updatedAt: SERVER_TIME }`
   - Expected: `PERMISSION_DENIED`

3. **Shadow / Ghost Field Injection (`Payload 3`)**:
   - Auth: `{ uid: "user_1", token: { email_verified: true } }`
   - Target: `POST /users/user_1`
   - Data: `{ ownerId: "user_1", displayName: "Alice", activeTabPreference: "terminal", isAdmin: true, createdAt: SERVER_TIME, updatedAt: SERVER_TIME }`
   - Expected: `PERMISSION_DENIED`

4. **Orphaned Write Without User Profile (`Payload 4`)**:
   - Auth: `{ uid: "user_no_profile", token: { email_verified: true } }`
   - Target: `POST /searchHistory/sh_1`
   - Data: `{ ownerId: "user_no_profile", query: "transformers", contextTab: "terminal", createdAt: SERVER_TIME }`
   - Expected: `PERMISSION_DENIED` (because `/users/user_no_profile` does not exist)

5. **Path ID Poisoning Attack (`Payload 5`)**:
   - Auth: `{ uid: "user_1", token: { email_verified: true } }`
   - Target: `POST /bookmarks/invalid$id!@#`
   - Expected: `PERMISSION_DENIED`

6. **Denial of Wallet Oversized String (`Payload 6`)**:
   - Auth: `{ uid: "user_1", token: { email_verified: true } }`
   - Target: `POST /searchHistory/sh_oversized`
   - Data: `{ ownerId: "user_1", query: "A".repeat(500), contextTab: "terminal", createdAt: SERVER_TIME }`
   - Expected: `PERMISSION_DENIED` (`query.size() > 200`)

7. **Client-Spoofed Timestamp (`Payload 7`)**:
   - Auth: `{ uid: "user_1", token: { email_verified: true } }`
   - Target: `POST /searchHistory/sh_past`
   - Data: `{ ownerId: "user_1", query: "vllm", contextTab: "discovery", createdAt: Timestamp.fromMillis(1000000) }`
   - Expected: `PERMISSION_DENIED` (`createdAt != request.time`)

8. **Immutable Field Mutation on Update (`Payload 8`)**:
   - Auth: `{ uid: "user_1", token: { email_verified: true } }`
   - Target: `PATCH /bookmarks/bm_1`
   - Data: `{ ownerId: "user_2", notes: "Hijacked", updatedAt: SERVER_TIME }`
   - Expected: `PERMISSION_DENIED`

9. **Unallowed Key Mutation on Update (`Payload 9`)**:
   - Auth: `{ uid: "user_1", token: { email_verified: true } }`
   - Target: `PATCH /bookmarks/bm_1`
   - Data: `{ title: "Changed Title", notes: "Updated note", updatedAt: SERVER_TIME }`
   - Expected: `PERMISSION_DENIED` (Only `notes` and `updatedAt` are mutable inBookmark update action)

10. **Invalid Enum Value (`Payload 10`)**:
    - Auth: `{ uid: "user_1", token: { email_verified: true } }`
    - Target: `POST /users/user_1`
    - Data: `{ ownerId: "user_1", displayName: "Alice", activeTabPreference: "hacked-tab", createdAt: SERVER_TIME, updatedAt: SERVER_TIME }`
    - Expected: `PERMISSION_DENIED`

11. **Cross-Tenant Read (`Payload 11`)**:
    - Auth: `{ uid: "user_2", token: { email_verified: true } }`
    - Target: `GET /users/user_1`
    - Expected: `PERMISSION_DENIED`

12. **Blanket Unfiltered List Query (`Payload 12`)**:
    - Auth: `{ uid: "user_2", token: { email_verified: true } }`
    - Target: `LIST /bookmarks` (without `where('ownerId', '==', 'user_2')`)
    - Expected: `PERMISSION_DENIED`

---

## 3. Red Team Audit & Conflict Report

| Collection | Identity Spoofing | State Shortcutting | Resource Poisoning | Value Poisoning | `isValid[Entity]` in Update | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `/users/{userId}` | Blocked (`ownerId == request.auth.uid && userId == request.auth.uid`) | N/A | Blocked (`isValidId` + max lengths) | Blocked (`isValidUserProfile` enforces enum & sizes) | Present (`isValidUserProfile(incoming())`) | PASS |
| `/bookmarks/{bookmarkId}` | Blocked (`ownerId == request.auth.uid` + `exists(/users/uid)`) | N/A | Blocked (`isValidId` + max lengths) | Blocked (`isValidBookmark` enforces types & sizes) | Present (`isValidBookmark(incoming())`) | PASS |
| `/customPapers/{paperId}` | Blocked (`ownerId == request.auth.uid` + `exists(/users/uid)`) | Updates forbidden (append/delete only) | Blocked (`isValidId` + max lengths) | Blocked (`isValidCustomPaper`) | Updates disabled (`allow update: if false`) | PASS |
| `/customRepos/{repoId}` | Blocked (`ownerId == request.auth.uid` + `exists(/users/uid)`) | Updates forbidden (append/delete only) | Blocked (`isValidId` + max lengths) | Blocked (`isValidCustomRepo`) | Updates disabled (`allow update: if false`) | PASS |
| `/searchHistory/{searchId}` | Blocked (`ownerId == request.auth.uid` + `exists(/users/uid)`) | Updates forbidden (append/delete only) | Blocked (`isValidId` + max lengths) | Blocked (`isValidSearchHistory`) | Updates disabled (`allow update: if false`) | PASS |
