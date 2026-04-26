/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        base: '#FFFFFF',
        text: '#111111',
        soft: '#F5F5F5',
        border: '#EAEAEA',
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', 'sans-serif'],
      },
      borderRadius: {
        xl: '0.9rem',
      },
    },
  },
  plugins: [],
};
