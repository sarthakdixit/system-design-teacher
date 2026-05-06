import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useState } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ErrorBoundary } from "@/shared/components/ErrorBoundary";

function Boom(): JSX.Element {
  throw new Error("Test boom");
}

function FlakyChild({ shouldThrow }: { shouldThrow: boolean }): JSX.Element {
  if (shouldThrow) {
    throw new Error("Flaky failed");
  }
  return <div>Child rendered ok</div>;
}

describe("ErrorBoundary", () => {
  let consoleErrorSpy: ReturnType<typeof vi.spyOn>;

  beforeEach(() => {
    consoleErrorSpy = vi.spyOn(console, "error").mockImplementation(() => {});
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
  });

  it("renders children when no error is thrown", () => {
    render(
      <ErrorBoundary>
        <div>Happy child</div>
      </ErrorBoundary>,
    );

    expect(screen.getByText("Happy child")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("renders the fallback UI when a child throws", () => {
    render(
      <ErrorBoundary>
        <Boom />
      </ErrorBoundary>,
    );

    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(screen.getByText(/something went wrong/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /try again/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /reload page/i })).toBeInTheDocument();
  });

  it("includes the technical details disclosure", () => {
    render(
      <ErrorBoundary>
        <Boom />
      </ErrorBoundary>,
    );

    expect(screen.getByText(/technical details/i)).toBeInTheDocument();
    expect(screen.getByText(/test boom/i)).toBeInTheDocument();
  });

  it("logs the error to console.error", () => {
    render(
      <ErrorBoundary>
        <Boom />
      </ErrorBoundary>,
    );

    expect(consoleErrorSpy).toHaveBeenCalled();
    const calls = consoleErrorSpy.mock.calls;
    const ourCall = calls.find(
      (c) => typeof c[0] === "string" && c[0].includes("ErrorBoundary caught"),
    );
    expect(ourCall).toBeDefined();
  });

  it("recovers when Try again is clicked after the underlying error is fixed", async () => {
    const user = userEvent.setup();

    function Recoverable(): JSX.Element {
      const [shouldThrow, setShouldThrow] = useState(true);
      return (
        <div>
          <button type="button" onClick={() => setShouldThrow(false)}>
            fix the error
          </button>
          <ErrorBoundary>
            <FlakyChild shouldThrow={shouldThrow} />
          </ErrorBoundary>
        </div>
      );
    }

    render(<Recoverable />);

    expect(screen.getByRole("alert")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: /fix the error/i }));
    await user.click(screen.getByRole("button", { name: /try again/i }));

    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.getByText(/child rendered ok/i)).toBeInTheDocument();
  });
});
