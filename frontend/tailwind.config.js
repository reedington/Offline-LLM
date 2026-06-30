/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        adtc: {
          black: "#070805",
          ink: "#10130d",
          card: "#15170f",
          cardSoft: "#1d2015",
          line: "#37331f",
          cream: "#f5ead2",
          muted: "#cdbf9f",
          gold: "#d6a84f",
          amber: "#f0bd62",
          green: "#4f7d5b",
        },
      },
      boxShadow: {
        premium: "0 24px 80px rgba(0, 0, 0, 0.35)",
        amber: "0 0 40px rgba(214, 168, 79, 0.18)",
      },
      fontFamily: {
        display: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
