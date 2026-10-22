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
        background: "#F9FAFB",
        border: "#E5E7EB",
        "border-light": "#F3F4F6",
        foreground: "#111827",
        "text-secondary": "#6B7280",
        "text-tertiary": "#9CA3AF",
        primary: {
          DEFAULT: "#0D9488",
          hover: "#0F766E",
          light: "#CCFBF1",
          50: "#F0FDFA",
        },
        success: { DEFAULT: "#059669", light: "#D1FAE5" },
        warning: { DEFAULT: "#D97706", light: "#FEF3C7" },
        danger: { DEFAULT: "#DC2626", light: "#FEE2E2" },
        info: { DEFAULT: "#2563EB", light: "#DBEAFE" },
        "sidebar-hover": "#F3F4F6",
        "sidebar-active": "#F0FDFA",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      boxShadow: {
        xs: "0 1px 2px rgba(0,0,0,0.05)",
        card: "0 1px 3px rgba(0,0,0,0.08), 0 1px 2px rgba(0,0,0,0.04)",
        "card-hover":
          "0 4px 12px rgba(0,0,0,0.1), 0 1px 3px rgba(0,0,0,0.06)",
        sidebar: "1px 0 0 0 #E5E7EB",
      },
      keyframes: {
        fadeIn: {
          from: { opacity: "0", transform: "translateY(8px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
        slideUp: {
          from: { opacity: "0", transform: "translateY(16px)" },
          to: { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-in": "fadeIn 0.5s ease both",
        "fade-in-delay-1": "fadeIn 0.5s ease 0.1s both",
        "fade-in-delay-2": "fadeIn 0.5s ease 0.2s both",
        "fade-in-delay-3": "fadeIn 0.5s ease 0.3s both",
        "slide-up": "slideUp 0.6s ease both",
      },
    },
  },
  plugins: [],
};

export default config;
