import { type FormEvent } from "react";

type Props = {
  repositoryUrl: string;
  pullRequest: string;
  onRepositoryUrlChange: (value: string) => void;
  onPullRequestChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  cloning: boolean;
  running: boolean;
  progress: number;
  error: string | null;
};

export default function Section1({
  repositoryUrl,
  pullRequest,
  onRepositoryUrlChange,
  onPullRequestChange,
  onSubmit,
  cloning,
  running,
  progress,
  error,
}: Props) {
  return (
    <section aria-label="Repository and pull request" className="bg-white p-6" aria-busy={cloning}>
      <form onSubmit={onSubmit}>
        <h2 className="text-base font-medium text-neutral-900">Pull request</h2>

        <div className="mt-5 grid grid-cols-2 gap-3">
          <label htmlFor="repository-url" className="block text-sm font-medium text-neutral-700">
            Repository URL
            <input
              id="repository-url"
              name="repositoryUrl"
              type="url"
              required
              value={repositoryUrl}
              onChange={(event) => onRepositoryUrlChange(event.target.value)}
              readOnly={running}
              placeholder="https://github.com/owner/repository.git"
              autoComplete="off"
              spellCheck={false}
              className="mt-1.5 h-9 w-full rounded-md bg-neutral-100 px-3 text-sm font-normal text-neutral-900 outline-none placeholder:text-neutral-400 read-only:text-neutral-500 focus:bg-neutral-200"
            />
          </label>

          <label htmlFor="pull-request" className="block text-sm font-medium text-neutral-700">
            PR number / URL
            <input
              id="pull-request"
              name="pullRequest"
              type="text"
              required
              value={pullRequest}
              onChange={(event) => onPullRequestChange(event.target.value)}
              readOnly={running}
              placeholder="PR number or URL"
              autoComplete="off"
              spellCheck={false}
              className="mt-1.5 h-9 w-full rounded-md bg-neutral-100 px-3 text-sm font-normal text-neutral-900 outline-none placeholder:text-neutral-400 read-only:text-neutral-500 focus:bg-neutral-200"
            />
          </label>
        </div>

        <button
          type="submit"
          disabled={running}
          className="relative mt-3 h-9 w-full overflow-hidden rounded-md bg-neutral-900 px-4 text-sm font-medium text-white hover:bg-neutral-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-neutral-900/30 disabled:cursor-wait disabled:hover:bg-neutral-900"
        >
          {cloning && (
            <span
              role="progressbar"
              aria-label="Pull request loading progress"
              aria-valuemin={1}
              aria-valuemax={100}
              aria-valuenow={progress}
              className="absolute inset-y-0 left-0 bg-neutral-600 transition-[width] duration-500 ease-out"
              style={{ width: `${progress}%` }}
            />
          )}
          <span className="relative">
            {cloning ? `${progress}%` : progress === 100 ? "100% — PR loaded" : "Clone & load PR"}
          </span>
        </button>

        {error && (
          <pre
            role="alert"
            data-server-error
            className="mt-3 max-h-64 overflow-auto rounded-md bg-red-50 p-3 text-xs whitespace-pre-wrap break-words text-red-700"
          >
            {error}
          </pre>
        )}
      </form>
    </section>
  );
}
