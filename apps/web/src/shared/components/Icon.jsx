export function Icon({ name, className = "" }) {
  return <img className={`icon ${className}`} src={`/assets/icons/ui-${name}.svg`} width="20" height="20" alt="" aria-hidden="true" />;
}
