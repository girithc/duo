"use client";

import { useEffect, useRef, useState } from "react";

export type ExecutionTest = {
  id: string;
  status: "queued" | "running" | "passed" | "failed" | "error" | "timeout" | "repairing";
  output: string;
  returnCode: number | null;
  durationSeconds: number | null;
  error: string | null;
};

type Props = {
  tests: ExecutionTest[];
  currentTestId: string | null;
  active: boolean;
  phase: string | null;
  error: string | null;
};

function testName(id: string) {
  return id.replaceAll("-", " ");
}

function LiveOutput({ name, output }: { name: string; output: string }) {
  const outputRef = useRef<HTMLPreElement>(null);

  useEffect(() => {
    if (outputRef.current) outputRef.current.scrollTop = outputRef.current.scrollHeight;
  }, [output]);

  return (
    <pre
      ref={outputRef}
      aria-label={`${testName(name)} execution output`}
      className="mt-2 min-h-32 max-h-96 overflow-auto rounded-md bg-neutral-100 p-4 font-mono text-xs leading-5 whitespace-pre-wrap break-words text-neutral-900"
    >
      {output}
    </pre>
  );
}

const statusLabels: Record<ExecutionTest["status"], string> = {
  queued: "Queued",
  running: "Running",
  passed: "Passed",
  failed: "Failed assertions",
  error: "Execution error",
  timeout: "Timed out",
  repairing: "Repairing",
};

export default function Section4({ tests, currentTestId, active, phase, error }: Props) {
  const [expandedTests, setExpandedTests] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (currentTestId) setExpandedTests(new Set([currentTestId]));
  }, [currentTestId]);

  function toggleTest(id: string) {
    setExpandedTests((expanded) => {
      const next = new Set(expanded);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  const passed = tests.filter((test) => test.status === "passed").length;
  const failed = tests.filter((test) => test.status === "failed").length;
  const errors = tests.filter((test) => ["error", "timeout"].includes(test.status)).length;
  const running = tests.filter((test) => ["running", "repairing"].includes(test.status)).length;
  const queued = tests.filter((test) => test.status === "queued").length;

  return (
    <section aria-label="Execution" aria-busy={active} className="flex-1 bg-white p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-base font-medium text-neutral-900">Execution</h2>
        {active && (
          <span role="status" className="text-xs text-neutral-500">
            {phase === "preparing" ? "Preparing environment" : "Running tests"}
          </span>
        )}
      </div>

      {tests.length > 0 && (
        <p role="status" aria-live="polite" className="mt-2 text-xs text-neutral-500">
          {passed} passed · {failed} failed assertions · {errors} errors/timeouts · {running} running · {queued} queued
        </p>
      )}

      {error && (
        <pre
          role="alert"
          aria-label="Execution pipeline error"
          className="mt-4 max-h-64 overflow-auto rounded-md bg-red-50 p-3 text-xs whitespace-pre-wrap break-words text-red-700"
        >
          {error}
        </pre>
      )}

      {tests.length > 0 && (
        <ul className="mt-5 space-y-4">
          {tests.map((test) => {
            const name = testName(test.id);
            const expanded = expandedTests.has(test.id);
            const panelId = `execution-output-${test.id}`;
            const hasFailure = ["failed", "error", "timeout"].includes(test.status);
            return (
              <li key={test.id} data-execution-test={test.id}>
                <div className="flex items-center justify-between gap-4">
                  <h3 className="min-w-0 flex-1 text-sm font-medium text-neutral-800">
                    <button
                      type="button"
                      aria-expanded={expanded}
                      aria-controls={panelId}
                      onClick={() => toggleTest(test.id)}
                      className="flex min-w-0 items-center gap-2 text-left hover:text-neutral-500 focus:outline-none focus-visible:ring-2 focus-visible:ring-neutral-900/20"
                    >
                      <svg
                        viewBox="0 0 16 16"
                        fill="none"
                        aria-hidden="true"
                        className={`h-4 w-4 shrink-0 transition-transform ${expanded ? "rotate-90" : ""}`}
                      >
                        <path d="m6 4 4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                      <span className="truncate">{name}</span>
                    </button>
                  </h3>
                  <div className="shrink-0 text-right text-xs">
                    <span className={hasFailure ? "text-red-600" : test.status === "passed" ? "text-green-700" : "text-neutral-500"}>
                      {statusLabels[test.status]}
                    </span>
                    {test.durationSeconds !== null && (
                      <span className="ml-2 text-neutral-400">{test.durationSeconds.toFixed(1)}s</span>
                    )}
                    {test.returnCode !== null && (
                      <span className="ml-2 text-neutral-400">exit {test.returnCode}</span>
                    )}
                  </div>
                </div>

                <div id={panelId} hidden={!expanded}>
                  {test.output.length > 0 && <LiveOutput name={test.id} output={test.output} />}
                </div>
                {test.error && (
                  <pre className="mt-2 max-h-56 overflow-auto rounded-md bg-red-50 p-3 text-xs whitespace-pre-wrap break-words text-red-700">
                    {test.error}
                  </pre>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
