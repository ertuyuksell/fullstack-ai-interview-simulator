/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        ink: { 50: '#f8fafc', 100: '#f1f5f9', 800: '#0f172a', 900: '#020617' },
        brand: {
          50: '#eef2ff', 100: '#e0e7ff', 400: '#818cf8',
          500: '#6366f1', 600: '#4f46e5', 700: '#4338ca',
        },
        accent: { 400: '#22d3ee', 500: '#06b6d4' },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system'],
      },
      boxShadow: {
        glow: '0 0 0 1px rgba(99,102,241,.25), 0 8px 30px rgba(99,102,241,.18)',
      },
    },
  },
  plugins: [],
};
