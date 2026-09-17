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
          DEFAULT: "#faf7f2",
          raised: "#fffdf9",
          card: "#ffffff",
          border: "#e7e0d1",
        },
        brand: {
          50: "#eef0fd",
          100: "#dde1fb",
          200: "#b9c0f6",
          300: "#8f96ee",
          400: "#6b6fe3",
          500: "#4f46e5",
          600: "#4338ca",
          700: "#372fa6",
          800: "#2e2887",
          900: "#26226e",
        },
        accent: {
          teal: "#0d9488",
          violet: "#7c3aed",
          amber: "#b45309",
          rose: "#e11d48",
          emerald: "#059669",
        },
      },
      boxShadow: {
        glow: "0 1px 2px rgba(79,70,229,0.06), 0 10px 24px -10px rgba(79,70,229,0.22)",
        card: "0 1px 2px rgba(24,20,14,0.04), 0 8px 20px -10px rgba(24,20,14,0.10)",
      },
      backgroundImage: {
        "grid-fade": "radial-gradient(circle at 20% 0%, rgba(79,70,229,0.05), transparent 40%), radial-gradient(circle at 80% 0%, rgba(13,148,136,0.045), transparent 40%)",
        "brand-gradient": "linear-gradient(135deg, #4f46e5 0%, #7c3aed 50%, #0d9488 100%)",
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
