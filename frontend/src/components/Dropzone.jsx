import { useRef, useState } from "react";

const ACCEPTED_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
];

const ACCEPTED_EXTENSIONS = [".pdf", ".docx"];

function isAcceptedFile(file) {
  if (!file) return false;
  if (ACCEPTED_TYPES.includes(file.type)) {
    return true;
  }
  const lowerName = file.name.toLowerCase();
  return ACCEPTED_EXTENSIONS.some((ext) => lowerName.endsWith(ext));
}

const Dropzone = ({ value, onChange, error }) => {
  const inputRef = useRef(null);
  const [isDragging, setIsDragging] = useState(false);

  const openPicker = () => {
    inputRef.current?.click();
  };

  const handleFiles = (files) => {
    const [file] = files;
    if (!file) return;
    if (!isAcceptedFile(file)) {
      if (onChange) {
        onChange(null);
      }
      return;
    }
    if (onChange) {
      onChange(file);
    }
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setIsDragging(false);
    if (event.dataTransfer?.files) {
      handleFiles(event.dataTransfer.files);
    }
  };

  const handleDragOver = (event) => {
    event.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (event) => {
    event.preventDefault();
    setIsDragging(false);
  };

  const borderTone = error
    ? "border-red-300 bg-red-50/40"
    : isDragging
      ? "border-blue-400 bg-blue-50"
      : "border-slate-300 bg-white";

  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={openPicker}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`w-full h-56 rounded-2xl border-2 border-dashed ${borderTone} bg-white p-8 text-center transition focus:outline-none focus:ring-2 focus:ring-blue-200`}
      >
        <div className="flex h-full w-full flex-col items-center justify-center text-center">
          <svg
            viewBox="0 0 24 24"
            className="h-14 w-14 text-slate-400"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.6"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M12 3v12" />
            <path d="m7 8 5-5 5 5" />
            <path d="M5 21h14" />
          </svg>
          <div className="mt-4 text-sm">
            <span className="font-semibold text-blue-600">Choose a file</span>{" "}
            <span className="text-slate-600">or drag and drop</span>
          </div>
          <p className="mt-1 text-xs text-slate-500">PDF or DOCX up to 25MB</p>
          {value ? (
            <div className="mt-6 inline-flex items-center justify-center gap-3">
              <svg
                viewBox="0 0 24 24"
                className="h-6 w-6 text-emerald-600"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <path d="M14 2H7a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" />
                <path d="M14 2v6h6" />
              </svg>
              <span className="text-xl font-medium text-emerald-600">
                {value.name}
              </span>
            </div>
          ) : null}
        </div>
      </button>

      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        onChange={(event) => handleFiles(event.target.files || [])}
        className="hidden"
      />

      {value ? null : null}
    </div>
  );
};

export default Dropzone;
