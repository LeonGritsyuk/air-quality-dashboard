/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#F4F7F6",
        surface: "#FFFFFF",
        ink: {
          DEFAULT: "#16211D",
          muted: "#5B6B64",
          faint: "#8B9891",
        },
        hairline: "#DCE4E1",
        good: {
          DEFAULT: "#2F7A63",
          bg: "#E7F3EE",
        },
        elevated: {
          DEFAULT: "#B4780F",
          bg: "#FBF0DD",
        },
        poor: {
          DEFAULT: "#B0402F",
          bg: "#FBE9E5",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        display: ["\"Space Grotesk\"", "Inter", "system-ui", "sans-serif"],
      },
      borderRadius: {
        DEFAULT: "10px",
        lg: "14px",
        sm: "6px",
      },
      boxShadow: {
        none: "none",
      },
    },
  },
  plugins: [],
};
