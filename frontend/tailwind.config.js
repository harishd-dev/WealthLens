/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          green: '#10B981',
          cyan:  '#06B6D4',
        },
        surface: {
          900: '#060A12',
          800: '#0D1424',
          700: '#111827',
          600: '#1E2D45',
        },
        text: {
          primary:   '#E8EDF5',
          secondary: '#7B92B2',
          muted:     '#4B5563',
        },
      },
      fontFamily: {
        sans: ["'DM Sans'", 'sans-serif'],
        mono: ["'DM Mono'", 'monospace'],
        display: ["'Syne'", 'sans-serif'],
      },
      borderRadius: { xl: '1rem', '2xl': '1.25rem', '3xl': '1.5rem' },
      backgroundImage: {
        'brand-gradient': 'linear-gradient(135deg, #10B981, #06B6D4)',
      },
      animation: {
        'fade-in':  'fadeIn .35s ease forwards',
        'slide-in': 'slideIn .3s ease forwards',
      },
      keyframes: {
        fadeIn:  { from: { opacity: 0, transform: 'translateY(8px)' }, to: { opacity: 1, transform: 'translateY(0)' } },
        slideIn: { from: { opacity: 0, transform: 'translateX(-12px)' }, to: { opacity: 1, transform: 'translateX(0)' } },
      },
    },
  },
  plugins: [],
}
