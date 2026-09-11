/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: ['./src/**/*.{html,ts}'],
  theme: {
    extend: {
      colors: {
        paper: {
          50: '#FAFAF7',
          100: '#F3F1EA',
          200: '#E6E2D8',
        },
        ink: {
          50: '#F7F5F1',
          100: '#EBE7E0',
          200: '#D4CFC6',
          300: '#B5AFA4',
          400: '#8A847A',
          600: '#5C574F',
          700: '#3F3B35',
          800: '#2E2B26',
          900: '#22201C',
          950: '#1A1816',
        },
        brass: {
          400: '#C4A574',
          500: '#B08A52',
        },
        accent: {
          50: '#F3F1F8',
          100: '#E4DFF0',
          200: '#C9C0E0',
          400: '#8B7BB8',
          500: '#6B5B95',
          600: '#5B4B8A',
          700: '#4A3C72',
        },
      },
      fontFamily: {
        sans: ['Figtree', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        display: ['Newsreader', 'ui-serif', 'Georgia', 'serif'],
      },
      boxShadow: {
        card: '0 1px 0 rgba(26, 24, 22, 0.04), 0 12px 32px rgba(26, 24, 22, 0.05)',
        lift: '0 16px 40px rgba(26, 24, 22, 0.1)',
      },
      transitionTimingFunction: {
        smooth: 'cubic-bezier(0.22, 1, 0.36, 1)',
      },
    },
  },
  plugins: [],
};
