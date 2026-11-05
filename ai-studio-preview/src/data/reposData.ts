export interface PolicyAnalysis {
  privacy_summary: string;
  severity_counts: {
    high: number;
    medium: number;
    low: number;
  };
  third_party_mentions: string[];
  data_sharing_references: string[];
  detected_technologies: string[];
}

export interface ScoredRepository {
  id: string;
  name: string;
  full_name: string;
  url: string;
  description: string;
  relevance_score: number;
  summary: string;
  reason: string;
  stars: number;
  forks: number;
  language: string;
  license: string;
  topics: string[];
  updated_at: string;
  policy: PolicyAnalysis;
}

export const INITIAL_REPOSITORIES: ScoredRepository[] = [
  {
    id: "repo-1",
    name: "vllm",
    full_name: "vllm-project/vllm",
    url: "https://github.com/vllm-project/vllm",
    description: "A high-throughput and memory-efficient inference and serving engine for LLMs.",
    relevance_score: 96,
    summary: "vLLM delivers state-of-the-art throughput and low latency serving for large language models through PagedAttention. It enables high-concurrency LLM research and production serving with tensor parallel execution and continuous batching.",
    reason: "Directly solves the critical bottleneck of LLM inference throughput and memory fragmentation in research infrastructure.",
    stars: 38240,
    forks: 5690,
    language: "Python",
    license: "Apache-2.0",
    topics: ["llm", "inference", "deep-learning", "paged-attention", "gpu"],
    updated_at: "2026-10-25",
    policy: {
      privacy_summary: "Local runtime execution. No mandatory user telemetry or cloud payload transmission. Open source Apache-2.0 with clean dependency tree.",
      severity_counts: { high: 0, medium: 0, low: 1 },
      third_party_mentions: ["NVIDIA CUDA", "ROCm", "PyTorch", "Hugging Face"],
      data_sharing_references: ["Model weight downloads from Hugging Face Hub (user opt-in)"],
      detected_technologies: ["C++ CUDA Kernels", "PyTorch C extensions", "Triton", "FastAPI"]
    }
  },
  {
    id: "repo-2",
    name: "anthropic-sdk-python",
    full_name: "anthropics/anthropic-sdk-python",
    url: "https://github.com/anthropics/anthropic-sdk-python",
    description: "Official Python library for the Anthropic Claude API.",
    relevance_score: 91,
    summary: "Official client library for orchestrating Claude 3.5 Sonnet, Claude 4.5, and multimodal reasoning pipelines with typed streaming, tool calling, and prompt caching primitives.",
    reason: "Essential developer SDK for foundation model interaction, research evaluations, and structured tool workflows.",
    stars: 8450,
    forks: 920,
    language: "Python",
    license: "MIT",
    topics: ["anthropic", "claude", "llm-api", "ai-agents", "python-sdk"],
    updated_at: "2026-10-24",
    policy: {
      privacy_summary: "Transmits API requests over TLS to Anthropic endpoint. Adheres to Anthropic enterprise data privacy agreements with zero model training on API traffic.",
      severity_counts: { high: 0, medium: 1, low: 0 },
      third_party_mentions: ["Anthropic API Cloud", "httpx", "pydantic"],
      data_sharing_references: ["Prompts and responses processed according to Anthropic Commercial Terms"],
      detected_technologies: ["httpx", "pydantic v2", "typing-extensions"]
    }
  },
  {
    id: "repo-3",
    name: "autogen",
    full_name: "microsoft/autogen",
    url: "https://github.com/microsoft/autogen",
    description: "A programming framework for agentic AI that enables multiple conversational agents to solve tasks.",
    relevance_score: 89,
    summary: "Microsoft AutoGen enables multi-agent conversation patterns where specialized LLM agents collaborate, execute verified shell scripts, critique intermediate solutions, and coordinate with human operators.",
    reason: "Premier research framework for multi-agent coordination topologies and empirical agent benchmark experiments.",
    stars: 36400,
    forks: 5310,
    language: "Python",
    license: "Creative Commons / MIT",
    topics: ["agents", "multi-agent", "llm", "conversational-ai", "orchestration"],
    updated_at: "2026-10-26",
    policy: {
      privacy_summary: "Executes arbitrary generated code in configured sandbox docker containers. Requires strict isolation guardrails to prevent host command breakout.",
      severity_counts: { high: 1, medium: 1, low: 0 },
      third_party_mentions: ["Docker Engine", "OpenAI API", "Azure OpenAI"],
      data_sharing_references: ["LLM vendor endpoints for conversation context logs"],
      detected_technologies: ["Docker SDK", "OpenAI Client", "ChromaDB", "Python AST"]
    }
  },
  {
    id: "repo-4",
    name: "ollama",
    full_name: "ollama/ollama",
    url: "https://github.com/ollama/ollama",
    description: "Get up and running with Llama 3.3, Mistral, Gemma 2, and other large language models locally.",
    relevance_score: 94,
    summary: "Ollama packages open-weight model weights, quantization formats (GGUF), and local HTTP API servers into an intuitive cross-platform tool for running foundation models completely on-device.",
    reason: "Standard tool for privacy-preserving local LLM execution, zero-cloud data sovereignty, and offline research testing.",
    stars: 104200,
    forks: 9280,
    language: "Go",
    license: "MIT",
    topics: ["local-llm", "gguf", "llama", "deep-learning", "offline-ai"],
    updated_at: "2026-10-27",
    policy: {
      privacy_summary: "100% offline, local-first execution. Zero telemetry or prompt uploads to cloud servers. Maximum privacy score.",
      severity_counts: { high: 0, medium: 0, low: 0 },
      third_party_mentions: ["Ollama Registry (for downloading weights)"],
      data_sharing_references: ["Zero data sharing during inference"],
      detected_technologies: ["Go runtime", "llama.cpp backend", "Metal / CUDA bindings"]
    }
  },
  {
    id: "repo-5",
    name: "transformers",
    full_name: "huggingface/transformers",
    url: "https://github.com/huggingface/transformers",
    description: "State-of-the-art Machine Learning for Pytorch, TensorFlow, and JAX.",
    relevance_score: 98,
    summary: "The definitive open-source toolkit for thousands of pretrained neural architectures across text, vision, audio, and multimodal domains, backed by standard tokenizers and training loops.",
    reason: "Universal foundational library upon which the vast majority of academic ML and generative AI research is implemented.",
    stars: 136000,
    forks: 26500,
    language: "Python",
    license: "Apache-2.0",
    topics: ["transformers", "pytorch", "deep-learning", "nlp", "vision", "speech"],
    updated_at: "2026-10-27",
    policy: {
      privacy_summary: "Permissive Apache-2.0. Optional analytics telemetry disabled via HF_HUB_DISABLE_TELEMETRY=1 env flag.",
      severity_counts: { high: 0, medium: 0, low: 1 },
      third_party_mentions: ["Hugging Face Hub", "PyTorch", "SafeTensors"],
      data_sharing_references: ["Model checkpoint cache sync with Hub"],
      detected_technologies: ["PyTorch", "SafeTensors", "Tokenizers Rust", "FlashAttention"]
    }
  },
  {
    id: "repo-6",
    name: "uv",
    full_name: "astral-sh/uv",
    url: "https://github.com/astral-sh/uv",
    description: "An extremely fast Python package and project manager, written in Rust.",
    relevance_score: 82,
    summary: "uv replaces pip, pip-tools, virtualenv, and poetry with a blazing 10-100x faster package resolver and workspace orchestrator, dramatically accelerating research experiment reproducibility.",
    reason: "High impact on AI research productivity and deterministic environment setup across deep learning clusters.",
    stars: 43200,
    forks: 1420,
    language: "Rust",
    license: "Apache-2.0 / MIT",
    topics: ["rust", "python", "packaging", "virtualenv", "performance"],
    updated_at: "2026-10-26",
    policy: {
      privacy_summary: "Deterministic lockfiles and SHA-256 hash enforcement. No user profiling.",
      severity_counts: { high: 0, medium: 0, low: 0 },
      third_party_mentions: ["PyPI", "GitHub Releases"],
      data_sharing_references: ["Only standard HTTP index queries to PyPI"],
      detected_technologies: ["Rust", "Tokio", "Reqwest", "PubGrub resolver"]
    }
  }
];
