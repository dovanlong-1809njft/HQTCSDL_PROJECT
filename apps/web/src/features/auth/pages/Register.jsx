import { useState } from "react";
import { useForm } from "react-hook-form";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { AuthLayout } from "@/shared/layouts/AuthLayout";
import { Icon } from "@/shared/components/Icon";
import { useAuth } from "@/features/auth/hooks/useAuth";
import { getApiErrorMessage } from "@/shared/api/client";
import { useSiteSettings } from "@/features/admin-config/SiteSettings";

export function Register() {
  const { signUp, isAuthenticated } = useAuth();
  const site = useSiteSettings();
  const navigate = useNavigate();
  const [submitError, setSubmitError] = useState("");
  const { register, handleSubmit, watch, formState: { errors, isSubmitting } } = useForm();

  if (isAuthenticated) return <Navigate to="/dashboard" replace />;
  if (site.isPending) return <AuthLayout registering><p role="status">Đang tải thiết lập đăng ký…</p></AuthLayout>;
  if (site.isError) return <AuthLayout registering><p role="alert">Chưa tải được thiết lập đăng ký. Vui lòng thử lại.</p><button type="button" className="btn btn--primary" onClick={() => site.refetch()}>Thử lại</button></AuthLayout>;
  if (!site.settings.registration_enabled) return <AuthLayout registering><div className="auth-form-heading"><h1>Đăng ký đang tạm đóng</h1><p>Vui lòng liên hệ quản trị viên để được hỗ trợ. Nếu đã có tài khoản, bạn vẫn có thể đăng nhập.</p></div><Link className="btn btn--primary mt-6" to="/login">Đăng nhập</Link></AuthLayout>;

  const onSubmit = async (values) => {
    setSubmitError("");
    try {
      await signUp({ full_name: values.full_name, email: values.email, password: values.password });
      navigate("/dashboard", { replace: true });
    } catch (error) {
      setSubmitError(getApiErrorMessage(error));
      if (error.response?.status === 403) site.refetch();
    }
  };

  return <AuthLayout registering>
    <div className="auth-form-heading"><span className="section-label">Không gian dành cho các thế hệ</span><h1>Tạo tài khoản</h1><p>Tham gia và lưu giữ câu chuyện gia đình.</p></div>
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="auth-form" aria-busy={isSubmitting}>
      <div className="auth-field"><label htmlFor="full_name">Họ và tên</label><input id="full_name" required autoComplete="name" placeholder="Nhập họ và tên" aria-invalid={Boolean(errors.full_name)} aria-describedby={errors.full_name ? "name-error" : undefined} {...register("full_name", { setValueAs: (value) => value.trim(), required: "Bạn nhập họ tên nhé.", minLength: { value: 2, message: "Họ tên cần ít nhất 2 ký tự." }, maxLength: { value: 200, message: "Họ tên không quá 200 ký tự." } })} />{errors.full_name && <p id="name-error" role="alert" className="field-error">{errors.full_name.message}</p>}</div>
      <div className="auth-field"><label htmlFor="email">Email</label><input id="email" required type="email" autoComplete="email" placeholder="Nhập địa chỉ email" aria-invalid={Boolean(errors.email)} aria-describedby={errors.email ? "email-error" : undefined} {...register("email", { setValueAs: (value) => value.trim(), required: "Bạn nhập email nhé.", pattern: { value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: "Email chưa đúng định dạng." } })} />{errors.email && <p id="email-error" role="alert" className="field-error">{errors.email.message}</p>}</div>
      <div className="auth-field"><label htmlFor="password">Mật khẩu</label><input id="password" required type="password" autoComplete="new-password" placeholder="Ít nhất 8 ký tự" aria-invalid={Boolean(errors.password)} aria-describedby={errors.password ? "password-error" : undefined} {...register("password", { validate: (value) => /\S/.test(value) || "Vui lòng nhập mật khẩu không chỉ gồm khoảng trắng.", required: "Bạn tạo mật khẩu nhé.", minLength: { value: 8, message: "Mật khẩu cần ít nhất 8 ký tự." }, maxLength: { value: 128, message: "Mật khẩu không quá 128 ký tự." } })} />{errors.password && <p id="password-error" role="alert" className="field-error">{errors.password.message}</p>}</div>
      <div className="auth-field"><label htmlFor="confirmPassword">Nhập lại mật khẩu</label><input id="confirmPassword" required type="password" autoComplete="new-password" placeholder="Nhập lại mật khẩu" aria-invalid={Boolean(errors.confirmPassword)} aria-describedby={errors.confirmPassword ? "confirm-error" : undefined} {...register("confirmPassword", { required: "Bạn nhập lại mật khẩu nhé.", validate: (value) => value === watch("password") || "Hai mật khẩu chưa trùng nhau." })} />{errors.confirmPassword && <p id="confirm-error" role="alert" className="field-error">{errors.confirmPassword.message}</p>}</div>
      {submitError && <p role="alert" className="form-error">{submitError}</p>}
      <button type="submit" disabled={isSubmitting} className="btn btn--primary auth-submit">{isSubmitting ? "Đang tạo tài khoản…" : <>Đăng ký <Icon name="arrow-right" /></>}</button>
      <p role="status" className="sr-only">{isSubmitting ? "Đang tạo tài khoản…" : ""}</p>
    </form>
  </AuthLayout>;
}
