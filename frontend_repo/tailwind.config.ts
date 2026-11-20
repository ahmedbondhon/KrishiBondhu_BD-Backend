import type { Config } from "tailwindcss";

/**
 * Design tokens — "Canopy" system.
 * brand = leaf greens (actions, selection), canopy = deep forest (sidebar, hero),
 * lime = highlight used only on dark surfaces, sun/clay/sky = status only.
 * series = validated categorical slots for crop identity in charts.
 */
const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        canvas: "#F4F7F3",
        ink: { DEFAULT: "#0E1F18", soft: "#3E5047", mute: "#66776E" },
        line: { DEFAULT: "#E1E8E3", strong: "#CBD6CE" },
        brand: { 50: "#EDF8F1", 100: "#D6F0E0", 200: "#ADE1C2", 300: "#78CC99", 400: "#40B476", 500: "#1F9D5C", 600: "#178049", 700: "#136540", 800: "#124F34", 900: "#0C3324", 950: "#072219" },
        canopy: { DEFAULT: "#0C3324", 2: "#124F34", 3: "#1A6144" },
        lime: { 300: "#D8F36E", 400: "#C4E94B", 500: "#A9D12E" },
        sun: { 50: "#FFF6DF", 100: "#FFEBB8", 500: "#D99A00", 600: "#A87500", 700: "#7F5800" },
        clay: { 50: "#FDEEEA", 100: "#FADAD3", 500: "#D9472F", 600: "#B3361F", 700: "#8C2815" },
        sky: { 50: "#EBF3FD", 100: "#D3E5FA", 500: "#2F74C8", 600: "#245DA3", 700: "#1B4780" },
        series: { 1: "#2a78d6", 2: "#eb6834", 3: "#1baf7a" },
      },
      fontFamily: {
        sans: ['"Hind Siliguri"', "system-ui", "sans-serif"],
        display: ['"Anek Bangla Variable"', '"Hind Siliguri"', "system-ui", "sans-serif"],
      },
      borderRadius: { ctl: "10px", card: "16px", sheet: "24px" },
      boxShadow: {
        card: "0 1px 2px rgba(14,31,24,.05), 0 0 0 1px rgba(14,31,24,.04)",
        pop: "0 16px 40px -12px rgba(14,31,24,.28), 0 0 0 1px rgba(14,31,24,.06)",
        cta: "0 1px 0 rgba(255,255,255,.2) inset, 0 6px 16px -6px rgba(23,128,73,.55)",
      },
      keyframes: {
        scan: { "0%,100%": { top: "8%" }, "50%": { top: "86%" } },
        ring: { "0%": { transform: "scale(1)", opacity: ".5" }, "100%": { transform: "scale(1.45)", opacity: "0" } },
        rise: { from: { opacity: "0", transform: "translateY(8px)" }, to: { opacity: "1", transform: "none" } },
        shimmer: { from: { backgroundPosition: "200% 0" }, to: { backgroundPosition: "-200% 0" } },
      },
      animation: {
        scan: "scan 3.4s ease-in-out infinite",
        ring: "ring 2.6s ease-out infinite",
        rise: "rise .35s ease-out both",
        shimmer: "shimmer 1.6s linear infinite",
      },
    },
  },
  plugins: [],
};
export default config;
