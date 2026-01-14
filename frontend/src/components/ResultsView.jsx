import { useEffect, useMemo, useState } from "react";

import { getExplain } from "../api.js";
import ClauseCard from "./ClauseCard.jsx";
import { buildCopyTable, normalizeExplain } from "../utils/formatters.js";

const ResultsView = ({ reviewId, onBack, fileName }) => {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isCopying, setIsCopying] = useState(false);

  const loadExplain = async () => {
    setIsLoading(true);
    setError("");
    try {
      const response = await getExplain(reviewId);
      setData(response);
    } catch (err) {
      setError(err?.message || "Failed to load results.");
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!reviewId) return;
    loadExplain();
  }, [reviewId]);

  const model = useMemo(
    () => (data ? normalizeExplain(data, fileName) : null),
    [data, fileName]
  );

  const handleCopy = async () => {
    setIsCopying(true);
    try {
      const text = buildCopyTable(model.clauses, false);
      await navigator.clipboard.writeText(text);
    } catch (err) {
      setError("Unable to copy table.");
    } finally {
      setIsCopying(false);
    }
  };

  if (isLoading) {
    return (
      <div className="rounded-2xl bg-white p-10 shadow">
        <div className="text-sm text-slate-500">Loading results...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-2xl bg-white p-10 shadow space-y-4">
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
        <button
          type="button"
          onClick={loadExplain}
          className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!model) {
    return null;
  }

  return (
    <div className="mx-auto w-full max-w-5xl space-y-8 px-6 py-8">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold text-slate-900">
            {model.docTitle}
          </h1>
          {model.docFileName ? (
            <p className="mt-1 text-sm text-slate-500">
              {model.docFileName}
            </p>
          ) : null}
        </div>
        {onBack ? (
          <button
            type="button"
            onClick={onBack}
            className="text-sm font-medium text-blue-600 hover:underline"
          >
            Back to Upload
          </button>
        ) : null}
      </div>

      <div className="space-y-8">
        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900 mb-4">
            Executive Summary
          </h2>
          <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
            <div className="text-sm font-medium text-blue-700">
              Recommendation
            </div>
            <div className="text-base font-semibold text-blue-700">
              {model.recommendationText}
            </div>
          </div>

          <div className="mt-6">
            <h3 className="mb-3 text-sm font-semibold text-slate-900">
              Top Risks
            </h3>
            {model.topRisks.length === 0 ? (
              <p className="text-sm text-slate-500">
                No high-risk clauses detected.
              </p>
            ) : (
              <ul className="space-y-3 text-base text-slate-700">
                {model.topRisks.map((risk, index) => (
                  <li key={`risk-${index}`} className="flex items-start gap-2">
                    <svg
                      className="w-5 h-5 mt-0.5 text-amber-500"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    >
                      <path d="m12 9 0 4" />
                      <path d="M12 17h.01" />
                      <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z" />
                    </svg>
                    <span>{risk.text}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-slate-900">
            Clause Analysis
          </h2>
          <button
            type="button"
            onClick={handleCopy}
            disabled={isCopying}
            className="inline-flex items-center gap-2 text-sm font-medium text-blue-600 hover:underline disabled:cursor-not-allowed disabled:opacity-50"
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
              <rect x="9" y="9" width="13" height="13" rx="2" ry="2" />
              <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1" />
            </svg>
            {isCopying ? "Copying..." : "Copy Table"}
          </button>
        </div>

        <div className="space-y-4">
          {model.clauses.map((item) => (
            <ClauseCard key={item.id} item={item} />
          ))}
        </div>
      </div>
    </div>
  );
};

export default ResultsView;
