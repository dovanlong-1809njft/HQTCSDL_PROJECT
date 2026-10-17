/* Biểu mẫu xác thực bản xem trước — không liên hệ Google, Facebook hoặc SQL Server. */
(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  function show(message, error = false) {
    const node = $('auth-feedback');
    node.hidden = false;
    node.textContent = message;
    node.classList.toggle('error', error);
    node.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }
  function busy(button, working, text) {
    button.disabled = working;
    button.textContent = working ? 'Đang xử lý…' : text;
  }
  function init() {
    const A = window.FamilyDemoAuth;
    const login = document.body.dataset.authView === 'login';
    document.querySelectorAll('[data-reveal]').forEach(button => button.addEventListener('click', () => {
      const field = $(button.dataset.reveal);
      const visible = field.type === 'text';
      field.type = visible ? 'password' : 'text';
      button.textContent = visible ? 'Hiện' : 'Ẩn';
      button.setAttribute('aria-label', visible ? 'Hiện mật khẩu' : 'Ẩn mật khẩu');
    }));
    if (login) {
      if (new URLSearchParams(location.search).has('logged_out')) show('Bạn đã đăng xuất khỏi bản xem trước FamilyConnect.');
      const suggest = new URLSearchParams(location.search).get('username');
      if (suggest) $('login-identity').value = suggest;
      $('demo-fill').addEventListener('click', () => { $('login-identity').value = A.DEMO_EMAIL; $('login-password').value = A.DEMO_PASSWORD; $('login-password').focus(); });
      $('forgot-open').addEventListener('click', () => { $('forgot-panel').hidden = false; $('login-form').hidden = true; $('forgot-open').hidden = true; $('auth-title').textContent = 'Quên mật khẩu'; });
      $('forgot-close').addEventListener('click', () => { $('forgot-panel').hidden = true; $('login-form').hidden = false; $('forgot-open').hidden = false; $('auth-title').textContent = 'Chào mừng trở lại'; });
      document.querySelectorAll('[data-provider]').forEach(button => button.addEventListener('click', () => {
        show(`Đăng nhập bằng ${button.dataset.provider} cần tích hợp OAuth 2.0 phía Backend và cấu hình từ nhà cung cấp; bản Frontend hiện chưa hỗ trợ đăng nhập thật.`, false);
      }));
      $('login-form').addEventListener('submit', async event => {
        event.preventDefault();
        const button = $('login-submit');
        busy(button, true, 'Đăng nhập');
        try {
          await A.login($('login-identity').value, $('login-password').value);
          const next = new URLSearchParams(location.search).get('next');
          location.replace(next?A.targetPage(next):A.landingPage());
        } catch (error) { show(error.message || 'Không thể đăng nhập.', true); busy(button, false, 'Đăng nhập'); }
      });
    } else {
      $('register-form').addEventListener('submit', async event => {
        event.preventDefault();
        if ($('register-password').value !== $('register-repeat').value) { show('Hai lần nhập mật khẩu chưa trùng khớp.', true); return; }
        const button = $('register-submit');
        busy(button, true, 'Đăng ký');
        try {
          const created = await A.register({name:$('register-name').value,username:$('register-username').value,email:$('register-email').value,password:$('register-password').value});
          // Không tự động đăng nhập: người dùng cần đăng nhập bằng tài khoản vừa tạo.
          location.replace('login.html?username=' + encodeURIComponent(created.username));
        } catch (error) { show(error.message || 'Không thể tạo tài khoản.', true); busy(button, false, 'Đăng ký'); }
      });
    }
  }
  document.addEventListener('DOMContentLoaded', init, { once: true });
}());
