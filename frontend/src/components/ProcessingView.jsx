const ProcessingView = () => {
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

      <div className="space-y-3 text-sm">
        <ChecklistItem label="Document uploaded" status="done" />
        <ChecklistItem label="Text extracted" status="done" />
        <ChecklistItem label="Classifying clauses..." status="active" />
        <ChecklistItem label="Evaluating risk" status="pending" />
        <ChecklistItem label="Generating report" status="pending" />
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
