import { useState } from "react";

import ProcessingView from "./components/ProcessingView.jsx";
import ResultsView from "./components/ResultsView.jsx";
import UploadView from "./components/UploadView.jsx";

function App() {
  const [step, setStep] = useState("upload");
  const [reviewId, setReviewId] = useState(null);
  const [jobId, setJobId] = useState(null);

  const handleStarted = ({ reviewId: nextReviewId, jobId: nextJobId }) => {
    setReviewId(nextReviewId);
    setJobId(nextJobId);
    setStep("processing");
  };

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900 flex items-center justify-center p-6">
      <div className="w-full max-w-xl rounded-2xl bg-white shadow-lg border border-slate-200 p-8">
        <div className="text-center space-y-2">
          <h1 className="text-3xl font-semibold tracking-tight">DPA Guard</h1>
          <p className="text-sm text-slate-500">Frontend scaffold</p>
        </div>
        <div className="mt-8">
          {step === "upload" && <UploadView onStarted={handleStarted} />}
          {step === "processing" && (
            <div className="space-y-2">
              <ProcessingView />
              <p className="text-xs text-slate-500">
                Review ID: {reviewId} {jobId ? `• Job ID: ${jobId}` : ""}
              </p>
            </div>
          )}
          {step === "results" && <ResultsView />}
        </div>
      </div>
    </div>
  )
}

export default App
