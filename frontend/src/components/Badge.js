import './Badge.css';

const VARIANTS = {
  Bajo:      'badge--bajo',
  Medio:     'badge--medio',
  Alto:      'badge--alto',
  Bronce:    'badge--bronce',
  Plata:     'badge--plata',
  Oro:       'badge--oro',
  default:   'badge--default',
};

export default function Badge({ label }) {
  const cls = VARIANTS[label] || VARIANTS.default;
  return <span className={`badge ${cls}`}>{label}</span>;
}
