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
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
}
