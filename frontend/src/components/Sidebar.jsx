import { NavLink } from "react-router-dom";

const primaryLinks = [{ label: "Tổng quan", icon: "⌂", to: "/dashboard" }];
const upcomingLinks = [
  { label: "Cây gia phả", icon: "⌘" },
  { label: "Cộng đồng", icon: "♡" },
  { label: "Di sản", icon: "▤" },
  { label: "Danh bạ", icon: "♧" },
  { label: "Trợ lý AI", icon: "✳" },
];

export function Sidebar({ role, open, onClose }) {
  const canManage = role === "admin" || role === "family_head";

  return (
    <>
      {open && <button aria-label="Đóng menu" className="fixed inset-0 z-30 bg-forest/30 lg:hidden" onClick={onClose} />}
      <aside className={`fixed inset-y-0 left-0 z-40 flex w-72 flex-col border-r border-[#e6e8df] bg-white px-5 py-6 transition-transform lg:static lg:z-auto lg:translate-x-0 ${open ? "translate-x-0" : "-translate-x-full"}`}>
        <div className="mb-9 flex items-center gap-3 px-2">
          <span className="grid h-11 w-11 place-items-center rounded-2xl bg-sage text-2xl text-forest">⌂</span>
          <div><p className="font-bold tracking-tight text-forest">FamilyConnect</p><p className="text-xs text-stone-500">Gắn kết qua nhiều thế hệ</p></div>
        </div>
        <p className="mb-3 px-3 text-[11px] font-bold uppercase tracking-[0.16em] text-stone-400">Không gian gia đình</p>
        <nav className="space-y-1">
          {primaryLinks.map((item) => <NavLink key={item.to} to={item.to} onClick={onClose} className={({ isActive }) => `flex items-center gap-3 rounded-xl px-3 py-3 text-sm font-semibold transition ${isActive ? "bg-sage text-forest" : "text-stone-600 hover:bg-stone-50"}`}><span className="w-5 text-center text-lg">{item.icon}</span>{item.label}</NavLink>)}
          {upcomingLinks.map((item) => <div key={item.label} title="Tính năng đang được xây dựng" className="flex cursor-not-allowed items-center gap-3 rounded-xl px-3 py-3 text-sm text-stone-400"><span className="w-5 text-center text-lg">{item.icon}</span>{item.label}<span className="ml-auto text-[10px]">Sắp có</span></div>)}
        </nav>
        {canManage && <div className="mt-7 border-t border-stone-100 pt-5"><p className="mb-3 px-3 text-[11px] font-bold uppercase tracking-[0.16em] text-stone-400">Quản lý</p><div className="flex items-center gap-3 rounded-xl px-3 py-3 text-sm text-stone-500"><span className="w-5 text-center">⚙</span>Quản trị <span className="ml-auto text-[10px]">Sắp có</span></div></div>}
        <div className="mt-auto rounded-2xl bg-[#f6f5ef] p-4"><p className="text-sm font-semibold text-forest">Lưu giữ chuyện nhà</p><p className="mt-1 text-xs leading-5 text-stone-500">Kết nối thành viên, gìn giữ ký ức gia đình.</p></div>
      </aside>
    </>
  );
}
