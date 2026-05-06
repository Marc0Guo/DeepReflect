/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['Outfit', 'system-ui', 'sans-serif'],
        body: ['DM Sans', 'system-ui', 'sans-serif'],
      },
      colors: {
        accent: { DEFAULT: 'var(--accent)', secondary: 'var(--accent-secondary)', warm: 'var(--accent-warm)', green: 'var(--accent-green)', pink: 'var(--accent-pink)' },
      },
    },
  },
  plugins: [],
}
