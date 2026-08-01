import { useEffect } from "react";

/**
 * props:
 *  - notification: { type: 'success' | 'error', message: string } | null
 *  - onDismiss: () => void
 */
export default function Notification({ notification, onDismiss }) {
  useEffect(() => {
    if (!notification) return;
    const t = setTimeout(onDismiss, 5000);
    return () => clearTimeout(t);
  }, [notification, onDismiss]);

  if (!notification) return null;

  const isError = notification.type === "error";

  return (
    <div
      role="status"
      className={`fixed bottom-6 right-6 z-50 flex max-w-sm items-start gap-3 rounded-lg border px-4 py-3 shadow-card animate-[fadeIn_0.2s_ease-out] ${
        isError ? "border-signal-error/30 bg-red-50 text-signal-error" : "border-signal-success/30 bg-green-50 text-signal-success"
      }`}
    >
      <span className="mt-0.5">
        {isError ? (
          <svg width="18" height="18" viewBox="0 0 20 20" fill="currentColor">
            <path
              fillRule="evenodd"
              d="M18 10A8 8 0 11 2 10a8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
              clipRule="evenodd"
            />
          </svg>
        ) : (
          <svg width="18" height="18" viewBox="0 0 20 20" fill="currentColor">
            <path
              fillRule="evenodd"
              d="M16.7 5.3a1 1 0 010 1.4l-7.4 7.4a1 1 0 01-1.4 0L3.3 9.5a1 1 0 111.4-1.4l3.6 3.6 6.7-6.7a1 1 0 011.4 0z"
              clipRule="evenodd"
            />
          </svg>
        )}
      </span>
      <p className="text-sm font-medium leading-snug">{notification.message}</p>
      <button
        onClick={onDismiss}
        aria-label="Dismiss notification"
        className="ml-auto text-current/60 hover:text-current"
      >
        &times;
      </button>
    </div>
  );
}
