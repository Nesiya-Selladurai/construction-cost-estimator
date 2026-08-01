import { NavLink } from "react-router-dom";

const linkClass = ({ isActive }) =>
  `px-3 py-2 text-sm font-medium rounded-md transition-colors ${
    isActive ? "text-blueprint-ink bg-blueprint-tint" : "text-blueprint-graphite/70 hover:text-blueprint-ink"
  }`;

export default function Navbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-blueprint-line bg-blueprint-paper/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3 sm:px-6">
        <div className="flex items-center gap-2">
          <svg width="28" height="28" viewBox="0 0 28 28" fill="none" aria-hidden="true">
            <rect x="1" y="1" width="26" height="26" rx="4" stroke="#0B3D91" strokeWidth="1.5" />
            <path d="M6 20V8h6a4 4 0 0 1 0 8H6" stroke="#2F6FED" strokeWidth="1.5" strokeLinecap="round" />
            <path d="M17 20v-8" stroke="#2F6FED" strokeWidth="1.5" strokeLinecap="round" />
          </svg>
          <span className="font-display text-lg font-semibold tracking-tight text-blueprint-ink">
            BluePrint<span className="text-blueprint-accent">Cost</span>
          </span>
        </div>
        <nav className="flex items-center gap-1">
          <NavLink to="/" end className={linkClass}>
            Home
          </NavLink>
          <NavLink to="/predict" className={linkClass}>
            Estimate Cost
          </NavLink>
          <NavLink to="/about" className={linkClass}>
            About
          </NavLink>
        </nav>
      </div>
    </header>
  );
}
