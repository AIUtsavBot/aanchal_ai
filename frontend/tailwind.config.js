export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#0d9488',
        secondary: '#06b6d4',
        accent: '#ec4899',
        'glass-bg': 'rgba(255, 255, 255, 0.55)',
        'glass-border': 'rgba(13, 148, 136, 0.15)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}