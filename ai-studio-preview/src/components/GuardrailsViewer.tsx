import React, { useState } from "react";
import { ShieldAlert, CheckCircle2, XCircle, AlertTriangle, Play, RefreshCw, Cpu, FileCheck } from "lucide-react";

interface GuardrailLog {
  id: string;
  timestamp: string;
  action: string;
  rule: string;
  status: "PASSED" | "BLOCKED";
  message: string;
}

export const GuardrailsViewer: React.FC = () => {
  // Pipeline simulation state
  const [hasVisualClue, setHasVisualClue] = useState<boolean>(false);
  const [evidenceCrossValidated, setEvidenceCrossValidated] = useState<boolean>(false);
  const [priorTransformPassed, setPriorTransformPassed] = useState<boolean>(true);
  const [logs, setLogs] = useState<GuardrailLog[]>([
    {
      id: "log-1",
      timestamp: "10:50:12",
      action: "Search Repositories (Topic: LLM Orchestration)",
      rule: "Rule 1: No search without a clue",
      status: "PASSED",
      message: "Verified prior visual clue exists in context frame.",
    },
    {
      id: "log-2",
      timestamp: "10:51:04",
      action: "Synthesize Final Answer",
      rule: "Rule 2: No final answer without evidence reconciliation",
      status: "BLOCKED",
      message: "GuardrailError: Action rejected. Reconciliation matrix incomplete across 2 triples.",
    },
  ]);

  const testAction = (actionType: "search" | "answer" | "transform") => {
    const time = new Date().toTimeString().split(" ")[0];
    let newLog: GuardrailLog;

    if (actionType === "search") {
      if (!hasVisualClue) {
        newLog = {
          id: `log-${Date.now()}`,
          timestamp: time,
          action: "Execute Deep Search Query",
          rule: "Rule 1: No search without a clue",
          status: "BLOCKED",
          message: "GuardrailError: Search step rejected. Visual clue flag is false.",
        };
      } else {
        newLog = {
          id: `log-${Date.now()}`,
          timestamp: time,
          action: "Execute Deep Search Query",
          rule: "Rule 1: No search without a clue",
          status: "PASSED",
          message: "Guardrail check satisfied. Query executed successfully.",
        };
      }
    } else if (actionType === "answer") {
      if (!evidenceCrossValidated) {
        newLog = {
          id: `log-${Date.now()}`,
          timestamp: time,
          action: "Emit Final Evidence Verdict",
          rule: "Rule 2: No final answer without evidence reconciliation",
          status: "BLOCKED",
          message: "GuardrailError: Final answer rejected. Evidence reconciliation pending.",
        };
      } else {
        newLog = {
          id: `log-${Date.now()}`,
          timestamp: time,
          action: "Emit Final Evidence Verdict",
          rule: "Rule 2: No final answer without evidence reconciliation",
          status: "PASSED",
          message: "Reconciliation verified against knowledge graph triples. Verdict permitted.",
        };
      }
    } else {
      if (priorTransformPassed) {
        newLog = {
          id: `log-${Date.now()}`,
          timestamp: time,
          action: "Re-apply Visual Transform",
          rule: "Rule 3: No repeated visual transform unless prior verification failed",
          status: "BLOCKED",
          message: "GuardrailError: Repeated visual transform rejected. Prior transform passed verification.",
        };
      } else {
        newLog = {
          id: `log-${Date.now()}`,
          timestamp: time,
          action: "Re-apply Visual Transform",
          rule: "Rule 3: No repeated visual transform unless prior verification failed",
          status: "PASSED",
          message: "Prior transform failed verification. Re-application permitted.",
        };
      }
    }

    setLogs((prev) => [newLog, ...prev]);
  };

  return (
    <div className="w-full">
      {/* Header */}
      <div className="border-b border-[#2a2a3a] px-6 py-6 bg-gradient-to-b from-[#0f0f1a] to-[#0a0a0f]">
        <div className="max-w-6xl mx-auto">
          <div className="flex items-center gap-2 mb-1">
            <span className="text-rose-400 text-xs font-semibold tracking-widest uppercase">
              ◈ PIPELINE_GUARDRAILS // INVARIANT ENFORCEMENT
            </span>
            <span className="text-[#555] text-xs">src/guardrails.py · stateless checker</span>
          </div>
          <h1 className="text-2xl sm:text-3xl font-normal text-[#f0ede8]">
            Agent Pipeline Guardrails
          </h1>
          <p className="text-[#888] text-xs sm:text-sm mt-1">
            Stateless runtime invariant checking preventing unjustified jumps, hallucinated conclusions, and wasteful loops
          </p>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-8">
        {/* 3 Core Invariant Rules Display */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
          <div className="p-4 bg-[#0c0c14] border border-[#1e1e2e] rounded">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] text-[#4a9eff] tracking-widest uppercase font-mono">
                RULE 1
              </span>
              <span className="text-[10px] px-1.5 py-0.5 rounded font-mono bg-blue-950/40 text-blue-400 border border-blue-800">
                INVARIANT
              </span>
            </div>
            <h3 className="text-sm font-semibold text-[#f0ede8] mb-1">
              No search without a clue
            </h3>
            <p className="text-xs text-[#888] leading-relaxed mb-3">
              For clue-dependent tasks, a search step may only proceed when a visual or preliminary step has already extracted at least one clue.
            </p>
            <div className="pt-2 border-t border-[#1a1a28] flex items-center justify-between text-xs font-mono">
              <span className="text-[#666]">Clue State:</span>
              <button
                onClick={() => setHasVisualClue(!hasVisualClue)}
                className={`px-2 py-0.5 rounded border text-[11px] ${
                  hasVisualClue
                    ? "bg-emerald-950 border-emerald-600 text-emerald-400 font-bold"
                    : "bg-rose-950 border-rose-800 text-rose-400"
                }`}
              >
                {hasVisualClue ? "CLUE EXTRACTED ✓" : "NO CLUE ✕"}
              </button>
            </div>
          </div>

          <div className="p-4 bg-[#0c0c14] border border-[#1e1e2e] rounded">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] text-amber-400 tracking-widest uppercase font-mono">
                RULE 2
              </span>
              <span className="text-[10px] px-1.5 py-0.5 rounded font-mono bg-amber-950/40 text-amber-400 border border-amber-800">
                INVARIANT
              </span>
            </div>
            <h3 className="text-sm font-semibold text-[#f0ede8] mb-1">
              No answer without reconciliation
            </h3>
            <p className="text-xs text-[#888] leading-relaxed mb-3">
              An answer step may only proceed after all collected evidence has been cross-validated across knowledge graph triples.
            </p>
            <div className="pt-2 border-t border-[#1a1a28] flex items-center justify-between text-xs font-mono">
              <span className="text-[#666]">Reconciled:</span>
              <button
                onClick={() => setEvidenceCrossValidated(!evidenceCrossValidated)}
                className={`px-2 py-0.5 rounded border text-[11px] ${
                  evidenceCrossValidated
                    ? "bg-emerald-950 border-emerald-600 text-emerald-400 font-bold"
                    : "bg-rose-950 border-rose-800 text-rose-400"
                }`}
              >
                {evidenceCrossValidated ? "VALIDATED ✓" : "PENDING ✕"}
              </button>
            </div>
          </div>

          <div className="p-4 bg-[#0c0c14] border border-[#1e1e2e] rounded">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] text-purple-400 tracking-widest uppercase font-mono">
                RULE 3
              </span>
              <span className="text-[10px] px-1.5 py-0.5 rounded font-mono bg-purple-950/40 text-purple-400 border border-purple-800">
                INVARIANT
              </span>
            </div>
            <h3 className="text-sm font-semibold text-[#f0ede8] mb-1">
              No repeat transform unless failed
            </h3>
            <p className="text-xs text-[#888] leading-relaxed mb-3">
              A visual transform may only be re-applied if the previous application of that same transform did not pass verification.
            </p>
            <div className="pt-2 border-t border-[#1a1a28] flex items-center justify-between text-xs font-mono">
              <span className="text-[#666]">Prior Pass:</span>
              <button
                onClick={() => setPriorTransformPassed(!priorTransformPassed)}
                className={`px-2 py-0.5 rounded border text-[11px] ${
                  priorTransformPassed
                    ? "bg-blue-950 border-blue-600 text-blue-400"
                    : "bg-amber-950 border-amber-800 text-amber-400"
                }`}
              >
                {priorTransformPassed ? "PRIOR PASSED (LOCK)" : "PRIOR FAILED (RETRY)"}
              </button>
            </div>
          </div>
        </div>

        {/* Action Testing Playground */}
        <div className="p-5 bg-[#0c0c14] border border-[#1e1e2e] rounded mb-8">
          <div className="text-xs text-[#aaa] font-semibold tracking-wider uppercase mb-3 flex items-center gap-2">
            <Play className="w-3.5 h-3.5 text-[#4a9eff]" /> Test Pipeline Invariant Gateways
          </div>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => testAction("search")}
              className="px-4 py-2 bg-[#142036] border border-[#2b4470] text-[#7ab8ff] text-xs font-mono uppercase tracking-wider rounded hover:bg-[#1a2c4e] transition-all"
            >
              Test Action: Execute Search
            </button>
            <button
              onClick={() => testAction("answer")}
              className="px-4 py-2 bg-[#2a1c14] border border-[#5c3e2b] text-[#ffa37a] text-xs font-mono uppercase tracking-wider rounded hover:bg-[#38261b] transition-all"
            >
              Test Action: Final Answer
            </button>
            <button
              onClick={() => testAction("transform")}
              className="px-4 py-2 bg-[#24142e] border border-[#522b63] text-[#e09eff] text-xs font-mono uppercase tracking-wider rounded hover:bg-[#321c40] transition-all"
            >
              Test Action: Re-apply Transform
            </button>
          </div>
        </div>

        {/* Guardrail Execution Log */}
        <div className="bg-[#0c0c14] border border-[#1e1e2e] rounded p-5">
          <div className="text-xs text-[#888] font-mono uppercase tracking-widest mb-3 flex items-center justify-between">
            <span>GUARDRAILS INVARIANT AUDIT LOG</span>
            <span className="text-[#555]">{logs.length} events logged</span>
          </div>

          <div className="space-y-2">
            {logs.map((log) => (
              <div
                key={log.id}
                className={`p-3 border rounded text-xs font-mono flex flex-col sm:flex-row sm:items-center justify-between gap-2 ${
                  log.status === "PASSED"
                    ? "bg-[#0b140e] border-emerald-900/60 text-emerald-300"
                    : "bg-[#170b0b] border-rose-900/60 text-rose-300"
                }`}
              >
                <div className="flex items-center gap-2">
                  {log.status === "PASSED" ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                  ) : (
                    <XCircle className="w-4 h-4 text-rose-400 shrink-0" />
                  )}
                  <span className="text-[#555]">{log.timestamp}</span>
                  <span className="font-semibold text-white">{log.action}</span>
                  <span className="text-[10px] text-[#888]">[{log.rule}]</span>
                </div>
                <div className="text-[11px] sm:text-right text-[#aaa]">
                  {log.message}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
