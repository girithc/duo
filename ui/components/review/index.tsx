"use client";

import { type FormEvent, useEffect, useRef, useState } from "react";
import Section1 from "./section-1";
import Section2 from "./section-2";
import Section3, { type WriterTest } from "./section-3";
import Section4, { type ExecutionTest } from "./section-4";

const API_URL = (process.env.NEXT_PUBLIC_DUO_API_URL ?? "http://localhost:8000").replace(/\/$/, "");

type RunEvent = {
  event?: string;
  stage?: string;
  phase?: string;
  selected?: boolean;
  leaf_id?: string;
  leaf_ids?: string[];
  delta?: string;
  code?: string;
  stream?: "stdout" | "stderr";
  text?: string;
  status?: string;
  returncode?: number | null;
  seconds?: number;
  round?: number;
  error?: string;
  traceback?: string;
};

type RunResponse = {
  run_id: string;
  events: string;
};

function streamedCode(raw: string) {
  const openingFence = raw.match(/^\s*```(?:python)?[ \t]*\r?\n/i);
  if (!openingFence) return raw;
  return raw.slice(openingFence[0].length).replace(/\r?\n```[^\n]*$/, "");
}

function executionStatus(status: string | undefined) {
  if (status === "passed" || status === "failed" || status === "error" || status === "timeout") {
    return status;
  }
  return null;
}

