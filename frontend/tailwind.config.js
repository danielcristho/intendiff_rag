/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Token diambil dari .ref/cloudx_ui/src/assets/main.css
        canvas: "#f4f4f6",
        surface: "#ffffff",
        ink: { DEFAULT: "#232430", soft: "#52525f", faint: "#9a9aa8" },
        line: "#232430", // border tegas: tombol, input
        hairline: "#e6e6ea", // pemisah halus
        accent: { DEFAULT: "#4f46e5", hover: "#4338ca", soft: "#eef2ff" },
        ok: { DEFAULT: "#15803d", soft: "#dcfce7" },
        warn: { DEFAULT: "#b45309", soft: "#fef3c7" },
        danger: { DEFAULT: "#b91c1c", soft: "#fee2e2" },
      },
      fontFamily: {
        sans: ["Inter Tight", "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
        mono: ["ui-monospace", "SF Mono", "Menlo", "Consolas", "monospace"],
      },
      boxShadow: {
        card: "0 1px 2px rgb(35 36 48 / 0.06), 0 1px 8px rgb(35 36 48 / 0.04)",
      },
      borderRadius: { DEFAULT: "0.5rem" },
    },
  },
  plugins: [],
};
