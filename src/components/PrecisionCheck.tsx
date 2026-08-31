interface Props {
  className?: string;
  size?: number;
}

export default function PrecisionCheck({ className, size = 11 }: Props) {
  return (
    <svg
      aria-hidden="true"
      className={className}
      width={size}
      height={size}
      viewBox="0 0 16 16"
      fill="none"
      shapeRendering="geometricPrecision"
    >
      <path
        d="M3.35 8.15 6.55 11.2 12.75 4.95"
        stroke="currentColor"
        strokeWidth="1.65"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
