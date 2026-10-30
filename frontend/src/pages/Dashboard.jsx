import { useAuth } from "../hooks/useAuth";

export function Dashboard() {
  const { user } = useAuth();

  return <section><p className="text-sm font-medium text-leaf">Tổng quan gia đình</p><h1 className="mt-2 text-2xl font-bold text-forest sm:text-3xl">Chào mừng, <span className="capitalize">{user?.fullName}</span></h1><p className="mt-2 text-sm text-stone-500">Không gian chung để kết nối và lưu giữ những điều thân thương.</p><div className="mt-8 rounded-2xl border border-[#e8e8df] bg-white p-6 shadow-sm"><div className="grid h-12 w-12 place-items-center rounded-2xl bg-sage text-2xl text-forest">⌂</div><h2 className="mt-5 text-lg font-semibold text-forest">Không gian gia đình đang được chuẩn bị</h2><p className="mt-2 max-w-xl text-sm leading-6 text-stone-500">Các khu vực cây gia phả, cộng đồng, sự kiện và di sản sẽ xuất hiện tại đây khi được xây dựng ở những bước tiếp theo.</p></div></section>;
}
