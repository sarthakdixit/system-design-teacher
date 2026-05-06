import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { EdgeLabelEditor } from "@/features/design-canvas/components/EdgeLabelEditor";

describe("EdgeLabelEditor", () => {
  it("renders with the initial label populated and ready to edit", () => {
    render(
      <EdgeLabelEditor
        edgeId="edge-1"
        initialLabel="redirect path"
        onSave={vi.fn()}
        onCancel={vi.fn()}
      />,
    );

    const input = screen.getByLabelText(/edge label/i) as HTMLInputElement;
    expect(input.value).toBe("redirect path");
  });

  it("calls onSave with trimmed text when Save is clicked", async () => {
    const onSave = vi.fn();
    const user = userEvent.setup();
    render(
      <EdgeLabelEditor
        edgeId="edge-1"
        initialLabel=""
        onSave={onSave}
        onCancel={vi.fn()}
      />,
    );

    const input = screen.getByLabelText(/edge label/i);
    await user.type(input, "  write path  ");
    await user.click(screen.getByRole("button", { name: /save/i }));

    expect(onSave).toHaveBeenCalledTimes(1);
    expect(onSave).toHaveBeenCalledWith("edge-1", "write path");
  });

  it("calls onSave when Enter is pressed", async () => {
    const onSave = vi.fn();
    const user = userEvent.setup();
    render(
      <EdgeLabelEditor
        edgeId="edge-1"
        initialLabel=""
        onSave={onSave}
        onCancel={vi.fn()}
      />,
    );

    const input = screen.getByLabelText(/edge label/i);
    await user.type(input, "async telemetry{Enter}");

    expect(onSave).toHaveBeenCalledTimes(1);
    expect(onSave).toHaveBeenCalledWith("edge-1", "async telemetry");
  });

  it("calls onCancel when Escape is pressed", async () => {
    const onCancel = vi.fn();
    const user = userEvent.setup();
    render(
      <EdgeLabelEditor
        edgeId="edge-1"
        initialLabel="existing"
        onSave={vi.fn()}
        onCancel={onCancel}
      />,
    );

    await user.keyboard("{Escape}");

    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it("calls onCancel when the Cancel button is clicked", async () => {
    const onCancel = vi.fn();
    const user = userEvent.setup();
    render(
      <EdgeLabelEditor
        edgeId="edge-1"
        initialLabel=""
        onSave={vi.fn()}
        onCancel={onCancel}
      />,
    );

    await user.click(screen.getByRole("button", { name: /cancel/i }));

    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it("respects the 80-character limit on input", () => {
    render(
      <EdgeLabelEditor
        edgeId="edge-1"
        initialLabel=""
        onSave={vi.fn()}
        onCancel={vi.fn()}
      />,
    );

    const input = screen.getByLabelText(/edge label/i) as HTMLInputElement;
    expect(input.maxLength).toBe(80);
  });

  it("shows a character counter", () => {
    render(
      <EdgeLabelEditor
        edgeId="edge-1"
        initialLabel="abc"
        onSave={vi.fn()}
        onCancel={vi.fn()}
      />,
    );

    expect(screen.getByText("3/80")).toBeInTheDocument();
  });

  it("updates the character counter as the user types", () => {
    render(
      <EdgeLabelEditor
        edgeId="edge-1"
        initialLabel=""
        onSave={vi.fn()}
        onCancel={vi.fn()}
      />,
    );

    const input = screen.getByLabelText(/edge label/i);
    fireEvent.change(input, { target: { value: "hello" } });
    expect(screen.getByText("5/80")).toBeInTheDocument();
  });
});
