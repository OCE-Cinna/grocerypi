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
      fontSize: {
        xs: ["14px", { lineHeight: "20px" }],     // Default 12px -> 14px (+2px)
        sm: ["16px", { lineHeight: "24px" }],     // Default 14px -> 16px (+2px)
        base: ["18px", { lineHeight: "28px" }],   // Default 16px -> 18px (+2px)
        lg: ["20px", { lineHeight: "28px" }],     // Default 18px -> 20px (+2px)
        xl: ["22px", { lineHeight: "30px" }],     // Default 20px -> 22px (+2px)
        "2xl": ["26px", { lineHeight: "34px" }], // Default 24px -> 26px (+2px)
        "3xl": ["32px", { lineHeight: "38px" }], // Default 30px -> 32px (+2px)
        "4xl": ["38px", { lineHeight: "42px" }], // Default 36px -> 38px (+2px)
        "5xl": ["50px", { lineHeight: "1" }],    // Default 48px -> 50px (+2px)
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
        touch: "55px", // +15% from 48px kiosk touch standard
      },
      minWidth: {
        touch: "55px", // +15% from 48px kiosk touch standard
      },
    },
  },
  plugins: [],
};
