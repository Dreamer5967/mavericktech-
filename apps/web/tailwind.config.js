/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        industrial: {
          bg: '#FFFFFF',
          subtle: '#F5F5F5',
          border: '#E5E5E5',
          primary: '#171717',
          header: '#262626',
          secondary: '#737373',
          green: '#23865A',
          'green-bg': '#EAF4EE',
          amber: '#B7791F',
          'amber-bg': '#FFFBEB',
          red: '#C0392B',
          'red-bg': '#FDF2F2',
        },
        cinematic: {
          dark: '#080D10',
          darkSecondary: '#111A1D',
          green: '#45C982',
          amber: '#E9A23B',
          editorial: '#F1EFE8',
          darkText: '#151A18',
        },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        display: ['"Space Grotesk"', 'sans-serif'],
        mono: ['"IBM Plex Mono"', '"JetBrains Mono"', 'ui-monospace', 'monospace'],
        data: ['"IBM Plex Mono"', 'ui-monospace', 'monospace'],
      },
    },
  },
  plugins: [],
}
