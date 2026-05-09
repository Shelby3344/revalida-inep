/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['-apple-system', 'BlinkMacSystemFont', '"SF Pro Display"', '"Segoe UI"', 'system-ui', 'sans-serif'],
      },
      colors: {
        area: {
          clinica: '#0071e3',
          cirurgia: '#e8541e',
          go: '#ac3e92',
          pediatria: '#34c759',
          preventiva: '#5856d6',
        },
      },
    },
  },
  plugins: [],
};
