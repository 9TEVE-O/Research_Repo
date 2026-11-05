/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        mono: ["'Courier New'", "'Lucida Console'", "ui-monospace", "monospace"],
      },
      colors: {
        term: {
          bg: "#0a0a0f",
          surface: "#0c0c14",
          card: "#0f0f1a",
          border: "#1e1e2e",
          borderHighlight: "#2a2a3a",
          blue: "#4a9eff",
          blueDim: "#1a2a4a",
          text: "#e8e6e1",
          dim: "#888899",
          muted: "#555566",
        }
      }
    },
  },
  plugins: [],
}
