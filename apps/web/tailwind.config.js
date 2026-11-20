/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        forest: "rgb(var(--forest-rgb) / <alpha-value>)",
        leaf: "rgb(var(--leaf-rgb) / <alpha-value>)",
        sage: "rgb(var(--sage-rgb) / <alpha-value>)",
        earth: "#9a684b",
        sand: "rgb(var(--sand-rgb) / <alpha-value>)",
      },
      boxShadow: {
        soft: "0 18px 50px rgba(36, 75, 62, 0.10)",
      },
    },
  },
  plugins: [],
};
