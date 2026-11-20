import { Link } from "react-router-dom";
import { Brand } from "@/shared/components/Brand";
import { Icon } from "@/shared/components/Icon";
import { useSiteSettings } from "@/features/admin-config/SiteSettings";

export function AuthLayout({ children, registering = false }) {
  const { settings, isPending, isError } = useSiteSettings();
  return <div className="auth-page">
    <a className="skip-link" href="#auth-main">Đến biểu mẫu</a>
    <header className="auth-header"><Brand to="/login" />{(registering || (!isPending && !isError && settings.registration_enabled)) && <p>{registering ? "Đã có tài khoản?" : "Chưa có tài khoản?"} <Link className="m-link" to={registering ? "/login" : "/register"}>{registering ? "Đăng nhập" : "Đăng ký"}<Icon name="arrow-up-right" /></Link></p>}</header>
    <main id="auth-main" className="auth-page-main" tabIndex={-1}><section className="hero auth-screen" data-enter aria-label={registering ? "Đăng ký thành viên" : "Đăng nhập tài khoản"}><div className="auth-main wrap">
      <div className="auth-story">
        <div className="section-label"><span className="label-dot" /> Không gian gia đình số</div>
        <p className="auth-headline">Gia phả và ký ức<br /> của <span>gia đình bạn.</span></p>
        <p className="auth-intro">Ghi lại cội nguồn, kết nối các thế hệ và lưu giữ những câu chuyện của gia đình.</p>
        <div className="generation-preview" role="img" aria-label="Sơ đồ kết nối ba thế hệ: ông bà, cha mẹ và con cháu">
          <div className="preview-topline"><span><Icon name="network" /> Kết nối các thế hệ</span><span className="preview-dots" aria-hidden="true">•••</span></div>
          <div className="generation-root"><span className="generation-avatar"><Icon name="heart-handshake" /></span><span>Ông bà<span className="generation-caption">Cội nguồn gia đình</span></span></div>
          <div className="generation-line" />
          <div className="generation-branches"><div className="generation-node"><span className="generation-avatar warm"><Icon name="users" /></span><span>Cha mẹ</span></div><div className="generation-node"><span className="generation-avatar"><Icon name="users" /></span><span>Cô, dì, chú, bác</span></div></div>
          <div className="generation-line" />
          <div className="generation-leaf"><Icon name="leaf" /><span>Thế hệ tiếp nối</span></div>
        </div>
        <div className="auth-topics"><span><Icon name="network" /> Gia phả</span><span><Icon name="book-open" /> Di sản</span><span><Icon name="award" /> Vinh danh</span></div>
      </div>
      <div className="auth-form-panel">{children}</div>
    </div></section></main>
    <footer className="auth-footer"><span>© {new Date().getFullYear()} {settings.site_name}</span><span>Gia phả · Di sản · Kết nối thế hệ</span></footer>
  </div>;
}
