import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

export function Register() {
  const { signUp, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [submitError, setSubmitError] = useState("");
  const { register, handleSubmit, watch, formState: { errors, isSubmitting } } = useForm();

  if (isAuthenticated) return <Navigate to="/dashboard" replace />;

  const onSubmit = async (values) => {
    setSubmitError("");
    try {
      await signUp({ full_name: values.full_name, email: values.email, password: values.password });
      navigate("/dashboard", { replace: true });
    } catch (error) {
      const message = error?.response?.data?.detail;
      setSubmitError(message || "Chưa tạo được tài khoản. Bạn kiểm tra thông tin rồi thử lại nhé.");
    }
  };

  return <main className="flex min-h-screen items-center justify-center bg-[#f6f5ef] px-5 py-10"><section className="w-full max-w-lg rounded-3xl border border-[#e8e8df] bg-white p-6 shadow-soft sm:p-9"><Link to="/login" className="flex items-center gap-3"><span className="grid h-11 w-11 place-items-center rounded-2xl bg-sage text-2xl text-forest">⌂</span><span className="font-bold text-forest">FamilyConnect</span></Link><div className="mt-8"><p className="text-sm font-semibold text-leaf">Chào mừng bạn đến với gia đình</p><h1 className="mt-2 text-2xl font-bold text-forest">Tạo tài khoản thành viên</h1><p className="mt-2 text-sm leading-6 text-stone-500">Thông tin của bạn sẽ được lưu an toàn trong hệ thống gia đình.</p></div><form onSubmit={handleSubmit(onSubmit)} noValidate className="mt-7 space-y-4"><div><label htmlFor="full_name" className="mb-1.5 block text-sm font-semibold text-stone-700">Họ và tên</label><input id="full_name" autoComplete="name" {...register("full_name", { required: "Bạn nhập họ tên nhé.", minLength: { value: 2, message: "Họ tên cần ít nhất 2 ký tự." }, maxLength: { value: 200, message: "Họ tên không quá 200 ký tự." } })} className="w-full rounded-xl border border-stone-200 px-4 py-3 text-sm outline-none focus:border-leaf focus:ring-4 focus:ring-sage" placeholder="Nguyễn Văn An" />{errors.full_name && <p role="alert" className="mt-1 text-xs text-red-600">{errors.full_name.message}</p>}</div><div><label htmlFor="email" className="mb-1.5 block text-sm font-semibold text-stone-700">Email</label><input id="email" type="email" autoComplete="email" {...register("email", { required: "Bạn nhập email nhé.", pattern: { value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: "Email chưa đúng định dạng." } })} className="w-full rounded-xl border border-stone-200 px-4 py-3 text-sm outline-none focus:border-leaf focus:ring-4 focus:ring-sage" placeholder="ten@email.com" />{errors.email && <p role="alert" className="mt-1 text-xs text-red-600">{errors.email.message}</p>}</div><div><label htmlFor="password" className="mb-1.5 block text-sm font-semibold text-stone-700">Mật khẩu</label><input id="password" type="password" autoComplete="new-password" {...register("password", { required: "Bạn tạo mật khẩu nhé.", minLength: { value: 8, message: "Mật khẩu cần ít nhất 8 ký tự." }, maxLength: { value: 128, message: "Mật khẩu không quá 128 ký tự." } })} className="w-full rounded-xl border border-stone-200 px-4 py-3 text-sm outline-none focus:border-leaf focus:ring-4 focus:ring-sage" placeholder="Ít nhất 8 ký tự" />{errors.password && <p role="alert" className="mt-1 text-xs text-red-600">{errors.password.message}</p>}</div><div><label htmlFor="confirmPassword" className="mb-1.5 block text-sm font-semibold text-stone-700">Nhập lại mật khẩu</label><input id="confirmPassword" type="password" autoComplete="new-password" {...register("confirmPassword", { required: "Bạn nhập lại mật khẩu nhé.", validate: (value) => value === watch("password") || "Hai mật khẩu chưa trùng nhau." })} className="w-full rounded-xl border border-stone-200 px-4 py-3 text-sm outline-none focus:border-leaf focus:ring-4 focus:ring-sage" placeholder="Nhập lại mật khẩu" />{errors.confirmPassword && <p role="alert" className="mt-1 text-xs text-red-600">{errors.confirmPassword.message}</p>}</div>{submitError && <p role="alert" className="rounded-xl bg-red-50 px-4 py-3 text-sm text-red-700">{submitError}</p>}<button type="submit" disabled={isSubmitting} className="flex w-full items-center justify-center gap-2 rounded-xl bg-forest px-4 py-3.5 text-sm font-semibold text-white hover:bg-[#1d4034] disabled:opacity-60">{isSubmitting ? "Đang tạo tài khoản…" : "Đăng ký"}</button></form><p className="mt-6 text-center text-sm text-stone-500">Đã có tài khoản? <Link to="/login" className="font-semibold text-leaf hover:underline">Đăng nhập</Link></p></section></main>;
}
