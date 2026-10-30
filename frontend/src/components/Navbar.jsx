import { useAuth } from "../hooks/useAuth";

export function Navbar({ onMenuClick }) {
  const { user, signOut } = useAuth();
  const initials = (user?.fullName || "G").trim().slice(0, 1).toLocaleUpperCase("vi");

  return (
    <header className="sticky top-0 z-20 flex h-[76px] items-center justify-between border-b border-[#e8e8e1] bg-white/95 px-4 backdrop-blur sm:px-7">
      <div className="flex items-center gap-3"><button onClick={onMenuClick} aria-label="Mở menu" className="grid h-10 w-10 place-items-center rounded-xl text-xl text-forest hover:bg-sage lg:hidden">☰</button><div><p className="text-xs text-stone-400">Xin chào,</p><p className="font-semibold capitalize text-forest">{user?.fullName || "thành viên"}</p></div></div>
      <div className="flex items-center gap-2 sm:gap-4"><button aria-label="Thông báo" className="relative grid h-10 w-10 place-items-center rounded-xl text-lg text-stone-500 hover:bg-stone-50">♧<span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-earth" /></button><span className="hidden h-8 w-px bg-stone-200 sm:block" /><div className="flex items-center gap-2"><span className="grid h-9 w-9 place-items-center rounded-full bg-sage font-bold uppercase text-forest">{initials}</span><button onClick={signOut} className="hidden text-sm font-medium text-stone-500 hover:text-earth sm:block">Đăng xuất</button><button onClick={signOut} aria-label="Đăng xuất" className="text-sm text-stone-500 sm:hidden">↪</button></div></div>
    </header>
  );
}