export default function Review() {
  const [repositoryUrl, setRepositoryUrl] = useState("");
  const [pullRequest, setPullRequest] = useState("");
  const [running, setRunning] = useState(false);
  const [cloning, setCloning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [decisionActive, setDecisionActive] = useState(false);
  const [testTypes, setTestTypes] = useState<string[]>([]);
  const [writerActive, setWriterActive] = useState(false);
  const [writerTests, setWriterTests] = useState<WriterTest[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [writerError, setWriterError] = useState<string | null>(null);
  const [executionActive, setExecutionActive] = useState(false);
  const [executionPhase, setExecutionPhase] = useState<string | null>(null);
  const [executionTests, setExecutionTests] = useState<ExecutionTest[]>([]);
  const [currentExecutionId, setCurrentExecutionId] = useState<string | null>(null);
  const [executionError, setExecutionError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => () => eventSourceRef.current?.close(), []);

  function resetResult() {
    setProgress(0);
    setCloning(false);
    setDecisionActive(false);
    setTestTypes([]);
    setWriterActive(false);
    setWriterTests([]);
    setError(null);
    setWriterError(null);
    setExecutionActive(false);
    setExecutionPhase(null);
    setExecutionTests([]);
    setCurrentExecutionId(null);
    setExecutionError(null);
  }

  function updateWriterTest(id: string, update: Partial<Omit<WriterTest, "id">>) {
    setWriterTests((tests) => {
      const index = tests.findIndex((test) => test.id === id);
      if (index === -1) {
        return [...tests, { id, code: "", status: "generating", error: null, ...update }];
      }
      return tests.map((test, testIndex) => testIndex === index ? { ...test, ...update } : test);
    });
  }

  function updateExecutionTest(id: string, update: Partial<Omit<ExecutionTest, "id">>) {
    setExecutionTests((tests) => {
      const test: ExecutionTest = {
        id,
        status: "queued",
        output: "",
        returnCode: null,
        durationSeconds: null,
        error: null,
      };
      const index = tests.findIndex((entry) => entry.id === id);
      if (index === -1) return [...tests, { ...test, ...update }];
      return tests.map((entry, entryIndex) => entryIndex === index ? { ...entry, ...update } : entry);
    });
  }

  function appendExecutionOutput(id: string, text: string) {
    setExecutionTests((tests) => {
      const index = tests.findIndex((test) => test.id === id);
      if (index === -1) {
        return [...tests, {
          id, status: "running", output: text, returnCode: null, durationSeconds: null, error: null,
        }];
      }
      return tests.map((test, testIndex) => testIndex === index
        ? { ...test, status: "running", output: test.output + text }
        : test);
    });
  }

  async function startReview(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (running) return;

    eventSourceRef.current?.close();
    resetResult();
    setProgress(1);
    setCloning(true);
    setRunning(true);
    let writerStageStarted = false;
    let executionStageStarted = false;

    try {
      const response = await fetch(`${API_URL}/runs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          target: repositoryUrl.trim(),
          pr: pullRequest.trim(),
          stop_after: "sandbox",
        }),
      });
      const payload = (await response.json()) as RunResponse & { detail?: unknown };

      if (!response.ok) {
        const detail = payload.detail ?? payload;
        throw new Error(`Duo API ${response.status}: ${
          typeof detail === "string" ? detail : JSON.stringify(detail)
        }`);
      }
      if (typeof payload.events !== "string") {
        throw new Error("Duo API response is missing the run event stream path");
      }

      setProgress(5);
      const source = new EventSource(new URL(payload.events, `${API_URL}/`));
      eventSourceRef.current = source;
      let settled = false;
      const rawCode = new Map<string, string>();

      function finish(message?: string) {
        if (settled) return;
        settled = true;
        source.close();
        if (eventSourceRef.current === source) eventSourceRef.current = null;
        setRunning(false);
        setCloning(false);
        setWriterActive(false);
        setExecutionActive(false);
        if (message) {
          if (executionStageStarted) setExecutionError(message);
          else if (writerStageStarted) setWriterError(message);
          else {
            setError(message);
            setDecisionActive(false);
          }
        }
      }

      source.onmessage = (message) => {
        let runEvent: RunEvent;
        try {
          runEvent = JSON.parse(message.data) as RunEvent;
        } catch {
          finish(`Invalid event stream data: ${message.data}`);
          return;
        }

        switch (runEvent.event) {
          case "run_start":
            setProgress((value) => Math.max(value, 10));
            break;
          case "pr":
            break;
          case "stage_start":
            if (runEvent.stage === "clone") setProgress((value) => Math.max(value, 15));
            if (runEvent.stage === "curate") setDecisionActive(true);
            if (runEvent.stage === "write") {
              writerStageStarted = true;
              setDecisionActive(false);
              setWriterActive(true);
            }
            if (runEvent.stage === "sandbox") {
              executionStageStarted = true;
              setWriterActive(false);
              setExecutionActive(true);
              setExecutionPhase("preparing");
            }
            break;
          case "clone_progress": {
            const phaseProgress = {
              pr_fetched: 30,
              snapshot_ready: 50,
              contract_written: 75,
            }[runEvent.phase ?? ""];
            if (phaseProgress) setProgress((value) => Math.max(value, phaseProgress));
            break;
          }
          case "stage_end":
            if (runEvent.stage === "clone") {
              setProgress(100);
              setCloning(false);
            }
            if (runEvent.stage === "write") setWriterActive(false);
            if (runEvent.stage === "sandbox") setExecutionPhase("completed");
            break;
          case "family_gate":
            setDecisionActive(true);
            break;
          case "type_verdict":
            setDecisionActive(true);
            if (runEvent.leaf_id && runEvent.selected === true) {
              const selectedId = runEvent.leaf_id;
              setTestTypes((types) => types.includes(selectedId) ? types : [...types, selectedId]);
            }
            break;
          case "test_started":
            if (runEvent.leaf_id) {
              setWriterActive(true);
              updateWriterTest(runEvent.leaf_id, {
                code: "", status: "generating", error: null,
              });
            }
            break;
          case "test_code_delta":
            if (runEvent.leaf_id && typeof runEvent.delta === "string") {
              const combined = (rawCode.get(runEvent.leaf_id) ?? "") + runEvent.delta;
              rawCode.set(runEvent.leaf_id, combined);
              updateWriterTest(runEvent.leaf_id, { code: streamedCode(combined) });
            }
            break;
          case "test_code":
            if (runEvent.leaf_id && typeof runEvent.code === "string") {
              rawCode.set(runEvent.leaf_id, runEvent.code);
              updateWriterTest(runEvent.leaf_id, { code: runEvent.code });
            }
            break;
          case "write_progress":
            break;
          case "test_written":
            if (runEvent.leaf_id) {
              const leafId = runEvent.leaf_id;
              updateWriterTest(leafId, {
                ...(typeof runEvent.code === "string" ? { code: runEvent.code } : {}),
                status: runEvent.status === "ok" ? "written" : "error",
                error: runEvent.traceback ?? runEvent.error ?? null,
              });
            }
            break;
          case "execution_queued":
            if (Array.isArray(runEvent.leaf_ids) && runEvent.leaf_ids.every((id) => typeof id === "string")) {
              setExecutionTests(runEvent.leaf_ids.map((id) => ({
                id, status: "queued", output: "", returnCode: null, durationSeconds: null, error: null,
              })));
              setExecutionActive(true);
              setExecutionPhase("preparing");
            }
            break;
          case "execution_phase":
            if (runEvent.phase === "preparing" || runEvent.phase === "running") {
              setExecutionPhase(runEvent.phase);
              if (runEvent.phase === "running") setExecutionActive(true);
            }
            break;
          case "execution_started":
            if (runEvent.leaf_id) {
              setCurrentExecutionId(runEvent.leaf_id);
              updateExecutionTest(runEvent.leaf_id, {
                status: "running", returnCode: null, durationSeconds: null, error: null,
              });
            }
            break;
          case "execution_output":
            if (runEvent.leaf_id && typeof runEvent.text === "string") {
              appendExecutionOutput(runEvent.leaf_id, runEvent.text);
            }
            break;
          case "execution_finished":
          case "sandbox_result":
            if (runEvent.leaf_id) {
              const status = executionStatus(runEvent.status);
              if (!status) {
                finish(`Unknown execution status: ${JSON.stringify(runEvent)}`);
                break;
              }
              if (runEvent.event === "sandbox_result" && executionStageStarted) {
                updateExecutionTest(runEvent.leaf_id, { status });
              } else {
                updateExecutionTest(runEvent.leaf_id, {
                  status,
                  returnCode: runEvent.returncode ?? null,
                  durationSeconds: runEvent.seconds ?? null,
                  error: runEvent.traceback ?? runEvent.error ?? null,
                });
              }
            }
            break;
          case "repair_started":
            if (runEvent.leaf_id) {
              rawCode.set(runEvent.leaf_id, "");
              updateWriterTest(runEvent.leaf_id, {
                status: "repairing", code: "", error: null,
              });
              updateExecutionTest(runEvent.leaf_id, { status: "repairing" });
            }
            break;
          case "repair":
            if (runEvent.leaf_id) {
              updateWriterTest(runEvent.leaf_id, { status: "written" });
            }
            break;
          case "stage_error":
            finish(runEvent.traceback ?? `${runEvent.stage ?? "service"}: ${runEvent.error ?? "unknown stage error"}`);
            break;
          case "bus_error":
            finish(`Event stream error: ${runEvent.error ?? "unknown bus error"}`);
            break;
          case "run_end":
            if (runEvent.status === "completed") finish();
            else finish(runEvent.traceback ?? runEvent.error ?? "The review run failed");
            break;
          default:
            finish(`Unknown event from Duo service: ${JSON.stringify(runEvent)}`);
        }
      };

      source.onerror = () => {
        finish("Lost the connection to the Duo event stream; the run may still be active on the server");
      };
    } catch (caught) {
      const message = caught instanceof Error ? caught.message : String(caught);
      setRunning(false);
      setCloning(false);
      setWriterActive(false);
      setExecutionActive(false);
      if (executionStageStarted) setExecutionError(message);
      else if (writerStageStarted) setWriterError(message);
      else {
        setDecisionActive(false);
        setError(message);
      }
    }
  }

  return (
    <div className="flex min-h-dvh flex-col divide-y divide-neutral-200 bg-white">
      <Section1
        repositoryUrl={repositoryUrl}
        pullRequest={pullRequest}
        onRepositoryUrlChange={(value) => { setRepositoryUrl(value); if (!running) resetResult(); }}
        onPullRequestChange={(value) => { setPullRequest(value); if (!running) resetResult(); }}
        onSubmit={startReview}
        cloning={cloning}
        running={running}
        progress={progress}
        error={error}
      />
      <Section2
        active={decisionActive}
        running={running}
        complete={!running && !error}
        testTypes={testTypes}
      />
      <Section3
        tests={writerTests}
        active={writerActive}
        error={writerError}
      />
      <Section4
        tests={executionTests}
        currentTestId={currentExecutionId}
        active={executionActive}
        phase={executionPhase}
        error={executionError}
      />
    </div>
  );
}
