import { useState } from "react";
import { useForm } from "react-hook-form";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { AuthLayout } from "@/shared/layouts/AuthLayout";
import { Icon } from "@/shared/components/Icon";
import { useAuth } from "@/features/auth/hooks/useAuth";

export function Login() {
  const { signIn, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [submitError, setSubmitError] = useState("");
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm({ defaultValues: { email: "", password: "" } });

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

  return <AuthLayout>
    <div className="auth-form-heading"><span className="section-label">Chào mừng trở lại</span><h1>Đăng nhập</h1><p>Tiếp tục câu chuyện của gia đình mình.</p></div>
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="auth-form" aria-busy={isSubmitting}>
      <div className="auth-field"><label htmlFor="email">Email</label><input id="email" required type="email" autoComplete="email" placeholder="Nhập địa chỉ email" aria-invalid={Boolean(errors.email)} aria-describedby={errors.email ? "email-error" : undefined} {...register("email", { setValueAs: (value) => value.trim(), required: "Bạn nhập email giúp mình nhé.", pattern: { value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: "Email chưa đúng định dạng." } })} />{errors.email && <p id="email-error" role="alert" className="field-error">{errors.email.message}</p>}</div>
      <div className="auth-field"><label htmlFor="password">Mật khẩu</label><input id="password" required type="password" autoComplete="current-password" placeholder="Nhập mật khẩu" aria-invalid={Boolean(errors.password)} aria-describedby={errors.password ? "password-error" : undefined} {...register("password", { validate: (value) => /\S/.test(value) || "Vui lòng nhập mật khẩu không chỉ gồm khoảng trắng.", required: "Bạn nhập mật khẩu giúp mình nhé.", minLength: { value: 6, message: "Mật khẩu cần có ít nhất 6 ký tự." } })} />{errors.password && <p id="password-error" role="alert" className="field-error">{errors.password.message}</p>}</div>
      {submitError && <p role="alert" className="form-error">{submitError}</p>}
      <button type="submit" disabled={isSubmitting} className="btn btn--primary auth-submit">{isSubmitting ? "Đang đăng nhập…" : <>Đăng nhập <Icon name="arrow-right" /></>}</button>
      <p role="status" className="sr-only">{isSubmitting ? "Đang đăng nhập…" : ""}</p>
    </form>
    <p className="auth-note"><Icon name="lock-keyhole" /> Dùng tài khoản đã đăng ký với FamilyConnect.</p>
    {import.meta.env.VITE_ENABLE_MOCK_AUTH === "true" && <p className="demo-note">Tài khoản demo: demo@familyconnect.vn · Family123!</p>}
  </AuthLayout>;
}
