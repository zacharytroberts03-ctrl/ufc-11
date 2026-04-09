import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        ufc: {
          red: "#dc0000",
          "red-dark": "#a80000",
          "red-glow": "rgba(220,0,0,0.15)",
          gold: "#d4af37",
          "gold-dim": "#9a7d24",
          green: "#00d68f",
          bg: "#111111",
          surface: "#ffffff",
          elevated: "#f0ebe1",
          border: "#e0d8cc",
          "border-bright": "#d20a0a",
          text: "#f0f0f0",
          muted: "#999999",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      backgroundImage: {
        "hero-gradient":
          "linear-gradient(135deg, #fff0f0 0%, #f7f3ec 50%, #fff8ec 100%)",
        "card-gradient":
          "linear-gradient(180deg, #f0ebe1 0%, #ffffff 100%)",
        "red-gradient":
          "linear-gradient(135deg, #dc0000 0%, #8a0000 100%)",
      },
      animation: {
        "pulse-red": "pulse-red 2s ease-in-out infinite",
        "fade-in": "fade-in 0.3s ease-out",
        "slide-up": "slide-up 0.4s ease-out",
      },
      keyframes: {
        "pulse-red": {
          "0%, 100%": { boxShadow: "0 0 0 0 rgba(220,0,0,0)" },
          "50%": { boxShadow: "0 0 20px 4px rgba(220,0,0,0.3)" },
        },
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "slide-up": {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
