/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Geist Sans", "system-ui", "sans-serif"],
        mono: ["Geist Mono", "ui-monospace", "monospace"],
      },
      colors: {
        surface: {
          0: "#09090b",
          1: "#131316",
          2: "#1c1c21",
          3: "#27272a",
        },
        accent: {
          DEFAULT: "#10b981",
          muted: "rgba(16, 185, 129, 0.12)",
        },
        danger: {
          DEFAULT: "#ef4444",
          muted: "rgba(239, 68, 68, 0.12)",
        },
        warn: {
          DEFAULT: "#f59e0b",
          muted: "rgba(245, 158, 11, 0.12)",
        },
        text: {
          primary: "#fafafa",
          secondary: "#a1a1aa",
          muted: "#52525b",
        },
        line: "#27272a",
      },
      borderRadius: {
        "2xl": "1.25rem",
        "3xl": "1.5rem",
        "4xl": "2.5rem",
      },
      keyframes: {
        shimmer: {
          "0%": { backgroundPosition: "-200% 0" },
          "100%": { backgroundPosition: "200% 0" },
        },
      },
      animation: {
        shimmer: "shimmer 1.8s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
