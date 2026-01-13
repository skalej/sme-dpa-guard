import { useState } from "react";

import { submitReview } from "../api.js";
import {
  isAllowedFileSize,
  isAllowedFileType,
  MAX_FILE_SIZE_BYTES,
} from "../utils/helpers.js";
import Dropzone from "./Dropzone.jsx";

const ROLE_OPTIONS = ["controller", "processor"];
const REGION_OPTIONS = ["EU", "UK", "US", "Other"];
const VENDOR_OPTIONS = ["SaaS", "Cloud", "Marketing", "HR", "Payments", "Other"];

const UploadView = ({ onStarted, defaultRole = "", defaultRegion = "", defaultVendorType = "" }) => {
  const [file, setFile] = useState(null);
  const [role, setRole] = useState(defaultRole);
  const [region, setRegion] = useState(defaultRegion);
  const [vendorType, setVendorType] = useState(defaultVendorType);
  const [error, setError] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError("");

    if (!file) {
      setError("Please select a PDF or DOCX file.");
      return;
    }
    if (!isAllowedFileType(file)) {
      setError("Unsupported file type. Please upload PDF or DOCX.");
      return;
    }
    if (!isAllowedFileSize(file)) {
      setError("File is too large. Maximum size is 25MB.");
      return;
    }
    if (!role) {
      setError("Please select your role.");
      return;
    }
    if (!region) {
      setError("Please select the processing region.");
      return;
    }

    setIsSubmitting(true);
    try {
      const contextJson = {
        company_role: role,
        region,
        vendor_type: vendorType || null,
      };
      const response = await submitReview({ file, context: contextJson });
      const reviewId = response.review_id ?? response.reviewId ?? response.id;
      const jobId = response.job_id ?? response.jobId;
      if (onStarted) {
        onStarted({ reviewId, jobId });
      }
    } catch (err) {
      if (err && err.status === 415) {
        setError("Unsupported file type. Please upload PDF or DOCX.");
      } else if (err && err.status === 413) {
        setError("File too large. Max 25MB.");
      } else if (err && err.status === 409) {
        setError(
          `Review is not in a state that allows upload. ${err.message || ""}`.trim()
        );
      } else {
        setError(err?.message || "Something went wrong. Please try again.");
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const maxSizeMb = Math.round(MAX_FILE_SIZE_BYTES / (1024 * 1024));

  return (
    <div className="mx-auto w-full max-w-5xl space-y-6">
      <div className="text-center space-y-2">
        <h1 className="text-4xl font-bold text-slate-900">DPA Guard</h1>
        <p className="text-base text-slate-500">
          Fast, evidence-based DPA review for GDPR compliance
        </p>
      </div>

      <div className="rounded-2xl bg-white p-8 shadow-lg w-full">
        <div className="space-y-2">
          <h2 className="text-2xl font-semibold text-slate-900">
            Upload Data Processing Agreement
          </h2>
          <p className="text-sm text-slate-500">PDF or DOCX up to {maxSizeMb}MB</p>
        </div>

        {error ? (
          <div className="mt-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        ) : null}

        <form onSubmit={handleSubmit} className="mt-6 space-y-6">
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">
              Document Upload
            </label>
            <Dropzone value={file} onChange={setFile} error={error} />
          </div>

          <div className="grid grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="block text-sm font-medium text-slate-700">
                Your Role
              </label>
              <select
                value={role}
                onChange={(event) => setRole(event.target.value)}
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700"
              >
                <option value="">Select role</option>
                {ROLE_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-medium text-slate-700">
                Processing Region
              </label>
              <select
                value={region}
                onChange={(event) => setRegion(event.target.value)}
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700"
              >
                <option value="">Select region</option>
                {REGION_OPTIONS.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-slate-700">
              Vendor Type (optional)
            </label>
            <select
              value={vendorType}
              onChange={(event) => setVendorType(event.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-700"
            >
              <option value="">Select vendor type</option>
              {VENDOR_OPTIONS.map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="w-full rounded-xl bg-blue-600 px-4 py-3.5 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isSubmitting ? "Starting review..." : "Start Review"}
          </button>

          <p className="text-xs text-slate-500">
            This tool provides decision support and is not legal advice.
          </p>
        </form>
      </div>
    </div>
  );
};

export default UploadView;
