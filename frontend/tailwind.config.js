/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./src/**/*.{html,ts}",
  ],
  theme: {
    extend: {
      colors: {
        destinyDark: '#0f172a',
        destinyGold: '#eab308',
        destinyBlue: '#38bdf8',
      }
    },
  },
  plugins: [],
}