/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          50: '#f5f3ff',
          100: '#ede9fe',
          200: '#ddd6fe',
          300: '#c4b5fd',
          400: '#a78bfa',
          500: '#8b5cf6',
          600: '#7c3aed',
          700: '#6d28d9',
          800: '#5b21b6',
          900: '#4c1d95',
        },
        palette: {
          cream: '#FFF4BF',
          pink: '#FFBEFB',
          orchid: '#DC95FF',
          purple: '#8C56D4',
        },
        luxury: {
          bg: '#f8f6fd',
          surface: '#ffffff',
          lavender: '#ede8f9',
          lavenderDark: '#8C56D4',
          gold: '#FFF4BF',
          goldLight: '#FFF4BF',
          goldBorder: '#DC95FF',
          cardBorder: 'rgba(220, 149, 255, 0.3)',
        }
      },
      fontFamily: {
        sans: ['Outfit', 'Prompt', 'sans-serif'],
        mono: ['JetBrains Mono', 'Consolas', 'monospace'],
      },
      boxShadow: {
        'card': '0 10px 30px -5px rgba(124, 58, 237, 0.07), 0 4px 12px -2px rgba(0, 0, 0, 0.03)',
        'btn': '0 8px 20px -4px rgba(124, 58, 237, 0.35)',
        'btn-gold': '0 8px 20px -4px rgba(245, 158, 11, 0.35)',
        'glass': '0 8px 32px 0 rgba(109, 40, 217, 0.06), 0 2px 8px 0 rgba(0, 0, 0, 0.02)',
        'glow-purple': '0 0 24px rgba(139, 92, 246, 0.22)',
      }
    },
  },
  plugins: [],
}
