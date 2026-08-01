import { useCallback, useRef, useState } from "react";

const ACCEPTED_EXTENSIONS = ["svg", "png", "jpg", "jpeg", "pdf"];
const ACCEPTED_MIME_TYPES = [
  "image/svg+xml",
  "image/png",
  "image/jpeg",
  "application/pdf",
];

/**
 * props:
 *  - onFileReady: (file) => void   called once a valid blueprint file is chosen/dropped
 *  - uploadProgress: number | null  0-100 while a request is in flight
 *  - fileName: string | null        currently selected/uploaded filename
 *  - disabled: boolean
 */
export default function UploadCard({ onFileReady, uploadProgress, fileName, disabled }) {
  const [isDragging, setIsDragging] = useState(false);
  const [localError, setLocalError] = useState(null);
  const inputRef = useRef(null);

  const validateAndEmit = useCallback(
    (file) => {
      setLocalError(null);
      if (!file) return;

      const ext = file.name.split(".").pop()?.toLowerCase();
      const isAccepted = ACCEPTED_MIME_TYPES.includes(file.type) || ACCEPTED_EXTENSIONS.includes(ext);
      if (!isAccepted) {
        setLocalError("Only SVG, PNG, JPG/JPEG, or PDF blueprint files are supported.");
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        setLocalError("File is larger than the 10 MB limit.");
        return;
      }
      onFileReady(file);
    },
    [onFileReady]
  );

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    if (disabled) return;
    validateAndEmit(e.dataTransfer.files?.[0]);
  };

  return (
    <div>
      <label
        htmlFor="blueprint-upload"
        onDragOver={(e) => {
          e.preventDefault();
          if (!disabled) setIsDragging(true);
        }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        className={`group relative flex min-h-[220px] cursor-pointer flex-col items-center justify-center gap-3 rounded-xl border-2 border-dashed bg-blueprint-tint/40 px-6 py-10 text-center transition-colors ${
          isDragging ? "border-blueprint-accent bg-blueprint-tint" : "border-blueprint-line"
        } ${disabled ? "cursor-not-allowed opacity-60" : "hover:border-blueprint-accent"}`}
      >
        <input
          id="blueprint-upload"
          ref={inputRef}
          type="file"
          accept=".svg,.png,.jpg,.jpeg,.pdf,image/svg+xml,image/png,image/jpeg,application/pdf"
          className="sr-only"
          disabled={disabled}
          onChange={(e) => validateAndEmit(e.target.files?.[0])}
        />

        <svg width="40" height="40" viewBox="0 0 40 40" fill="none" aria-hidden="true">
          <rect x="4" y="4" width="32" height="32" rx="3" stroke="#0B3D91" strokeWidth="1.5" strokeDasharray="3 3" />
          <path d="M20 26V14M20 14l-5 5M20 14l5 5" stroke="#2F6FED" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" />
        </svg>

        <div>
          <p className="font-medium text-blueprint-ink">
            {fileName ? "Replace blueprint" : "Drop your blueprint here"}
          </p>
          <p className="mt-1 text-sm text-blueprint-graphite/60">
            or click to browse &middot; SVG, PNG, JPG/JPEG, or PDF &middot; up to 10 MB
          </p>
        </div>

        {fileName && (
          <div className="mt-1 flex items-center gap-2 rounded-md bg-white px-3 py-1.5 font-mono text-xs text-blueprint-ink shadow-sm">
            <svg width="14" height="14" viewBox="0 0 20 20" fill="currentColor" aria-hidden="true">
              <path d="M4 2a2 2 0 00-2 2v12a2 2 0 002 2h12a2 2 0 002-2V8l-6-6H4z" opacity="0.15" />
              <path d="M11 2v5a1 1 0 001 1h5" />
            </svg>
            {fileName}
          </div>
        )}
      </label>

      {uploadProgress !== null && uploadProgress < 100 && (
        <div className="mt-3">
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-blueprint-line">
            <div
              className="h-full rounded-full bg-blueprint-accent transition-all duration-200"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
          <p className="mt-1 text-xs text-blueprint-graphite/60">Uploading &middot; {uploadProgress}%</p>
        </div>
      )}

      {localError && <p className="mt-2 text-sm font-medium text-signal-error">{localError}</p>}
    </div>
  );
}
