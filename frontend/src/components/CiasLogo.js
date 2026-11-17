export default function CiasLogo({ size = 48, className = '' }) {
  return (
    <img
      src="/logo-cias.svg"
      alt="CIAS"
      width={size}
      height={size}
      style={{ display: 'block' }}
      className={className}
    />
  );
}
