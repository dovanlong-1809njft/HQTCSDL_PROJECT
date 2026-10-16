/* Avatar trên Topbar: Hồ sơ, chế độ Sáng/Tối và Đăng xuất (không cần React). */
(function () {
  'use strict';
  const AUTH = window.FamilyDemoAuth;
  function init() {
    const trigger = document.getElementById('fc-account-button');
    if (!trigger || !AUTH) return;
    const menu = document.createElement('div');
    menu.id = 'fc-account-menu';
    menu.className = 'fc-account-menu';
    menu.setAttribute('role', 'dialog');
    menu.setAttribute('aria-label', 'Tài khoản và giao diện');
    menu.hidden = true;
    menu.innerHTML = `
      <div class="fc-account-header"><span class="fc-account-header-icon" id="fc-menu-photo" aria-hidden="true">VA</span><div><div class="fc-account-name" id="fc-menu-name">Tài khoản</div><div class="fc-account-status">FamilyConnect · Bản dùng thử</div></div></div>
      <a class="fc-account-link" href="profile.html"><span class="fc-account-icon" aria-hidden="true">♙</span> Xem trang cá nhân <span style="margin-left:auto">›</span></a>
      <div class="fc-account-theme"><span class="fc-account-icon" aria-hidden="true">◐</span><span class="fc-theme-label" id="fc-theme-label">Giao diện sáng</span><button type="button" role="switch" class="fc-account-switch" id="fc-theme-toggle" aria-label="Chuyển chế độ sáng tối" aria-checked="false"></button></div>
      <div class="fc-account-hint">Gạt trái: Sáng · Gạt phải: Tối</div>
      <button type="button" class="fc-account-logout" id="fc-logout"><span class="fc-account-icon" aria-hidden="true">↪</span> Đăng xuất</button>`;
    document.body.append(menu);
    trigger.setAttribute('aria-controls', 'fc-account-menu');
    trigger.setAttribute('aria-expanded', 'false');
    trigger.setAttribute('aria-haspopup', 'dialog');
    trigger.setAttribute('title', 'Tài khoản và giao diện');
    const toggle = menu.querySelector('#fc-theme-toggle');
    function syncTheme() {
      const isDark = AUTH.getTheme() === 'dark';
      toggle.setAttribute('aria-checked', String(isDark));
      menu.querySelector('#fc-theme-label').textContent = isDark ? 'Giao diện tối' : 'Giao diện sáng';
    }
    function syncProfile() {
      const node = menu.querySelector('#fc-menu-photo');
      const name = menu.querySelector('#fc-menu-name');
      const avatar = trigger.querySelector('img');
      name.textContent = trigger.dataset.profileName || AUTH.getSession()?.name || 'Tài khoản';
      node.replaceChildren();
      if (avatar) { const image = document.createElement('img'); image.src = avatar.src; image.alt = ''; node.append(image); }
      else node.textContent = trigger.textContent.trim() || 'VA';
    }
    function position() {
      if (menu.hidden) return;
      const r = trigger.getBoundingClientRect();
      const width = menu.getBoundingClientRect().width;
      menu.style.top = Math.min(innerHeight - 40, r.bottom + 12) + 'px';
      menu.style.left = Math.max(10, Math.min(innerWidth - width - 10, r.right - width)) + 'px';
    }
    function close(restoreFocus = false) {
      menu.hidden = true;
      trigger.setAttribute('aria-expanded', 'false');
      if (restoreFocus) trigger.focus();
    }
    function open() { syncTheme(); syncProfile(); menu.hidden = false; trigger.setAttribute('aria-expanded', 'true'); position(); menu.querySelector('.fc-account-link').focus(); }
    trigger.addEventListener('click', event => { event.preventDefault(); menu.hidden ? open() : close(true); });
    document.addEventListener('pointerdown', event => { if (!menu.hidden && !menu.contains(event.target) && !trigger.contains(event.target)) close(); });
    document.addEventListener('keydown', event => { if (event.key === 'Escape' && !menu.hidden) { event.preventDefault(); close(true); } });
    window.addEventListener('resize', position);
    window.addEventListener('scroll', position, true);
    menu.querySelector('#fc-logout').addEventListener('click', () => AUTH.signOut());
    toggle.addEventListener('click', () => { AUTH.setTheme(AUTH.getTheme() === 'dark' ? 'light' : 'dark'); syncTheme(); });
    window.addEventListener('familyconnect:profile-updated', syncProfile);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
}());
