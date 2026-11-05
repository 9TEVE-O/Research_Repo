import React, { useState } from "react";
import { CheckCircle2, XCircle, AlertCircle, HelpCircle, Shield, Hash, Clock, FileCheck, ArrowRight, Play, RefreshCw } from "lucide-react";

interface ClassificationReceipt {
  status: "SUPPORTED" | "CONTRADICTED" | "INSUFFICIENT" | "ABSTAIN";
  confidence: number;
  contract_version: string;
  model: string;
  evaluated_at: string;
  input_hash: string;
  review_required: boolean;
  promotion_status: string;
  token_usage: {
    input_tokens: number;
    output_tokens: number;
  };
  reasoning: string;
}

const PRESET_EXAMPLES = [
  {
    id: "mit-licence",
    label: "Example 1: MIT Licence (Synthetic Record)",
    claim: "This example project uses the MIT licence.",
    source_text: "Example project README: Licence: MIT.",
    source_url: "https://example.org/project",
    source_accessed_at: "2026-10-07",
    expected: "SUPPORTED" as const,
  },
  {
    id: "quantum-claim",
    label: "Example 2: Topological Braiding Claim",
    claim: "Non-Abelian anyonic braiding was observed at room temperature in graphene.",
    source_text: "Experimental evidence of non-Abelian topological quasiparticle braiding in twisted bilayer MoTe2 was confirmed at 4.2 Kelvin under zero magnetic field.",
    source_url: "https://arxiv.org/abs/2602.01945",
    source_accessed_at: "2026-10-25",
    expected: "CONTRADICTED" as const,
  },
  {
    id: "inference-speed",
    label: "Example 3: Partial Proof (Insufficient Scope)",
    claim: "vLLM achieves 100x speedup across all hardware architectures.",
    source_text: "vLLM delivers up to 2-4x higher throughput compared to Hugging Face TGI on NVIDIA A100 GPUs using PagedAttention.",
    source_url: "https://vllm.ai/benchmarks",
    source_accessed_at: "2026-10-26",
    expected: "INSUFFICIENT" as const,
  },
  {
    id: "ambiguous-text",
    label: "Example 4: Conflicting Evidence (Abstain)",
    claim: "Model safety alignment prevents all jailbreak attempts.",
    source_text: "Preliminary benchmark runs showed 0% bypass rate on dataset Alpha, but third-party red-teaming reported conflicting results with 34% adversarial penetration on multi-turn prompts.",
    source_url: "https://ai-safety.org/reports/eval",
    source_accessed_at: "2026-10-24",
    expected: "ABSTAIN" as const,
  },
];

// Helper to compute a simple SHA-256 representation in browser
async function computeSha256(text: string): Promise<string> {
  const encoder = new TextEncoder();
  const data = encoder.encode(text);
  const hashBuffer = await crypto.subtle.digest("SHA-256", data);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  return hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");
}

