"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import CodeMirror, { type ReactCodeMirrorRef } from "@uiw/react-codemirror";
import { python } from "@codemirror/lang-python";
import { EditorView } from "@codemirror/view";

export type WriterTest = {
  id: string;
  code: string;
  status: "generating" | "repairing" | "written" | "error";
  error: string | null;
};

type Props = {
  tests: WriterTest[];
  active: boolean;
  error: string | null;
};

function testName(id: string) {
  return id.replaceAll("-", " ");
}

function CodeEditor({ name, code }: { name: string; code: string }) {
  const editorRef = useRef<ReactCodeMirrorRef>(null);
  const extensions = useMemo(
    () => [python(), EditorView.contentAttributes.of({ "aria-label": `${testName(name)} code` })],
    [name],
  );

  useEffect(() => {
    const view = editorRef.current?.view;
    if (view) {
      view.dispatch({ selection: { anchor: view.state.doc.length }, scrollIntoView: true });
    }
  }, [code]);

  return (
    <CodeMirror
      ref={editorRef}
      value={code}
      extensions={extensions}
      readOnly
      editable={false}
      theme="light"
      minHeight="14rem"
      maxHeight="24rem"
      basicSetup={{ lineNumbers: true, foldGutter: true, highlightActiveLine: false }}
      className="mt-2 overflow-hidden rounded-md text-xs [&_.cm-editor]:outline-none [&_.cm-editor.cm-focused]:outline-none"
    />
  );
}

export default function Section3({ tests, active, error }: Props) {
  const [expandedTests, setExpandedTests] = useState<Set<string>>(new Set());
  const openedWithCode = useRef(new Set<string>());

  useEffect(() => {
    // Open only when real text has arrived. Never reopen a panel the user
    // deliberately closed, even if that parallel test keeps streaming.
    const startingToStream = tests.filter(
      (test) => test.code.length > 0 && !openedWithCode.current.has(test.id)
    );
    if (startingToStream.length === 0) return;
    for (const test of startingToStream) openedWithCode.current.add(test.id);
    setExpandedTests((expanded) => {
      const next = new Set(expanded);
      for (const test of startingToStream) next.add(test.id);
      return next;
    });
  }, [tests]);

  function toggleTest(id: string) {
    setExpandedTests((expanded) => {
      const next = new Set(expanded);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  return (
    <section aria-label="Writer" aria-busy={active} className="bg-white p-6">
      <h2 className="text-base font-medium text-neutral-900">Writer</h2>

      {error && (
        <pre
          role="alert"
          aria-label="Writer pipeline error"
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
            const panelId = `writer-editor-${test.id}`;
            return (
              <li key={test.id} data-writer-test={test.id}>
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
                  <span
                    title={test.status === "written" ? "Generated and saved" : undefined}
                    className={`shrink-0 text-xs ${test.status === "error" ? "text-red-600" : "text-neutral-500"}`}
                  >
                    {test.status === "generating" && "Generating"}
                    {test.status === "repairing" && "Repairing"}
                    {test.status === "written" && "Written"}
                    {test.status === "error" && "Failed"}
                  </span>
                </div>

                <div id={panelId} hidden={!expanded}>
                  {test.code.length > 0 && <CodeEditor name={test.id} code={test.code} />}
                </div>
                {test.error && (
                  <pre data-writer-test-error className="mt-2 max-h-56 overflow-auto rounded-md bg-red-50 p-3 text-xs whitespace-pre-wrap break-words text-red-700">
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
