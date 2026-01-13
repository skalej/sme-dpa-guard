import { useEffect, useMemo, useRef, useState } from "react";

import { formatApiError, getJob } from "../api.js";

const ProcessingView = ({
  reviewId,
  jobId,
  onCompleted,
  onBack,
  pollIntervalMs = 1500,
}) => {
  const [jobState, setJobState] = useState("PENDING");
  const [errorMessage, setErrorMessage] = useState("");
  const [failureCount, setFailureCount] = useState(0);
  const failureCountRef = useRef(0);
  const [isPaused, setIsPaused] = useState(false);
  const intervalRef = useRef(null);

  const stopPolling = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  const pollJob = async () => {
    try {
      const response = await getJob(reviewId);
      const nextState = response.state || "PENDING";
      setJobState(nextState);
      failureCountRef.current = 0;
      setFailureCount(0);
      setErrorMessage("");

      if (
        response.ready === true ||
        nextState === "SUCCESS" ||
        nextState === "FAILURE"
      ) {
        stopPolling();
        if (nextState === "SUCCESS") {
          window.setTimeout(() => {
            onCompleted?.({ reviewId });
          }, 400);
        } else if (nextState === "FAILURE") {
          setErrorMessage("Processing failed. Please retry or restart.");
        }
      }
    } catch (err) {
      failureCountRef.current += 1;
      const nextFailures = failureCountRef.current;
      setFailureCount(nextFailures);
      if (nextFailures >= 3) {
        setErrorMessage(formatApiError(err));
        setIsPaused(true);
        stopPolling();
      }
    }
  };

  useEffect(() => {
    if (!reviewId || isPaused) {
      return undefined;
    }
    pollJob();
    intervalRef.current = setInterval(pollJob, pollIntervalMs);
    return () => {
      stopPolling();
    };
  }, [reviewId, isPaused, pollIntervalMs]);

  const handleRetry = () => {
    failureCountRef.current = 0;
    setFailureCount(0);
    setErrorMessage("");
    setIsPaused(false);
    pollJob();
  };

  const stepStatuses = useMemo(() => {
    const done = "done";
    const pending = "pending";
    const active = "active";
    const error = "error";

    if (jobState === "FAILURE") {
      return [done, done, error, pending, pending];
    }
    if (jobState === "SUCCESS") {
      return [done, done, done, done, done];
    }
    return [done, done, active, pending, pending];
  }, [jobState]);

  return (
    <div className="space-y-6 text-slate-900">
      <div className="flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-blue-50 text-blue-600">
          <svg
            className="h-5 w-5 animate-spin"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="12" cy="12" r="10" className="opacity-25" />
            <path d="M22 12a10 10 0 0 1-10 10" className="opacity-75" />
          </svg>
        </div>
        <div>
          <h2 className="text-xl font-semibold">Processing DPA...</h2>
          <p className="text-sm text-slate-500">This usually takes a few moments.</p>
        </div>
      </div>

      {errorMessage ? (
        <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
          {errorMessage}
        </div>
      ) : null}

      <div className="space-y-3 text-sm">
        <ChecklistItem label="Document uploaded" status={stepStatuses[0]} />
        <ChecklistItem label="Text extracted" status={stepStatuses[1]} />
        <ChecklistItem label="Classifying clauses..." status={stepStatuses[2]} />
        <ChecklistItem label="Evaluating risk" status={stepStatuses[3]} />
        <ChecklistItem label="Generating report" status={stepStatuses[4]} />
      </div>

      <div className="space-x-3 text-xs text-slate-500">
        <span>Review ID: {reviewId}</span>
        {jobId ? <span>• Job ID: {jobId}</span> : null}
      </div>

      <div className="flex flex-wrap gap-3">
        {onBack ? (
          <button
            type="button"
            onClick={onBack}
            className="rounded-lg border border-slate-300 px-4 py-2 text-xs font-semibold text-slate-600"
          >
            Back to upload
          </button>
        ) : null}
        {(isPaused || jobState === "FAILURE") && (
          <button
            type="button"
            onClick={handleRetry}
            className="rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white"
          >
            Retry
          </button>
        )}
      </div>
    </div>
  );
};

const ChecklistItem = ({ label, status }) => {
  const styles = {
    done: {
      wrapper: "text-slate-700",
      icon: "bg-green-500 text-white",
      iconSvg: (
        <path d="M5 13l4 4L19 7" />
      ),
    },
    active: {
      wrapper: "text-blue-700",
      icon: "border border-blue-500 text-blue-600",
      iconSvg: (
        <path d="M12 6v6l4 2" />
      ),
    },
    pending: {
      wrapper: "text-slate-400",
      icon: "border border-slate-300 text-slate-300",
      iconSvg: (
        <circle cx="12" cy="12" r="4" />
      ),
    },
    error: {
      wrapper: "text-red-600",
      icon: "bg-red-500 text-white",
      iconSvg: (
        <path d="M18 6 6 18M6 6l12 12" />
      ),
    },
  };

  const style = styles[status] || styles.pending;

  return (
    <div className={`flex items-center gap-3 ${style.wrapper}`}>
      <div
        className={`flex h-7 w-7 items-center justify-center rounded-full ${style.icon}`}
      >
        <svg
          className="h-4 w-4"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          {style.iconSvg}
        </svg>
      </div>
      <span>{label}</span>
    </div>
  );
};

export default ProcessingView;
