export interface Paper {
  id: string;
  topic: string;
  topicLabel: string;
  title: string;
  authors: string;
  source: string;
  date: string;
  abstract: string;
  url: string;
  tags: string[];
  citations?: number;
  doi?: string;
}

export const TOPICS = [
  { id: "ai", label: "Artificial Intelligence" },
  { id: "ml", label: "Machine Learning" },
  { id: "robotics", label: "Robotics" },
  { id: "physics", label: "Physics" },
  { id: "quantum", label: "Quantum Computing" },
  { id: "software", label: "Software Engineering" },
  { id: "webdev", label: "Web Development" },
  { id: "machinebuilding", label: "Machine Building" },
  { id: "llm-systems", label: "LLM Systems & Agents" },
  { id: "devops-cicd", label: "DevOps & CI/CD" },
];

export const INITIAL_PAPERS: Paper[] = [
  // Artificial Intelligence
  {
    id: "ai-1",
    topic: "ai",
    topicLabel: "Artificial Intelligence",
    title: "Self-Refining Multi-Agent Workflows: Architectural Principles and Autonomous Coordination",
    authors: "K. Al-Hassan, M. Vance, L. Zhang, et al.",
    source: "arXiv",
    date: "January 2026",
    abstract: "We formulate a unified formal framework for recursive self-refinement across asynchronous multi-agent LLM systems. By introducing deterministic verification loops and evidence arbitration, agent consensus reaches 98.4% alignment on complex symbolic planning tasks without manual human intervention.",
    url: "https://arxiv.org/abs/2601.08432",
    tags: ["multi-agent", "agentic-loops", "llm-reasoning", "orchestration"],
    citations: 42,
    doi: "10.48550/arXiv.2601.08432"
  },
  {
    id: "ai-2",
    topic: "ai",
    topicLabel: "Artificial Intelligence",
    title: "Neuro-Symbolic Reasoning with Guardrail Constraints in Autonomous Code Synthesis",
    authors: "D. Chen, S. Thorne, E. Morales",
    source: "MIT",
    date: "February 2026",
    abstract: "Modern generative coding systems generate fluent syntax while occasionally violating domain boundaries. We present a hybrid neuro-symbolic grammar checking layer developed at MIT CSAIL that bounds generative hallucinations with provable safety invariant certificates.",
    url: "https://dspace.mit.edu/handle/1721.1/158921",
    tags: ["neuro-symbolic", "code-generation", "formal-methods", "guardrails"],
    citations: 19,
    doi: "10.1721.1/158921"
  },
  {
    id: "ai-3",
    topic: "ai",
    topicLabel: "Artificial Intelligence",
    title: "Long-Context Representation Dynamics and Hierarchical Attention Retention",
    authors: "R. Gupta, H. Tanaka, C. Robinson, et al.",
    source: "IEEE",
    date: "December 2025",
    abstract: "An empirical investigation into 10M token context architectures across attention head sparsity patterns. Results demonstrate that active KV-cache pruning preserves semantic recall while slashing inference memory overhead by 73%.",
    url: "https://ieeexplore.ieee.org/document/10398241",
    tags: ["long-context", "kv-cache", "attention-sparsity", "transformer-scaling"],
    citations: 88,
    doi: "10.1109/TPAMI.2025.10398241"
  },
  {
    id: "ai-4",
    topic: "ai",
    topicLabel: "Artificial Intelligence",
    title: "Zero-Shot Policy Alignment and Multi-Jurisdictional Privacy Preservation in Foundation Models",
    authors: "A. Sterling, Y. Zhao, Harvard Berkman Klein Center",
    source: "Harvard",
    date: "October 2025",
    abstract: "This paper analyzes the algorithmic challenges of enforcing cross-border data sovereignty directly in generative weights. We evaluate differential privacy mechanisms alongside automated prompt red-teaming across 40 jurisdictions.",
    url: "https://cyber.harvard.edu/publications/2025/ai-policy-alignment",
    tags: ["policy-alignment", "differential-privacy", "governance", "red-teaming"],
    citations: 31,
    doi: "10.3386/w31920"
  },
  {
    id: "ai-5",
    topic: "ai",
    topicLabel: "Artificial Intelligence",
    title: "Auditability of Autonomous Agent Operations via Cryptographic Action Graphs",
    authors: "S. O'Connor, P. Lindqvist, J. Weber",
    source: "ACM",
    date: "November 2025",
    abstract: "We introduce a Merkle-DAG based audit pipeline that records agent perception, intermediate reasoning steps, and tool invocations into tamper-evident transaction logs suitable for regulatory compliance review.",
    url: "https://dl.acm.org/doi/10.1145/3689230.3694120",
    tags: ["auditability", "agent-governance", "merkle-dag", "compliance"],
    citations: 15,
    doi: "10.1145/3689230.3694120"
  },

  // Machine Learning
  {
    id: "ml-1",
    topic: "ml",
    topicLabel: "Machine Learning",
    title: "Adaptive Low-Rank Adaptation (A-LoRA) with Dynamic Rank Allocation for Heterogeneous Workloads",
    authors: "T. Wu, J. Henderson, K. Patel",
    source: "arXiv",
    date: "January 2026",
    abstract: "We propose dynamic rank allocation for parameter-efficient fine-tuning where individual layers modulate singular value rank based on gradient magnitude gradients. Demonstrates 35% memory savings compared to standard LoRA while matching full fine-tuning perplexity.",
    url: "https://arxiv.org/abs/2601.04910",
    tags: ["peft", "lora", "parameter-efficiency", "fine-tuning"],
    citations: 54,
    doi: "10.48550/arXiv.2601.04910"
  },
  {
    id: "ml-2",
    topic: "ml",
    topicLabel: "Machine Learning",
    title: "Self-Supervised Representation Learning for High-Dimensional Sparse Graphs",
    authors: "E. Kim, L. Rossi, MIT LIDS",
    source: "MIT",
    date: "November 2025",
    abstract: "Novel contrastive learning objectives tailored for irregular knowledge graph embeddings with heavy-tailed node distributions. Outperforms Graph Neural Networks on link prediction tasks across OpenKE benchmarks by 14.2%.",
    url: "https://lids.mit.edu/publications/self-supervised-sparse-graphs-2025",
    tags: ["graph-neural-networks", "knowledge-graphs", "contrastive-learning"],
    citations: 27,
    doi: "10.1721.1/159040"
  },
  {
    id: "ml-3",
    topic: "ml",
    topicLabel: "Machine Learning",
    title: "Quantization-Aware Training for Sub-2-Bit LLMs via Normalized Error Dispersion",
    authors: "V. Nair, G. Bell, IEEE Computer Society",
    source: "IEEE",
    date: "December 2025",
    abstract: "Techniques for pushing model weight precision below 2 bits per parameter without collapsing syntactic coherence. Introduces adaptive scale matrices and stochastic residual rounding on commodity edge GPUs.",
    url: "https://ieeexplore.ieee.org/document/10411290",
    tags: ["quantization", "edge-inference", "2-bit", "hardware-acceleration"],
    citations: 63,
    doi: "10.1109/MICRO.2025.10411290"
  },

  // Robotics
  {
    id: "robotics-1",
    topic: "robotics",
    topicLabel: "Robotics",
    title: "Diffusion-Based Visuomotor Policy Synthesis for Multi-Fingered Dexterous Manipulation",
    authors: "H. Bauer, M. Takahashi, MIT CSAIL",
    source: "MIT",
    date: "January 2026",
    abstract: "We present a unified diffusion model that maps tactile sensing matrices and RGB-D depth arrays into 24-DOF hand trajectory waypoints in real time (60 Hz). Tested across 1,200 non-rigid object grasps with zero dropped items.",
    url: "https://csail.mit.edu/research/dexterous-diffusion-policy",
    tags: ["visuomotor", "dexterous-hands", "diffusion-policy", "realtime-control"],
    citations: 38,
    doi: "10.1721.1/160114"
  },
  {
    id: "robotics-2",
    topic: "robotics",
    topicLabel: "Robotics",
    title: "Decentralized Swarm Coordination via Local Graph Attention Networks Under Intermittent RF Denial",
    authors: "A. Rossi, T. Keller, IEEE Robotics & Automation",
    source: "IEEE",
    date: "February 2026",
    abstract: "Swarm autonomy requires resilient path planning when radio communication degrades. This paper demonstrates collision-free navigation for fleets of 50+ micro-UAVs using purely optical relative localization and localized graph embeddings.",
    url: "https://ieeexplore.ieee.org/document/10423180",
    tags: ["swarm-robotics", "gnn", "rf-denied", "decentralized-control"],
    citations: 29,
    doi: "10.1109/TRO.2026.10423180"
  },

  // Physics
  {
    id: "physics-1",
    topic: "physics",
    topicLabel: "Physics",
    title: "Neural Operator Accelerators for Multi-Scale Magnetohydrodynamic Turbulence Simulation",
    authors: "F. Dubois, K. Lindemann, Harvard Physics & SEAS",
    source: "Harvard",
    date: "January 2026",
    abstract: "Fourier Neural Operators (FNO) extended with spatial gauge symmetry priors to accelerate fusion plasma containment simulations. Achieves a 420x speedup over standard Petrov-Galerkin finite element solvers while preserving energy conservation.",
    url: "https://physics.harvard.edu/research/fno-plasma-turbulences-2026",
    tags: ["fno", "plasma-physics", "neural-operators", "fusion-energy"],
    citations: 45,
    doi: "10.1103/PhysRevLett.136.045001"
  },
  {
    id: "physics-2",
    topic: "physics",
    topicLabel: "Physics",
    title: "Observation of Non-Abelian Anyonic Braiding in Solid-State Fractional Chern Insulators",
    authors: "M. S. Park, N. Varma, arXiv Physics",
    source: "arXiv",
    date: "February 2026",
    abstract: "Experimental evidence of non-Abelian topological quasiparticle braiding at zero magnetic field in twisted bilayer molybdenum ditelluride (MoTe2). Demonstrates high-coherence fault-tolerant quantum states at temperatures up to 4.2 Kelvin.",
    url: "https://arxiv.org/abs/2602.01945",
    tags: ["anyons", "condensed-matter", "fractional-chern", "topological-physics"],
    citations: 92,
    doi: "10.48550/arXiv.2602.01945"
  },

  // Quantum Computing
  {
    id: "quantum-1",
    topic: "quantum",
    topicLabel: "Quantum Computing",
    title: "Fault-Tolerant Surface Code Decoding via Real-Time Graph Neural Network Inference",
    authors: "C. Zhang, R. Hoffman, IEEE Quantum",
    source: "IEEE",
    date: "January 2026",
    abstract: "Syndrome decoding latency is the primary bottleneck for continuous error correction on superconducting quantum processors. We deploy FPGA-accelerated GNN decoders with sub-250ns inference cycles, comfortably below qubit decoherence thresholds.",
    url: "https://ieeexplore.ieee.org/document/10419820",
    tags: ["surface-codes", "syndrome-decoding", "fpga", "fault-tolerance"],
    citations: 40,
    doi: "10.1109/TQE.2026.10419820"
  },
  {
    id: "quantum-2",
    topic: "quantum",
    topicLabel: "Quantum Computing",
    title: "Neutral-Atom Quantum Architecture with High-Fidelity 3D Qubit Shuffling",
    authors: "L. Mikhailov, J. S. Endres, Harvard Quantum Initiative",
    source: "Harvard",
    date: "December 2025",
    abstract: "Demonstration of 1,200 rubidium atoms held in dynamic optical tweezer arrays with two-qubit Rydberg entangling gate fidelities exceeding 99.85%. Programmed reconfigurable topologies unlock all-to-all connectivity.",
    url: "https://quantum.harvard.edu/research/neutral-atom-3d-tweezer-array",
    tags: ["neutral-atoms", "rydberg-gates", "optical-tweezers", "quantum-processor"],
    citations: 76,
    doi: "10.1038/s41586-025-08120-x"
  },

  // Software Engineering
  {
    id: "software-1",
    topic: "software",
    topicLabel: "Software Engineering",
    title: "Establishing GitHub Workflows for App and Software Developers in the Age of AI",
    authors: "S. O'Connor, A. Vance, Institutional Research Working Group",
    source: "ACM",
    date: "February 2026",
    abstract: "A comprehensive investigation of repository architecture, branching strategies, and CI/CD pipelines when AI agents act as direct contributors. Distinguishes app developer workflows (iOS/Android) from backend package engineering, with formal governance frameworks for automated pull requests and automated security scans.",
    url: "https://dl.acm.org/doi/10.1145/3719000.3721050",
    tags: ["github-workflows", "ci-cd", "ai-agents", "security-governance", "devops"],
    citations: 18,
    doi: "10.1145/3719000.3721050"
  },
  {
    id: "software-2",
    topic: "software",
    topicLabel: "Software Engineering",
    title: "Empirical Analysis of Flaky Test Generation in LLM-Assisted Unit Test Suites",
    authors: "D. Ricci, T. M. Nguyen, ACM TOSEM",
    source: "ACM",
    date: "January 2026",
    abstract: "We evaluate 14,000 unit tests generated by leading coding models across 8 open-source repositories. Flakiness stems primarily from unseeded random generators, non-isolated filesystem access, and race conditions in mock servers.",
    url: "https://dl.acm.org/doi/10.1145/3701249",
    tags: ["test-generation", "flaky-tests", "empirical-study", "software-testing"],
    citations: 34,
    doi: "10.1145/3701249"
  },

  // Web Development
  {
    id: "webdev-1",
    topic: "webdev",
    topicLabel: "Web Development",
    title: "Zero-Latency Client-Side Edge Streaming: Server-Sent Events with Resilient Cache Reconciliation",
    authors: "J. Larsson, P. Gomez",
    source: "ACM",
    date: "January 2026",
    abstract: "Modern reactive web terminals require streaming updates under network jitter. This paper presents an optimistic client-side diffing state machine that guarantees strict linearization of partial responses over HTTP/3 QUIC streams.",
    url: "https://dl.acm.org/doi/10.1145/3699920",
    tags: ["web-streaming", "http3", "quic", "state-machines", "reactivity"],
    citations: 22,
    doi: "10.1145/3699920"
  },
  {
    id: "webdev-2",
    topic: "webdev",
    topicLabel: "Web Development",
    title: "Component-Level Security Sandboxing in Modern Frontend Micro-Frontends",
    authors: "Y. Feldman, K. Lindqvist, IEEE Software",
    source: "IEEE",
    date: "November 2025",
    abstract: "Securing third-party widgets and AI-generated UI scripts within the browser context. Explores WebAssembly-isolated component boundaries and Shadow DOM encapsulation to protect against DOM-based XSS attacks.",
    url: "https://ieeexplore.ieee.org/document/10389140",
    tags: ["micro-frontends", "browser-security", "wasm", "shadow-dom"],
    citations: 16,
    doi: "10.1109/MS.2025.10389140"
  },

  // Machine Building
  {
    id: "machinebuilding-1",
    topic: "machinebuilding",
    topicLabel: "Machine Building",
    title: "Generative Topology Optimization for Multi-Axis CNC Milling with Automated Toolpath Validation",
    authors: "E. Schneider, W. Becker, MIT Mechanical Engineering",
    source: "MIT",
    date: "February 2026",
    abstract: "Integration of level-set structural optimization with 5-axis collision checking algorithms. Generates structural brackets that are 42% lighter while reducing toolpath vibration and chatter during high-speed titanium machining.",
    url: "https://meche.mit.edu/research/cnc-topology-optimization-2026",
    tags: ["cnc-machining", "topology-optimization", "toolpath", "additive-manufacturing"],
    citations: 25,
    doi: "10.1721.1/160890"
  },
  {
    id: "machinebuilding-2",
    topic: "machinebuilding",
    topicLabel: "Machine Building",
    title: "Predictive Thermal Compensation in Ultra-Precision Machine Spindles Using Fiber Bragg Sensors",
    authors: "H. Richter, S. Vogel, IEEE Mechatronics",
    source: "IEEE",
    date: "October 2025",
    abstract: "Thermal drift accounts for over 65% of sub-micron machining errors. By embedding fiber Bragg grating sensors directly into hydrostatic ceramic spindle bearings, an adaptive Kalman filter predicts thermal growth within 80 nanometers.",
    url: "https://ieeexplore.ieee.org/document/10377490",
    tags: ["mechatronics", "thermal-drift", "fiber-bragg", "precision-engineering"],
    citations: 14,
    doi: "10.1109/TMECH.2025.10377490"
  },

  // LLM Systems & Agents
  {
    id: "llm-systems-1",
    topic: "llm-systems",
    topicLabel: "LLM Systems & Agents",
    title: "Sub-Graph Isolation and Memory Compaction for Continuous Autonomous Agents",
    authors: "M. Sterling, T. Chen, arXiv",
    source: "arXiv",
    date: "January 2026",
    abstract: "Long-running autonomous agents suffer from cognitive drift and token bloat. We present episodic sub-graph pruning where old conversational states are folded into symbolic knowledge triples with bounded retrieval latency.",
    url: "https://arxiv.org/abs/2601.11890",
    tags: ["agent-memory", "knowledge-graphs", "sub-graph-compaction", "cognitive-drift"],
    citations: 37,
    doi: "10.48550/arXiv.2601.11890"
  },

  // DevOps & CI/CD
  {
    id: "devops-cicd-1",
    topic: "devops-cicd",
    topicLabel: "DevOps & CI/CD",
    title: "Autonomous Pull Request Remediation Pipelines with Guardrail Verification",
    authors: "A. Vance, C. Moreau, ACM FSE",
    source: "ACM",
    date: "February 2026",
    abstract: "We formalize the triage, repro-step generation, and auto-patching of CI build failures through an agentic workflow. Evaluation over 500 failed GitHub Actions runs shows a 78% first-pass resolution rate without breaking external invariant tests.",
    url: "https://dl.acm.org/doi/10.1145/3720810",
    tags: ["ci-cd", "automated-remediation", "github-actions", "guardrails"],
    citations: 21,
    doi: "10.1145/3720810"
  }
];
