export default function Loader({ label = "Analyzing blueprint..." }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-10 text-blueprint-ink">
      <svg className="h-8 w-8 animate-spin text-blueprint-accent" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" opacity="0.2" />
        <path d="M22 12a10 10 0 00-10-10" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
      </svg>
      <p className="text-sm font-medium">{label}</p>
    </div>
  );
}
