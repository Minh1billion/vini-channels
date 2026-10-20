export function BrandMark({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden>
      <rect width="32" height="32" rx="8" fill="#010101" stroke="var(--border)" strokeWidth="1" />
      <g fill="none" strokeWidth="3.2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M8.5 9.5 16 23l7.5-13.5" stroke="#5CD9F0" transform="translate(-1.2 -0.8)" />
        <path d="M8.5 9.5 16 23l7.5-13.5" stroke="#167A8F" transform="translate(1.2 0.8)" />
        <path d="M8.5 9.5 16 23l7.5-13.5" stroke="#FFFFFF" />
      </g>
    </svg>
  );
}
