import { useState } from "react";
import { useForm } from "react-hook-form";
import { Navigate, useNavigate } from "react-router-dom";
import { AuthLayout } from "@/shared/layouts/AuthLayout";
import { Icon } from "@/shared/components/Icon";
import { useAuth } from "@/features/auth/hooks/useAuth";

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

  return <AuthLayout registering>
    <div className="auth-form-heading"><span className="section-label">Không gian dành cho các thế hệ</span><h1>Tạo tài khoản</h1><p>Tham gia và lưu giữ câu chuyện gia đình.</p></div>
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="auth-form" aria-busy={isSubmitting}>
      <div className="auth-field"><label htmlFor="full_name">Họ và tên</label><input id="full_name" autoComplete="name" placeholder="Nhập họ và tên" aria-invalid={Boolean(errors.full_name)} aria-describedby={errors.full_name ? "name-error" : undefined} {...register("full_name", { required: "Bạn nhập họ tên nhé.", minLength: { value: 2, message: "Họ tên cần ít nhất 2 ký tự." }, maxLength: { value: 200, message: "Họ tên không quá 200 ký tự." } })} />{errors.full_name && <p id="name-error" role="alert" className="field-error">{errors.full_name.message}</p>}</div>
      <div className="auth-field"><label htmlFor="email">Email</label><input id="email" type="email" autoComplete="email" placeholder="Nhập địa chỉ email" aria-invalid={Boolean(errors.email)} aria-describedby={errors.email ? "email-error" : undefined} {...register("email", { required: "Bạn nhập email nhé.", pattern: { value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: "Email chưa đúng định dạng." } })} />{errors.email && <p id="email-error" role="alert" className="field-error">{errors.email.message}</p>}</div>
      <div className="auth-field"><label htmlFor="password">Mật khẩu</label><input id="password" type="password" autoComplete="new-password" placeholder="Ít nhất 8 ký tự" aria-invalid={Boolean(errors.password)} aria-describedby={errors.password ? "password-error" : undefined} {...register("password", { required: "Bạn tạo mật khẩu nhé.", minLength: { value: 8, message: "Mật khẩu cần ít nhất 8 ký tự." }, maxLength: { value: 128, message: "Mật khẩu không quá 128 ký tự." } })} />{errors.password && <p id="password-error" role="alert" className="field-error">{errors.password.message}</p>}</div>
      <div className="auth-field"><label htmlFor="confirmPassword">Nhập lại mật khẩu</label><input id="confirmPassword" type="password" autoComplete="new-password" placeholder="Nhập lại mật khẩu" aria-invalid={Boolean(errors.confirmPassword)} aria-describedby={errors.confirmPassword ? "confirm-error" : undefined} {...register("confirmPassword", { required: "Bạn nhập lại mật khẩu nhé.", validate: (value) => value === watch("password") || "Hai mật khẩu chưa trùng nhau." })} />{errors.confirmPassword && <p id="confirm-error" role="alert" className="field-error">{errors.confirmPassword.message}</p>}</div>
      {submitError && <p role="alert" className="form-error">{submitError}</p>}
      <button type="submit" disabled={isSubmitting} className="btn btn--primary auth-submit">{isSubmitting ? "Đang tạo tài khoản…" : <>Đăng ký <Icon name="arrow-right" /></>}</button>
      <p role="status" className="sr-only">{isSubmitting ? "Đang tạo tài khoản…" : ""}</p>
    </form>
  </AuthLayout>;
}
