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
    <div className="min-h-screen bg-slate-50 py-10 px-6 text-slate-900">
      <div className="mx-auto w-full max-w-5xl">
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
  )
}

export default App
