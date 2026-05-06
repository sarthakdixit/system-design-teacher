import { Component, type ErrorInfo, type ReactNode } from "react";

type Props = {
  children: ReactNode;
};

type State = {
  error: Error | null;
};

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    console.error("ErrorBoundary caught an error", { error, errorInfo });
  }

  private handleReload = (): void => {
    window.location.reload();
  };

  private handleReset = (): void => {
    this.setState({ error: null });
  };

  render(): ReactNode {
    if (this.state.error === null) {
      return this.props.children;
    }

    return (
      <div
        role="alert"
        className="flex min-h-screen items-center justify-center bg-slate-50 px-4"
      >
        <div className="w-full max-w-md rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
          <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-rose-100">
            <svg
              className="h-6 w-6 text-rose-600"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <h1 className="mb-2 text-xl font-semibold text-slate-900">
            Something went wrong
          </h1>
          <p className="mb-6 text-sm text-slate-600">
            The page hit an unexpected error. You can try resetting this view,
            or reload the entire page.
          </p>
          <details className="mb-6 rounded border border-slate-200 bg-slate-50 p-3 text-xs">
            <summary className="cursor-pointer font-medium text-slate-700">
              Technical details
            </summary>
            <pre className="mt-2 overflow-x-auto whitespace-pre-wrap text-slate-600">
              {this.state.error.message}
            </pre>
          </details>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={this.handleReset}
              className="flex-1 rounded-md border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Try again
            </button>
            <button
              type="button"
              onClick={this.handleReload}
              className="flex-1 rounded-md bg-slate-800 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700"
            >
              Reload page
            </button>
          </div>
        </div>
      </div>
    );
  }
}
