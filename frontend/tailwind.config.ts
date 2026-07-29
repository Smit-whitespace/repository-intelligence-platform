import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        surface: "hsl(var(--surface))",
        "surface-secondary": "hsl(var(--surface-secondary))",
        muted: "hsl(var(--muted))",
        "muted-foreground": "hsl(var(--muted-foreground))",
        border: "var(--border)",
        divider: "var(--divider)",
        primary: "hsl(var(--primary))",
        "primary-foreground": "hsl(var(--primary-foreground))",
        "accent-blue": "hsl(var(--accent-blue))",
        "accent-purple": "hsl(var(--accent-purple))",
        "accent-cyan": "hsl(var(--accent-cyan))",
        success: "hsl(var(--success))",
        warning: "hsl(var(--warning))",
        danger: "hsl(var(--danger))",
      },
      borderRadius: {
        DEFAULT: "var(--radius)",
        sm: "var(--radius-sm)",
      },
      fontFamily: {
        sans: ["Geist", "Inter", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["Geist Mono", "Fira Code", "JetBrains Mono", "monospace"],
      },
      animation: {
        "pulse-blue": "pulse-blue 2s ease-in-out infinite",
        "slide-in": "slide-in 0.2s ease-out",
        "fade-in": "fade-in 0.15s ease-out",
        "scale-in": "scale-in 0.15s ease-out",
      },
    },
  },
  plugins: [],
} satisfies Config;
