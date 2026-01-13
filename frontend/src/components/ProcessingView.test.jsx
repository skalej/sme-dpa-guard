import { act, render, screen } from "@testing-library/react";
import { vi } from "vitest";

import ProcessingView from "./ProcessingView.jsx";
import * as api from "../api.js";

vi.mock("../api.js", () => ({
  getJob: vi.fn(),
  formatApiError: vi.fn(() => "Network error"),
}));

describe("ProcessingView", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    api.getJob.mockReset();
  });

  afterEach(() => {
    vi.clearAllTimers();
    vi.useRealTimers();
  });

  it("renders initial step statuses", () => {
    api.getJob.mockResolvedValue({ state: "PENDING" });

    render(<ProcessingView reviewId="review-1" />);

    expect(screen.getByText("Document uploaded")).toBeInTheDocument();
    expect(screen.getByText("Text extracted")).toBeInTheDocument();
    expect(screen.getByText("Classifying clauses...")).toBeInTheDocument();
  });

  it("calls onCompleted when job succeeds", async () => {
    const onCompleted = vi.fn();
    api.getJob
      .mockResolvedValueOnce({ state: "STARTED" })
      .mockResolvedValueOnce({ state: "SUCCESS" });

    render(<ProcessingView reviewId="review-1" onCompleted={onCompleted} />);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1500);
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1500);
    });

    await act(async () => {
      await vi.advanceTimersByTimeAsync(500);
    });

    expect(onCompleted).toHaveBeenCalledWith({ reviewId: "review-1" });
  });

  it("shows error state on failure", async () => {
    api.getJob.mockResolvedValue({ state: "FAILURE" });

    render(<ProcessingView reviewId="review-1" />);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1500);
    });

    expect(
      screen.getByText("Processing failed. Please retry or restart.")
    ).toBeInTheDocument();
  });

  it("pauses after three consecutive errors", async () => {
    api.getJob.mockRejectedValue(new Error("boom"));

    render(<ProcessingView reviewId="review-1" />);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(1500);
    });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1500);
    });
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1500);
    });

    expect(screen.getByText("Network error")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
  });
});
