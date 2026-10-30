import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export function Login() {
  const { signIn, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [submitError, setSubmitError] = useState("");
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm({ defaultValues: { email: "demo@familyconnect.vn", password: "Family123!" } });

  if (isAuthenticated) return <Navigate to="/dashboard" replace />;

  const onSubmit = async (values) => {
    setSubmitError("");
    try {
      await signIn(values);
      const destination = location.state?.from?.pathname || "/dashboard";
      navigate(destination, { replace: true });
    } catch {
      setSubmitError("Đăng nhập chưa thành công. Bạn kiểm tra email, mật khẩu rồi thử lại nhé.");
    }
  };

  return (
    <main className="min-h-screen bg-[#f6f5ef] lg:grid lg:grid-cols-[1.03fr_0.97fr]">
      <section className="relative hidden min-h-screen overflow-hidden bg-forest px-12 py-10 text-white lg:flex lg:flex-col lg:justify-between xl:px-20">
        <div className="absolute -right-28 -top-24 h-96 w-96 rounded-full border border-white/10" /><div className="absolute -bottom-40 -left-24 h-[500px] w-[500px] rounded-full border border-white/10" />
        <Link to="/login" className="relative z-10 flex items-center gap-3"><span className="grid h-12 w-12 place-items-center rounded-2xl bg-white/10 text-2xl">⌂</span><span className="text-lg font-bold">FamilyConnect</span></Link>
        <div className="relative z-10 max-w-xl"><span className="mb-6 inline-flex rounded-full border border-white/20 px-4 py-2 text-xs font-medium tracking-wide text-[#d5e2cf]">NỀN TẢNG CỘNG ĐỒNG GIA ĐÌNH SỐ</span><h1 className="text-5xl font-semibold leading-[1.15] tracking-tight xl:text-6xl">Câu chuyện gia đình<br /><span className="font-serif italic text-[#d1dfc8]">được nối dài.</span></h1><p className="mt-6 max-w-md text-base leading-7 text-white/70">Kết nối các thế hệ, gìn giữ ký ức và cùng nhau viết tiếp câu chuyện của gia đình mình.</p><div className="mt-12 flex items-center gap-3"><div className="flex -space-x-2"><span className="grid h-10 w-10 place-items-center rounded-full border-2 border-forest bg-[#dfb89c]">👩🏻</span><span className="grid h-10 w-10 place-items-center rounded-full border-2 border-forest bg-[#d9c187]">👨🏽</span><span className="grid h-10 w-10 place-items-center rounded-full border-2 border-forest bg-[#b9cba9]">👵🏻</span></div><p className="text-xs text-white/60">Một mái nhà, nhiều thế hệ</p></div></div>
        <p className="relative z-10 text-xs text-white/45">© 2026 FamilyConnect · Gắn kết từ cội nguồn</p>
      </section>

      <section className="flex min-h-screen items-center justify-center px-5 py-10 sm:px-10">
        <div className="w-full max-w-[430px]">
          <Link to="/login" className="mb-10 flex items-center gap-3 lg:hidden"><span className="grid h-11 w-11 place-items-center rounded-2xl bg-sage text-2xl text-forest">⌂</span><span className="font-bold text-forest">FamilyConnect</span></Link>
          <div className="mb-8"><p className="text-sm font-semibold text-leaf">Chào mừng trở lại</p><h2 className="mt-2 text-3xl font-bold tracking-tight text-[#26372f]">Đăng nhập</h2><p className="mt-2 text-sm text-stone-500">Đăng nhập để tiếp tục kết nối với gia đình.</p></div>
          <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-5">
            <div><label htmlFor="email" className="mb-2 block text-sm font-semibold text-stone-700">Email</label><input id="email" type="email" autoComplete="email" placeholder="ten@email.com" {...register("email", { required: "Bạn nhập email giúp mình nhé.", pattern: { value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: "Email chưa đúng định dạng." } })} className={`w-full rounded-xl border bg-white px-4 py-3.5 text-sm outline-none transition placeholder:text-stone-300 focus:border-leaf focus:ring-4 focus:ring-sage ${errors.email ? "border-red-300" : "border-stone-200"}`} />{errors.email && <p role="alert" className="mt-1.5 text-xs text-red-600">{errors.email.message}</p>}</div>
          <div><div className="mb-2 flex items-center justify-between"><label htmlFor="password" className="text-sm font-semibold text-stone-700">Mật khẩu</label><span className="text-xs text-stone-400">Quên mật khẩu?</span></div><input id="password" type="password" autoComplete="current-password" placeholder="Nhập mật khẩu" {...register("password", { required: "Bạn nhập mật khẩu giúp mình nhé.", minLength: { value: 6, message: "Mật khẩu cần có ít nhất 6 ký tự." } })} className={`w-full rounded-xl border bg-white px-4 py-3.5 text-sm outline-none transition placeholder:text-stone-300 focus:border-leaf focus:ring-4 focus:ring-sage ${errors.password ? "border-red-300" : "border-stone-200"}`} />{errors.password && <p role="alert" className="mt-1.5 text-xs text-red-600">{errors.password.message}</p>}</div>
            {submitError && <p role="alert" className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{submitError}</p>}
            <button type="submit" disabled={isSubmitting} className="flex w-full items-center justify-center gap-2 rounded-xl bg-forest px-4 py-3.5 text-sm font-semibold text-white shadow-sm transition hover:bg-[#1d4034] disabled:cursor-wait disabled:opacity-70">{isSubmitting ? <><span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />Đang đăng nhập…</> : "Đăng nhập"}</button>
          </form>
          <div className="my-6 flex items-center gap-4"><span className="h-px flex-1 bg-stone-200" /><span className="text-xs text-stone-400">hoặc</span><span className="h-px flex-1 bg-stone-200" /></div>
          <p className="text-center text-sm text-stone-500">Chưa có tài khoản? <Link to="/register" className="font-semibold text-leaf hover:underline">Đăng ký thành viên</Link></p>
          {import.meta.env.VITE_ENABLE_MOCK_AUTH === "true" && <div className="mt-7 rounded-xl border border-[#e4e9df] bg-white/70 p-4 text-xs leading-5 text-stone-500"><span className="font-semibold text-forest">Tài khoản demo</span><br />demo@familyconnect.vn · Family123!<br /><span className="text-stone-400">Phân quyền admin: dùng email bắt đầu bằng admin.</span></div>}
        </div>
      </section>
    </main>
  );
}
