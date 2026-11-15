import { Link } from "react-router-dom";

export function Brand({ to = "/dashboard" }) {
  return <Link className="brand" to={to} aria-label="FamilyConnect — trang chủ">
    <span className="brand-mark" aria-hidden="true"><svg viewBox="0 0 32 32" fill="none"><path d="M16 25V13m0 8-7-7m7 3 7-7" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" /><path d="M16 14c-5-3-5-8 0-11 5 3 5 8 0 11ZM10 16c-6 1-9-2-8-7 5-1 8 2 8 7Zm12-4c-1-6 2-9 7-8 1 5-2 8-7 8Z" fill="currentColor" /><path d="M10 28h12" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" /></svg></span>
    <span>Family<span className="brand-light">Connect</span></span>
  </Link>;
}
