export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#4f46e5',
        secondary: '#06b6d4',
      },
      fontFamily: {
        sans: ['system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}