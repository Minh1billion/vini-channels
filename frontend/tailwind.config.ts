import type { Config } from 'tailwindcss';

export default {
  darkMode: ['class'],
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg: 'var(--bg)',
        fg: 'var(--fg)',
        card: 'var(--card)',
        surface: 'var(--surface)',
        border: 'var(--border)',
        muted: 'var(--muted)',
        gray: 'var(--gray)',
        ink: 'var(--ink)',
        paper: 'var(--paper)',
        cyan: 'var(--cyan)',
        red: 'var(--red)',
        'red-text': 'var(--red-text)',
        blue: 'var(--blue)',
        'on-blue': 'var(--on-blue)',
        'blue-soft': 'var(--blue-soft)',
        up: 'var(--up)',
        'up-fill': 'var(--up-fill)',
        down: 'var(--down)',
        'cyan-soft': 'var(--cyan-soft)',
        'red-soft': 'var(--red-soft)',
        'cyan-deep': 'var(--cyan-deep)',
        'red-deep': 'var(--red-deep)',
      },
      fontFamily: {
        sans: ['"Be Vietnam Pro"', 'system-ui', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'monospace'],
      },
      borderRadius: { card: '12px', field: '8px' },
      boxShadow: { pop: '0 12px 40px rgba(1, 1, 1, 0.22)' },
      keyframes: {
        'fade-in': { from: { opacity: '0' }, to: { opacity: '1' } },
        'rise': {
          from: { opacity: '0', transform: 'translateY(6px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'pop-in': {
          from: { opacity: '0', transform: 'translateY(-4px) scale(0.97)' },
          to: { opacity: '1', transform: 'translateY(0) scale(1)' },
        },
        'pop-in-up': {
          from: { opacity: '0', transform: 'translateY(4px) scale(0.97)' },
          to: { opacity: '1', transform: 'translateY(0) scale(1)' },
        },
        'dialog-in': {
          from: { opacity: '0', transform: 'translateY(8px) scale(0.97)' },
          to: { opacity: '1', transform: 'translateY(0) scale(1)' },
        },
      },
      animation: {
        'fade-in': 'fade-in 150ms ease-out',
        'rise': 'rise 260ms cubic-bezier(0.16, 1, 0.3, 1) both',
        'pop-in': 'pop-in 140ms cubic-bezier(0.16, 1, 0.3, 1)',
        'pop-in-up': 'pop-in-up 140ms cubic-bezier(0.16, 1, 0.3, 1)',
        'dialog-in': 'dialog-in 180ms cubic-bezier(0.16, 1, 0.3, 1)',
      },
      fontSize: { kpi: ['40px', { lineHeight: '44px' }], page: ['28px', { lineHeight: '36px' }] },
    },
  },
  plugins: [],
} satisfies Config;
