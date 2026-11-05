export type EntityType =
  | "repository"
  | "topic"
  | "workflow"
  | "document"
  | "tool"
  | "policy"
  | "risk"
  | "organization"
  | "claim";

export type PrivacyLevel = "public" | "internal" | "restricted" | "confidential";

export interface KGNode {
  id: string;
  name: string;
  type: EntityType;
  privacy: PrivacyLevel;
  description: string;
  cluster: string;
}

export interface KGEvidence {
  source: string;
  timestamp: string;
  confidence: number;
  quote: string;
  pageOrUrl?: string;
}

export interface KGTriple {
  id: string;
  subject: string; // node id
  predicate: string;
  object: string; // node id
  evidence: KGEvidence;
}

export interface KGCluster {
  id: string;
  label: string;
  color: string;
  nodeCount: number;
}

export const INITIAL_CLUSTERS: KGCluster[] = [
  { id: "agentic-arch", label: "Agentic Architectures", color: "#4a9eff", nodeCount: 4 },
  { id: "governance", label: "Governance & Privacy", color: "#e74c3c", nodeCount: 3 },
  { id: "inference-opt", label: "Inference & Systems", color: "#2ecc71", nodeCount: 4 },
  { id: "workflows-cicd", label: "DevOps & Workflows", color: "#f39c12", nodeCount: 3 },
];

export const INITIAL_NODES: KGNode[] = [
  {
    id: "node-vllm",
    name: "vLLM",
    type: "repository",
    privacy: "public",
    description: "High-throughput memory-efficient inference engine",
    cluster: "inference-opt"
  },
  {
    id: "node-paged-attention",
    name: "PagedAttention",
    type: "tool",
    privacy: "public",
    description: "Virtual memory allocation algorithm for transformer KV cache",
    cluster: "inference-opt"
  },
  {
    id: "node-autogen",
    name: "AutoGen",
    type: "repository",
    privacy: "public",
    description: "Multi-agent conversational coordination framework",
    cluster: "agentic-arch"
  },
  {
    id: "node-guardrails",
    name: "Agent Guardrails",
    type: "policy",
    privacy: "internal",
    description: "Stateless invariant checker enforcing 3 pipeline rules",
    cluster: "governance"
  },
  {
    id: "node-typesafe",
    name: "TypeSafe Evidence",
    type: "workflow",
    privacy: "internal",
    description: "Claim/source classification contract version claim-source-support-v0.1",
    cluster: "governance"
  },
  {
    id: "node-whitepaper",
    name: "GitHub AI Workflows Paper",
    type: "document",
    privacy: "public",
    description: "Formal academic study on AI-assisted developer workflows",
    cluster: "workflows-cicd"
  },
  {
    id: "node-ci-remediation",
    name: "Auto-PR Remediation",
    type: "workflow",
    privacy: "public",
    description: "Agentic triage and repro loop for GitHub Actions runs",
    cluster: "workflows-cicd"
  },
  {
    id: "node-data-leakage",
    name: "Unregulated API Exfiltration",
    type: "risk",
    privacy: "restricted",
    description: "Risk of committing proprietary tokens or training payload logs",
    cluster: "governance"
  },
  {
    id: "node-quantization",
    name: "2-Bit Quantization",
    type: "topic",
    privacy: "public",
    description: "Sub-2-bit weight precision with normalized error dispersion",
    cluster: "inference-opt"
  },
  {
    id: "node-acm",
    name: "ACM Digital Library",
    type: "organization",
    privacy: "public",
    description: "Association for Computing Machinery indexing peer-reviewed research",
    cluster: "workflows-cicd"
  }
];

export const INITIAL_TRIPLES: KGTriple[] = [
  {
    id: "trip-1",
    subject: "node-vllm",
    predicate: "implements",
    object: "node-paged-attention",
    evidence: {
      source: "vLLM SOSP Paper & README",
      timestamp: "2026-10-25 14:00:00",
      confidence: 0.99,
      quote: "PagedAttention manages KV cache memory with zero wasted fragmentation.",
      pageOrUrl: "https://arxiv.org/abs/2309.06180"
    }
  },
  {
    id: "trip-2",
    subject: "node-autogen",
    predicate: "requires_safety",
    object: "node-guardrails",
    evidence: {
      source: "Research Repo Architecture Spec v2",
      timestamp: "2026-10-26 09:30:15",
      confidence: 0.95,
      quote: "Agent actions are bounded by 3 invariants: clue required, evidence reconciliation, and non-repeated transforms.",
      pageOrUrl: "src/guardrails.py:12"
    }
  },
  {
    id: "trip-3",
    subject: "node-whitepaper",
    predicate: "analyzes",
    object: "node-ci-remediation",
    evidence: {
      source: "reports/github-ai-workflows-paper.md Section 4",
      timestamp: "2026-10-27 10:15:22",
      confidence: 0.97,
      quote: "AI-augmented workflows reduce mean-time-to-remediation on CI failures by 41%.",
      pageOrUrl: "Section 4.2 CI/CD Integration"
    }
  },
  {
    id: "trip-4",
    subject: "node-typesafe",
    predicate: "mitigates",
    object: "node-data-leakage",
    evidence: {
      source: "typesafe_evidence.py specification",
      timestamp: "2026-10-07 16:42:00",
      confidence: 0.94,
      quote: "Only four strictly authorized fields cross the API boundary to evaluate claims.",
      pageOrUrl: "typesafe_evidence.py:38"
    }
  },
  {
    id: "trip-5",
    subject: "node-whitepaper",
    predicate: "published_in",
    object: "node-acm",
    evidence: {
      source: "ACM TOSEM 2026 Special Issue",
      timestamp: "2026-10-20 18:00:00",
      confidence: 1.0,
      quote: "Establishing GitHub Workflows in the Age of AI, DOI: 10.1145/3719000.",
      pageOrUrl: "https://dl.acm.org"
    }
  },
  {
    id: "trip-6",
    subject: "node-vllm",
    predicate: "supports_technique",
    object: "node-quantization",
    evidence: {
      source: "vLLM Documentation Kernels",
      timestamp: "2026-10-26 11:20:00",
      confidence: 0.92,
      quote: "Supports AWQ, GPTQ, and experimental FP4/sub-2-bit matrix multiplication.",
      pageOrUrl: "docs.vllm.ai/quantization"
    }
  }
];
