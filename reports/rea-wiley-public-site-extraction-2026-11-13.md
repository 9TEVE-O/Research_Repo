# REA Discovery Note — Wiley public site extraction

**Target:** https://www.wiley.com/en-us  
**Observed:** 2026-11-13  
**Method:** bounded public-web inspection using rendered-page extraction; no login, bypass, exploitation, proprietary source retrieval, or backend access.  
**REA status:** DISCOVERY_NOTE / PARTIAL  
**Decision owner:** Steven Lees  
**Repository:** 9TEVE-O/Research_Repo

## 1. Decision / scope

Extract the observable structure, interaction surfaces, product pathways, and defensible implementation clues from Wiley's public homepage so the material can support later comparison, design analysis, or controlled reconstruction.

This note does **not** claim source-code parity, backend knowledge, security findings, or permission to reproduce Wiley assets.

## 2. Original evidence

### OBSERVED
- Canonical page: `https://www.wiley.com/en-us`.
- Page title: `Trusted Research & AI Insights | Wiley`.
- Primary message centers on trusted knowledge, evidence, transparency, expert judgment, and reliable research outcomes in an AI-transformed research environment.
- The homepage exposes 125 outbound links in the rendered extraction: 110 Wiley-domain links and 15 external links.
- The rendered page exposed 10 image references and no iframe references in this extraction.
- Public navigation/content paths include publishing, research, learning, authors, educators, learners, librarians, corporate/R&D audiences, societies/partners, careers, and About Wiley.
- A Journal Finder is promoted with search/filter/compare functionality across 1,800+ journals and an AI-powered abstract-match pathway.
- Wiley Online Library is a major downstream research destination.
- Publishing workflow/product pathways include Research Exchange and publishing partner solutions.
- Audience-specific content paths include academic institutions, corporate information centres, hospitals/healthcare, authors, educators and learners.
- Page metadata contains Open Graph and Twitter-card metadata.
- The favicon is served from `cdn.prod.website-files.com`; this is an infrastructure clue only, not proof of the complete site platform.
- Social preview imagery is served from `assets.wiley.com`.

### OBSERVED ACCESS CONSTRAINT
A normal direct fetch of the homepage returned HTTP 403 in the first inspection route. A rendered public-page extraction route succeeded. This demonstrates route-dependent access behaviour; it does not by itself establish the cause or specific anti-bot implementation.

## 3. Observable information architecture

### Research / discovery
- trusted research positioning
- research subjects
- library and institution solutions
- Wiley Online Library
- scientific content and R&D support
- research discovery and influence

### Publishing
- journal publishing
- book publishing
- open access
- author guidance
- editors/reviewers
- research integrity
- AI guidelines
- journal finder
- partner solutions
- Research Exchange

### Learning
- textbooks
- courseware
- inclusive access
- WileyPLUS
- self-paced learning
- career/professional resources

### Partner / institutional
- societies
- librarians
- academic institutions
- corporate information centres
- hospitals and healthcare
- corporate R&D
- advertising/licensing/reprints
- custom content

### Corporate / brand
- careers
- About Wiley
- contact
- knowledge-to-impact positioning

## 4. Minimal system model

```text
public visitor
  -> Wiley homepage
     -> intent segmentation
        -> Research
        -> Publishing
        -> Learning
        -> Partner / institutional
        -> Corporate / careers
     -> specialised tools/products
        -> Journal Finder
        -> Wiley Online Library
        -> Research Exchange
        -> WileyPLUS
     -> downstream conversion / task completion
        -> discover
        -> compare
        -> publish
        -> subscribe/access
        -> learn
        -> partner
```

The homepage behaves primarily as an intent router rather than a single transactional application.

## 5. Inferences and contradictions

### INFERRED
- The homepage is designed around audience-and-intent routing rather than product-first navigation.
- AI is used as a trust-and-research theme and is also attached to at least one concrete user utility: abstract-based journal matching.
- The site likely composes multiple downstream platforms/services rather than implementing every user journey inside one application.
- The `website-files.com` asset host may indicate a Webflow-related delivery component. This remains **INFERRED**, not verified platform attribution.

### UNKNOWN
- frontend framework and build system
- CMS of record
- API topology
- identity/authentication architecture
- personalisation logic
- analytics stack
- search/index provider
- Journal Finder model/provider and ranking implementation
- Research Exchange architecture
- backend services and data stores
- deployment topology
- anti-bot/CDN configuration responsible for the 403 route difference

## 6. Candidate discriminating tests

These are **NOT_RUN**.

1. **Journal Finder behaviour test**  
   Compare keyword search, filter combinations, and abstract-match outputs against a fixed set of synthetic research abstracts.  
   Oracle: stable, explainable differences between lexical search and AI match.

2. **Navigation intent test**  
   Start from representative intents (publish article, obtain institutional access, find textbook, identify journal) and measure steps to task-specific destination.  
   Oracle: reproducible route map and redirect boundaries.

3. **Platform boundary test**  
   Record only public redirects/domain changes across Wiley homepage, Wiley Online Library, Journal Finder, Research Exchange and WileyPLUS.  
   Oracle: evidence-backed platform/domain boundary map without inspecting private implementation.

4. **Access-route test**  
   Compare standard fetch vs rendered-browser access under the same public URL without evasion or login.  
   Oracle: reproducible HTTP/browser difference with headers/status captured where permitted.

## 7. Reconstruction opportunity

A lawful reconstruction should reproduce **behavioural patterns**, not Wiley branding, proprietary content, or copyrighted assets.

Smallest useful prototype:
- neutral research/publishing landing page
- audience-intent segmentation
- journal/product finder mock using synthetic records
- research/publishing/learning route map
- transparent evidence labels for AI-assisted matching
- accessibility-first navigation
- no copied Wiley text or visual assets

Status would remain `RECONSTRUCTION_PROTOTYPE / NOT_RUN` until implemented and tested.

## 8. Decision

**SUPPORTED:** the public homepage can be modelled as a research-and-learning intent router connecting multiple specialised products and platforms.

**PARTIAL:** the extraction establishes visible information architecture, messaging, destinations and some delivery clues, but not internal implementation.

**Do not claim:** source parity, backend architecture, security weakness, model internals, or complete technology stack.

## 9. Smallest next action

If deeper technical understanding is required, inspect one bounded public workflow next: **Journal Finder**. Capture visible inputs, outputs, state transitions and domain boundaries using synthetic research text, then compare two plausible implementation hypotheses.

No deployment, scraping at scale, login access, or production mutation is authorised by this note.
