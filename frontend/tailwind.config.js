/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        forest: "#244b3e",
        leaf: "#577c5a",
        sage: "#e8efe4",
        earth: "#9a684b",
        sand: "#f7f5ef",
      },
      boxShadow: {
        soft: "0 18px 50px rgba(36, 75, 62, 0.10)",
      },
    },
  },
  plugins: [],
};
