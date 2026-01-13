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
      ? "border-blue-300 bg-blue-50/60"
      : "border-slate-300 bg-white";

  return (
    <div className="space-y-2">
      <button
        type="button"
        onClick={openPicker}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={`w-full rounded-2xl border-2 border-dashed ${borderTone} px-6 py-10 text-center transition focus:outline-none focus:ring-2 focus:ring-blue-200`}
      >
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-slate-100 text-slate-500">
          <svg
            viewBox="0 0 24 24"
            className="h-6 w-6"
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
        </div>
        <div className="mt-4 text-sm text-slate-600">
          <span className="font-semibold text-blue-600">Choose a file</span>{" "}
          or drag and drop
        </div>
        <p className="mt-1 text-xs text-slate-500">PDF or DOCX up to 25MB</p>
      </button>

      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        onChange={(event) => handleFiles(event.target.files || [])}
        className="hidden"
      />

      {value ? (
        <p className="text-xs text-slate-600">{value.name}</p>
      ) : null}
    </div>
  );
};

export default Dropzone;
