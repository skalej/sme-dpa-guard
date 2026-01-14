import { useState } from "react";

import { statusLabel, statusPillClasses } from "../utils/formatters.js";

const ClauseCard = ({ item }) => {
  const [open, setOpen] = useState(false);
  const hasEvidence = item.evidence && item.evidence.length > 0;

  return (
    <div className="rounded-2xl border border-slate-200 bg-white">
      <button
        type="button"
        onClick={() => setOpen((prev) => !prev)}
        className="flex w-full items-center justify-between gap-4 px-6 py-4 text-left"
      >
        <div className="flex items-center gap-4">
          <span
            className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-semibold ${statusPillClasses(
              item.status
            )}`}
          >
            <span className="h-2.5 w-2.5 rounded-full bg-current opacity-70" />
            {statusLabel(item.status)}
          </span>
          <div>
            <div className="text-sm font-semibold text-slate-900">
              {item.title}
            </div>
            {item.position ? (
              <div className="text-xs text-slate-500">{item.position}</div>
            ) : null}
          </div>
        </div>
        <svg
          className={`h-5 w-5 text-slate-400 transition ${
            open ? "rotate-180" : ""
          }`}
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="m6 9 6 6 6-6" />
        </svg>
      </button>

      {open ? (
        <div className="border-t border-slate-100 px-6 py-5 text-sm text-slate-700 space-y-4">
          <div>
            <div className="text-xs font-semibold uppercase text-slate-400">
              Analysis
            </div>
            <p className="mt-2 text-sm text-slate-700">
              {item.analysis || "No analysis provided."}
            </p>
          </div>

          {item.suggestedChange ? (
            <div className="rounded-xl border border-amber-100 bg-amber-50 px-4 py-3">
              <div className="text-xs font-semibold uppercase text-amber-600">
                Suggested Change
              </div>
              <p className="mt-2 text-sm text-amber-800">
                {item.suggestedChange}
              </p>
            </div>
          ) : null}

          {hasEvidence ? (
            <div>
              <div className="text-xs font-semibold uppercase text-slate-400">
                Evidence
              </div>
              <div className="mt-2 space-y-3">
                {item.evidence.map((snippet, index) => (
                  <div
                    key={`${item.id}-evidence-${index}`}
                    className="rounded-lg border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700 space-y-2"
                  >
                    {snippet.label ? (
                      <div className="text-xs font-semibold text-slate-500">
                        {snippet.label}
                      </div>
                    ) : null}
                    <div className="text-sm text-slate-700">
                      {snippet.quote || snippet}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : null}
        </div>
      ) : null}
    </div>
  );
};

export default ClauseCard;
