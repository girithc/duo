type Props = {
  active: boolean;
  running: boolean;
  complete: boolean;
  testTypes: string[];
};

export default function Section2({ active, running, complete, testTypes }: Props) {
  return (
    <section
      aria-label="Tests"
      aria-busy={active && running}
      className={`p-6 transition-colors duration-300 ${active ? "bg-neutral-100" : "bg-white"}`}
    >
      <h2 className="text-base font-medium text-neutral-900">Tests</h2>

      {active && running && testTypes.length === 0 && (
        <p role="status" className="mt-5 text-sm text-neutral-500">
          SubQ is classifying this pull request…
        </p>
      )}

      {testTypes.length > 0 && (
        <ul
          aria-live="polite"
          aria-relevant="additions"
          className="mt-5 grid grid-cols-2 gap-x-6 gap-y-3 text-sm text-neutral-700"
        >
          {testTypes.map((testType) => (
            <li key={testType}>{testType.replaceAll("-", " ")}</li>
          ))}
        </ul>
      )}

      {complete && testTypes.length === 0 && (
        <p role="status" className="mt-5 text-sm text-neutral-500">
          No test types met the decision model&apos;s confidence threshold.
        </p>
      )}
    </section>
  );
}
