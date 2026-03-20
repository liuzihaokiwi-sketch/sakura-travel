/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        sakura: {
          50: "#fef7f7",
          100: "#fce4ec",
          200: "#f8bbd0",
          300: "#f48fb1",
          400: "#ec407a",
          500: "#e91e63",
          600: "#c2185b",
        },
        warm: {
          50: "#fefaf6",
          100: "#fef3e2",
          200: "#fde4b8",
          300: "#f7931e",
          400: "#ff6b35",
          500: "#d35400",
        },
      },
      fontFamily: {
        display: [
          "Playfair Display",
          "Noto Serif SC",
          "serif",
        ],
        sans: [
          "Inter",
          "Noto Sans SC",
          "-apple-system",
          "BlinkMacSystemFont",
          "sans-serif",
        ],
        mono: ["JetBrains Mono", "monospace"],
      },
      animation: {
        "sakura-fall": "sakuraFall 10s linear infinite",
        "pulse-soft": "pulseSoft 2s ease-in-out infinite",
      },
      keyframes: {
        sakuraFall: {
          "0%": { transform: "translateY(-10%) rotate(0deg)", opacity: "1" },
          "100%": { transform: "translateY(110vh) rotate(720deg)", opacity: "0" },
        },
        pulseSoft: {
          "0%, 100%": { opacity: "1", transform: "scale(1)" },
          "50%": { opacity: "0.8", transform: "scale(1.05)" },
        },
      },
    },
  },
  plugins: [],
};