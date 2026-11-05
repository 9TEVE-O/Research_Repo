export interface PaperSection {
  id: string;
  title: string;
  content: string;
}

export const WHITEPAPER_META = {
  title: "Establishing GitHub Workflows for App and Software Developers in the Age of AI",
  authors: "S. O'Connor, A. Vance, Institutional Research Working Group",
  institution: "AI Systems Engineering & Research Working Group",
  date: "February 2026",
  abstract: "The proliferation of artificial intelligence tools within software development workflows has fundamentally altered how development teams design, review, and ship code. GitHub, as the dominant collaborative development platform, now occupies a central role in mediating both human and machine contributions to software projects. This paper examines how development teams can establish robust, scalable GitHub workflows that account for the unique demands imposed by AI-assisted development, encompassing mobile and web application delivery, backend systems engineering, and the governance challenges that arise when AI agents participate as active contributors.",
  keywords: ["GitHub", "AI-assisted development", "DevOps", "CI/CD", "GitHub Copilot", "branching strategy", "security governance", "mobile development", "semantic versioning"],
  wordCount: "4,850 words",
};

export const WHITEPAPER_SECTIONS: PaperSection[] = [
  {
    id: "abstract",
    title: "Abstract",
    content: `The proliferation of artificial intelligence tools within software development workflows has fundamentally altered how development teams design, review, and ship code. GitHub, as the dominant collaborative development platform, now occupies a central role in mediating both human and machine contributions to software projects.

This paper examines how development teams can establish robust, scalable GitHub workflows that account for the unique demands imposed by AI-assisted development, encompassing mobile and web application delivery, backend systems engineering, and the governance challenges that arise when AI agents participate as active contributors.

Drawing on established literature in DevOps, software engineering practices, and emerging AI tool adoption research, we synthesize best practices across repository architecture, branching strategy, continuous integration and delivery pipeline design, security governance, and asynchronous collaboration.`
  },
  {
    id: "sec-1",
    title: "1. Introduction",
    content: `Software development has never been more productive by certain measures, nor more complex to govern. The emergence of large language model (LLM)-based coding assistants — tools such as GitHub Copilot, Anthropic's Claude Code, and Cursor — has introduced a new class of contributor to the software project: one that can generate, review, test, and refactor code at machine speed but whose outputs require careful human oversight (Ziegler et al., 2022).

Coordinating human and AI contributions within a coherent, auditable workflow is now among the most consequential challenges in applied software engineering.

This paper addresses three research questions:
1. What repository architectures and branching strategies best accommodate the combination of human and AI contributions in modern software projects?
2. How should development teams integrate AI tools at each stage of the software delivery lifecycle while preserving appropriate human oversight and security guarantees?
3. What governance mechanisms are necessary to ensure that AI-augmented workflows remain compliant with security, licensing, and regulatory requirements?`
  },
  {
    id: "sec-2",
    title: "2. Background and Related Work",
    content: `2.1 DevOps and Continuous Delivery:
The principles underlying modern GitHub workflows owe much to the DevOps movement (Kim et al., 2016). Humble and Farley's foundational treatment established the pipeline as the organizing metaphor: a sequence of automated stages through which every change must pass before reaching production.

2.2 GitHub as a Research Subject:
Ray et al. (2014) analyzed the relationship between programming language choice and defect density across GitHub repositories. More recently, Mens et al. (2023) examined software ecosystem health and the cascading risks that dependency updates introduce.

2.3 AI-Assisted Development:
Ziegler et al. (2022) found Copilot suggestions were accepted ~26% of the time. However, Dakhel et al. (2023) and Pearce et al. (2022) revealed that a substantial fraction of AI-generated solutions contain logical bugs or security vulnerabilities, necessitating stringent automated testing and human oversight.`
  },
  {
    id: "sec-3",
    title: "3. Repository Architecture and Organization",
    content: `A codebase's directory structure dictates how effectively an AI agent can build contextual understanding.

Key architectural requirements:
- Monorepos vs Polyrepos: Monorepos provide holistic context for cross-cutting changes, but require strict boundaries (e.g., Nx, Turborepo) to prevent LLM context saturation.
- Self-Documenting Structure: Consistent directory hierarchies (docs/, tests/, src/) enable autonomous tools to locate files predictably.
- Explicit Contracts: OpenAPI specs, TypeScript types, and protobuf definitions serve as machine-readable boundaries that AI agents can validate against deterministically.`
  },
  {
    id: "sec-4",
    title: "4. AI Integration Strategies",
    content: `Integrating AI tools into GitHub workflows requires distinguishing between synchronous interactive assistance (IDE autocomplete) and asynchronous pipeline execution (automated PR review, bug remediation bots).

Strategies:
1. AI as Code Generator: Fast iterative drafting in feature branches.
2. AI as Automated Reviewer: Initial lint, style, and regression check prior to human reviewer assignment.
3. AI as Triage Agent: Classifying incoming issues, clustering bug reports, and generating minimal reproducible examples.`
  },
  {
    id: "sec-5",
    title: "5. App Developer Considerations (iOS & Android)",
    content: `Mobile application development introduces unique constraints:
- Binary signing keys (keystores, provisioning profiles) must never be accessible to AI agent sandboxes.
- Platform store review cycles (Apple App Store, Google Play) demand rigorous release branching.
- Device matrix testing requires automated emulator execution before merging AI-assisted UI changes.`
  },
  {
    id: "sec-6",
    title: "6. Software Developer Considerations (Backend & Libraries)",
    content: `For backend services and library authors:
- Strict Semantic Versioning: Automated changelog and version bumping via commit conventions.
- Zero-Trust Dependency Management: Automated auditing of lockfiles to prevent dependency confusion attacks.
- High-Concurrency Performance Benchmarking: Performance regression gates in CI to detect unoptimized AI-generated loops.`
  },
  {
    id: "sec-7",
    title: "7. Security, Compliance, and Governance",
    content: `Security governance for AI-assisted code requires three rings of defense:
1. Pre-commit Secret Scanning: Git hooks preventing accidental credential leakage.
2. Static Analysis & SAST: Automated scanning for SQL injection, buffer overflows, and unsafe deserialization.
3. Software Bill of Materials (SBOM): Generating cryptographic provenance for every build artifact in adherence to Executive Order 14028.`
  },
  {
    id: "sec-8",
    title: "8. Collaborative Workflows",
    content: `Asynchronous collaboration between human engineers and autonomous agents requires:
- Clear Attribution: Distinguishing human commits from agent commits with co-authored headers.
- Non-Blocking Review Pipelines: Automated review bots post non-blocking advisory suggestions without impeding merge velocity.
- Escalation Policies: Complex architecture or security changes automatically mandate senior engineer review.`
  },
  {
    id: "sec-9",
    title: "9. Discussion & Open Questions",
    content: `Key open questions include:
- Long-term code churn: Does high-volume AI code increase technical debt over 3-5 year horizons?
- Cognitive fatigue: How do human reviewers maintain vigilance when inspecting dozens of syntactically polished AI pull requests?
- Verification economics: Will the cost of formal verification outweigh the speed gains of generative code creation?`
  },
  {
    id: "sec-10",
    title: "10. Conclusion & References",
    content: `The most important single principle for establishing robust GitHub workflows in the age of AI is the preservation of human judgment at consequential decision points. AI tools should be understood as powerful force multipliers for the capabilities that software engineers already possess, not as autonomous agents whose outputs can be trusted without verification.

Workflows that deploy AI to reduce friction while reserving contextual, ethical, and architectural reasoning to human engineers will be the ones that endure.`
  }
];
