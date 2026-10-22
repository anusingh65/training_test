import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#0A0F1A",
        secondary: "#111827",
        surface: "#1E293B",
        accent: "#2563EB",
        "accent-light": "#3B82F6",
        muted: "#94A3B8",
        purple: "#7C3AED",
        "purple-light": "#8B5CF6",
      },
    },
  },
  plugins: [],
};
export default config;
