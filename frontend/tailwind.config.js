/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        industrial: {
          900: '#0f172a',
          800: '#1e293b',
          700: '#334155',
          600: '#475569',
          500: '#64748b',
          400: '#94a3b8',
          100: '#f1f5f9',
          50: '#f8fafc'
        },
        brand: {
          primary: '#2563eb',
          success: '#16a34a',
          warning: '#d97706',
          danger: '#dc2626',
          cyan: '#06b6d4',
          emerald: '#10b981'
        }
      }
    },
  },
  plugins: [],
}