export const TypeSafeClassifier: React.FC = () => {
  const [claim, setClaim] = useState(PRESET_EXAMPLES[0].claim);
  const [sourceText, setSourceText] = useState(PRESET_EXAMPLES[0].source_text);
  const [sourceUrl, setSourceUrl] = useState(PRESET_EXAMPLES[0].source_url);
  const [sourceAccessedAt, setSourceAccessedAt] = useState(PRESET_EXAMPLES[0].source_accessed_at);
  // No external model is configured. This is a local rule-based demonstration.
  const [loading, setLoading] = useState(false);
  const [receipt, setReceipt] = useState<ClassificationReceipt | null>(null);

  const loadPreset = (preset: typeof PRESET_EXAMPLES[0]) => {
    setClaim(preset.claim);
    setSourceText(preset.source_text);
    setSourceUrl(preset.source_url);
    setSourceAccessedAt(preset.source_accessed_at);
    setReceipt(null);
  };

  const runClassification = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!claim.trim() || !sourceText.trim() || !sourceUrl.trim() || !sourceAccessedAt.trim()) return;

    setLoading(true);
    setReceipt(null);

    // Compute input hash
    const inputCanonical = JSON.stringify({
      claim: claim.trim(),
      source_text: sourceText.trim(),
      source_url: sourceUrl.trim(),
      source_accessed_at: sourceAccessedAt.trim(),
    });
    const hash = await computeSha256(inputCanonical);

    // Realistic evaluation latency
    await new Promise((r) => setTimeout(r, 650));

    // Evaluation logic matching typesafe criteria
    let outcome: "SUPPORTED" | "CONTRADICTED" | "INSUFFICIENT" | "ABSTAIN" = "SUPPORTED";
    let reasoning = "";

    const cLower = claim.toLowerCase();
    const sLower = sourceText.toLowerCase();

    if (cLower.includes("room temperature") && sLower.includes("4.2 kelvin")) {
      outcome = "CONTRADICTED";
      reasoning = "Source states the experiment was confirmed at 4.2 Kelvin, which directly contradicts the claim of room temperature.";
    } else if (cLower.includes("100x") && sLower.includes("2-4x")) {
      outcome = "INSUFFICIENT";
      reasoning = "Source demonstrates 2-4x throughput on A100 GPUs, failing to substantiate the broad 100x claim across all hardware.";
    } else if (sLower.includes("conflicting") || sLower.includes("ambiguous")) {
      outcome = "ABSTAIN";
      reasoning = "The supplied text explicitly acknowledges conflicting red-teaming benchmarks, rendering an automated determination unreliable.";
    } else if (sLower.includes("mit") && cLower.includes("mit")) {
      outcome = "SUPPORTED";
      reasoning = "Local demonstration rule matched MIT in both text fields. This does not verify a licence or source.";
    } else {
      outcome = "ABSTAIN";
      reasoning = "Local rules cannot evaluate this claim. No external source or provider model has been checked.";
    }

    setReceipt({
      status: outcome,
      confidence: outcome === "ABSTAIN" ? 0.45 : outcome === "INSUFFICIENT" ? 0.72 : 0.98,
      contract_version: "claim-source-support-v0.1",
      model: "local-rules-demo (not a TypeSafe model)",
      evaluated_at: new Date().toISOString(),
      input_hash: hash,
      review_required: true,
      promotion_status: "NOT_PROMOTED",
      token_usage: {
        input_tokens: 0,
        output_tokens: 0,
      },
      reasoning: reasoning,
    });

    setLoading(false);
  };

  const outcomeConfig = {
    SUPPORTED: {
      color: "text-emerald-400",
      bg: "bg-emerald-950/40",
      border: "border-emerald-500",
      icon: CheckCircle2,
      desc: "The supplied source directly supports the full claim, including its scope and qualifications.",
    },
    CONTRADICTED: {
      color: "text-rose-400",
      bg: "bg-rose-950/40",
      border: "border-rose-500",
      icon: XCircle,
      desc: "The supplied source directly contradicts the claim.",
    },
    INSUFFICIENT: {
      color: "text-amber-400",
      bg: "bg-amber-950/40",
      border: "border-amber-500",
      icon: AlertCircle,
      desc: "The source is relevant but does not establish or contradict the full claim.",
    },
    ABSTAIN: {
      color: "text-gray-400",
      bg: "bg-gray-900/50",
      border: "border-gray-500",
      icon: HelpCircle,
      desc: "The material is ambiguous, conflicting, or cannot be assessed reliably.",
    },
  };

  return (
    <div className="w-full">
      {/* Header */}
      <div className="border-b border-[#2a2a3a] px-6 py-6 bg-gradient-to-b from-[#0f0f1a] to-[#0a0a0f]">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-[#38bdf8] text-xs font-semibold tracking-widest uppercase">
              ◈ TYPESAFE_EVIDENCE // CLAIM CLASSIFICATION (OPT-IN)
            </span>
            <span className="text-[#555] text-xs">typesafe_evidence.py · claim-source-support-v0.1</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-normal text-[#f0ede8]">
            TypeSafe Evidence Verification
          </h1>
          <p className="text-[#888] text-xs sm:text-sm mt-1">
            Simulated classification using local heuristics only; not connected to TypeSafe or any model. Input sources and outcomes are not verified.
          </p>
          <p role="status" className="mt-3 rounded border border-amber-700/50 bg-amber-950/30 p-3 text-xs text-amber-200">
            LOCAL HEURISTICS DEMO · No TypeSafe provider request, authenticated model evaluation, independent source check or real token usage. Results are illustrative and must not be treated as verified findings.
          </p>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* Preset Selector */}
        <div className="mb-6 p-4 bg-[#0c0c14] border border-[#1e1e2e] rounded">
          <div className="text-[10px] text-[#666] tracking-widest uppercase font-mono mb-2">
            ▸ LOAD PRESET TESTBENCH RECORDS (examples/typesafe_claim.json)
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-2">
            {PRESET_EXAMPLES.map((p) => (
              <button
                key={p.id}
                onClick={() => loadPreset(p)}
                className="p-2.5 text-left text-xs bg-[#111118] border border-[#232338] hover:border-[#4a9eff] rounded transition-all flex flex-col justify-between"
              >
                <div className="text-[#bbb] font-semibold mb-1 truncate">{p.label}</div>
                <div className="text-[10px] text-[#666] font-mono">
                  Expected: <span className="text-[#7ab8ff]">{p.expected}</span>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Input Form & Evaluation Receipt */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Left: Input Form */}
          <form onSubmit={runClassification} className="bg-[#0c0c14] border border-[#1e1e2e] rounded p-5 space-y-4">
            <div className="text-xs text-[#7ab8ff] font-semibold tracking-wider uppercase flex items-center justify-between">
              <span className="flex items-center gap-2">
                <Shield className="w-4 h-4 text-[#4a9eff]" /> Authorised Evidence Input Boundary
              </span>
              <span className="text-[#555] font-mono">4 authorized fields</span>
            </div>

            {/* Claim */}
            <div>
              <label className="text-[11px] text-[#aaa] font-mono block mb-1">
                1. Claim <span className="text-[#555]">(assertion to assess)</span>
              </label>
              <textarea
                rows={2}
                value={claim}
                onChange={(e) => setClaim(e.target.value)}
                required
                className="w-full bg-[#111118] border border-[#2a2a3a] text-xs text-[#e8e6e1] p-2.5 rounded outline-none focus:border-[#4a9eff] font-mono"
              />
            </div>

            {/* Source Text */}
            <div>
              <label className="text-[11px] text-[#aaa] font-mono block mb-1">
                2. Source Text <span className="text-[#555]">(untrusted evidence excerpt)</span>
              </label>
              <textarea
                rows={3}
                value={sourceText}
                onChange={(e) => setSourceText(e.target.value)}
                required
                className="w-full bg-[#111118] border border-[#2a2a3a] text-xs text-[#e8e6e1] p-2.5 rounded outline-none focus:border-[#4a9eff] font-mono"
              />
            </div>

            {/* Source URL & Accessed Date */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="text-[11px] text-[#aaa] font-mono block mb-1">
                  3. Source URL
                </label>
                <input
                  type="text"
                  value={sourceUrl}
                  onChange={(e) => setSourceUrl(e.target.value)}
                  required
                  className="w-full bg-[#111118] border border-[#2a2a3a] text-xs text-[#e8e6e1] p-2 rounded outline-none focus:border-[#4a9eff] font-mono"
                />
              </div>

              <div>
                <label className="text-[11px] text-[#aaa] font-mono block mb-1">
                  4. Source Accessed At
                </label>
                <input
                  type="text"
                  value={sourceAccessedAt}
                  onChange={(e) => setSourceAccessedAt(e.target.value)}
                  required
                  className="w-full bg-[#111118] border border-[#2a2a3a] text-xs text-[#e8e6e1] p-2 rounded outline-none focus:border-[#4a9eff] font-mono"
                />
              </div>
            </div>

            {/* Model & Submit */}
            <div className="pt-2 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <span className="text-[10px] text-[#aaa] font-mono uppercase">Local heuristics demo · no model call</span>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="px-6 py-2.5 bg-[#0a2a5a] border border-[#4a9eff] text-[#4a9eff] hover:bg-[#103875] hover:text-white rounded text-xs font-mono uppercase tracking-wider font-semibold transition-all flex items-center gap-2"
              >
                {loading ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" /> Assessing...
                  </>
                ) : (
                  <>
                    <Play className="w-3.5 h-3.5" /> Assess Evidence
                  </>
                )}
              </button>
            </div>
          </form>

          {/* Right: TypeSafe Evaluation Receipt */}
          <div className="bg-[#0c0c14] border border-[#1e1e2e] rounded p-5 flex flex-col justify-between">
            <div>
              <div className="text-xs text-emerald-400 font-semibold tracking-wider uppercase mb-4 flex items-center justify-between">
                <span className="flex items-center gap-2">
                  <FileCheck className="w-4 h-4 text-emerald-400" /> Local Simulation Receipt (Not Provider-Generated)
                </span>
                <span className="text-[10px] text-[#666] font-mono">contract: claim-source-support-v0.1</span>
              </div>

              {receipt ? (
                <div className="space-y-4">
                  {/* Outcome Banner */}
                  {(() => {
                    const cfg = outcomeConfig[receipt.status];
                    const Icon = cfg.icon;
                    return (
                      <div className={`p-4 border ${cfg.border} ${cfg.bg} rounded`}>
                        <div className="flex items-center justify-between mb-1.5">
                          <div className={`text-base font-bold font-mono ${cfg.color} flex items-center gap-2`}>
                            <Icon className="w-5 h-5" />
                            {receipt.status}
                          </div>
                          <span className="text-xs font-mono text-[#aaa]">
                            local demo · not verified
                          </span>
                        </div>
                        <div className="text-xs text-[#ddd] mb-2 font-mono">
                          {cfg.desc}
                        </div>
                        <div className="text-xs text-[#ccc] bg-[#0a0a0f]/60 p-2 border border-[#2a2a3a] rounded font-sans leading-relaxed">
                          <span className="font-semibold text-white">Evaluation note: </span>
                          {receipt.reasoning}
                        </div>
                      </div>
                    );
                  })()}

                  {/* Cryptographic SHA-256 Input Hash */}
                  <div className="p-3 bg-[#0a0a0f] border border-[#1e1e2e] rounded font-mono text-xs">
                    <div className="text-[10px] text-[#666] uppercase mb-1 flex items-center gap-1">
                      <Hash className="w-3 h-3 text-[#4a9eff]" /> SHA-256 Input Hash (State Binding):
                    </div>
                    <div className="text-[#7ab8ff] text-[11px] break-all">
                      {receipt.input_hash}
                    </div>
                  </div>

                  {/* Invariant Flags */}
                  <div className="grid grid-cols-2 gap-3 text-xs font-mono">
                    <div className="p-2.5 bg-[#0a0a0f] border border-[#1e1e2e] rounded">
                      <div className="text-[10px] text-[#666] uppercase">Review Required:</div>
                      <div className="text-amber-400 font-bold">
                        {String(receipt.review_required).toUpperCase()} (Human In Loop)
                      </div>
                    </div>
                    <div className="p-2.5 bg-[#0a0a0f] border border-[#1e1e2e] rounded">
                      <div className="text-[10px] text-[#666] uppercase">Promotion Status:</div>
                      <div className="text-rose-400 font-bold">
                        {receipt.promotion_status}
                      </div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="p-12 text-center text-xs text-[#555] border border-dashed border-[#222233] rounded">
                  Submit sample inputs for a local-rule simulation. An input hash does not verify the source or outcome.
                </div>
              )}
            </div>

            {/* Bottom Timestamp & Metrics */}
            {receipt && (
              <div className="pt-4 mt-4 border-t border-[#181824] flex items-center justify-between text-[11px] text-[#555] font-mono">
                <span className="flex items-center gap-1">
                  <Clock className="w-3 h-3" /> {receipt.evaluated_at}
                </span>
                <span>
                  no model invoked · tokens: 0
                </span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
