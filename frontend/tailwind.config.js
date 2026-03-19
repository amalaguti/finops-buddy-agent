/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        'finops-bg-page': 'var(--finops-bg-page)',
        'finops-bg-surface': 'var(--finops-bg-surface)',
        'finops-bg-header': 'var(--finops-bg-header)',
        'finops-text-primary': 'var(--finops-text-primary)',
        'finops-text-secondary': 'var(--finops-text-secondary)',
        'finops-border': 'var(--finops-border)',
        'finops-accent': 'var(--finops-accent)',
        'finops-btn-primary': 'var(--finops-btn-primary)',
        'finops-btn-secondary': 'var(--finops-btn-secondary)',
        'finops-badge': 'var(--finops-badge)',
        'finops-badge-text': 'var(--finops-badge-text)',
        'finops-resize-handle': 'var(--finops-resize-handle)',
        'finops-resize-handle-hover': 'var(--finops-resize-handle-hover)',
        'finops-text-header': 'var(--finops-text-header)',
      },
    },
  },
  plugins: [],
};
