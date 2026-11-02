/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "system-ui", "sans-serif"],
      },
      colors: {
        // Official GroceryPi 5-Color Kitchen Palette (from Figma / coolors.co)
        gunmetal: {
          DEFAULT: "#383D3B",
          dark: "#2A2E2C",
          light: "#4E5451",
        },
        parchment: {
          DEFAULT: "#F7F4F2",
          card: "#FFFFFF",
          hover: "#EFECE8",
          border: "#E2DDD8",
        },
        kioskGray: {
          DEFAULT: "#7C7C7C",
          light: "#A0A0A0",
          subtle: "#D6D4D1",
        },
        limeCream: {
          DEFAULT: "#C3E48B",
          dark: "#A8D462",
          light: "#E1F2C2",
        },
        dustyRose: {
          DEFAULT: "#CD7A7A",
          dark: "#B85C5C",
          light: "#F0C8C8",
        },
      },
      minHeight: {
        touch: "48px",
      },
      minWidth: {
        touch: "48px",
      },
    },
  },
  plugins: [],
};
