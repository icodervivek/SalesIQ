/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: "class",
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-inter)", "system-ui", "sans-serif"],
      },
      colors: {
        surface: {
          DEFAULT: "#0b0e17",
          raised: "#11162318",
          card: "#141a29",
          border: "#232a3d",
        },
        brand: {
          50: "#eef2ff",
          100: "#e0e7ff",
          200: "#c7d2fe",
          300: "#a5b4fc",
          400: "#818cf8",
          500: "#6366f1",
          600: "#4f46e5",
          700: "#4338ca",
          800: "#3730a3",
          900: "#312e81",
        },
        accent: {
          teal: "#2dd4bf",
          violet: "#a78bfa",
          amber: "#fbbf24",
          rose: "#fb7185",
          emerald: "#34d399",
        },
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(99,102,241,0.15), 0 8px 24px -8px rgba(99,102,241,0.35)",
        card: "0 1px 2px rgba(0,0,0,0.24), 0 8px 24px -12px rgba(0,0,0,0.5)",
      },
      backgroundImage: {
        "grid-fade": "radial-gradient(circle at 20% 0%, rgba(99,102,241,0.15), transparent 40%), radial-gradient(circle at 80% 0%, rgba(45,212,191,0.12), transparent 40%)",
        "brand-gradient": "linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #2dd4bf 100%)",
      },
      keyframes: {
        "fade-in": { "0%": { opacity: 0, transform: "translateY(4px)" }, "100%": { opacity: 1, transform: "translateY(0)" } },
        shimmer: { "0%": { backgroundPosition: "-500px 0" }, "100%": { backgroundPosition: "500px 0" } },
      },
      animation: {
        "fade-in": "fade-in 0.35s ease-out",
        shimmer: "shimmer 1.6s infinite linear",
      },
    },
  },
  plugins: [],
};
