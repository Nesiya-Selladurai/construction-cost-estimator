/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        blueprint: {
          ink: "#0B3D91",
          "ink-dark": "#082A66",
          accent: "#2F6FED",
          tint: "#EAF2FF",
          paper: "#FBFCFE",
          graphite: "#16213A",
          line: "#C7D8F5",
        },
        signal: {
          success: "#16A34A",
          error: "#DC2626",
          warning: "#D97706",
        },
      },
      fontFamily: {
        display: ["'Space Grotesk'", "sans-serif"],
        body: ["'Inter'", "sans-serif"],
        mono: ["'IBM Plex Mono'", "monospace"],
      },
      backgroundImage: {
        "blueprint-grid":
          "linear-gradient(rgba(47,111,237,0.08) 1px, transparent 1px), linear-gradient(90deg, rgba(47,111,237,0.08) 1px, transparent 1px)",
      },
      backgroundSize: {
        grid: "24px 24px",
      },
      boxShadow: {
        card: "0 1px 2px rgba(11,61,145,0.06), 0 8px 24px -12px rgba(11,61,145,0.18)",
      },
    },
  },
  plugins: [],
};
