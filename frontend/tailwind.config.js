/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        pink: "#FC2779",
        "pink-hover": "#E01B68",
        peach: "#FFC4A8",
        canvas: "#F7F7F7",
        surface: "#FFFFFF",
        ink: "#001325",
        muted: "#6F6F6F",
        hairline: "#E8E8E8",
        search: "#F3F3F3",
      },
      fontFamily: {
        wordmark: ['"Barlow Condensed"', "sans-serif"],
        ui: ['Outfit', "sans-serif"],
      },
      keyframes: {
        "promo-shift": {
          "0%, 100%": { backgroundPosition: "0% 50%" },
          "50%": { backgroundPosition: "100% 50%" },
        },
        "hero-zoom": {
          "0%": { transform: "scale(1)" },
          "100%": { transform: "scale(1.06)" },
        },
        "rise-in": {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        promo: "promo-shift 12s ease-in-out infinite",
        "hero-zoom": "hero-zoom 28s ease-out forwards",
        rise: "rise-in 0.7s ease-out both",
      },
    },
  },
  plugins: [],
};
