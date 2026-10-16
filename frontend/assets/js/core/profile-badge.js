/* Đồng bộ ảnh đại diện của hồ sơ mẫu lên Topbar trên tất cả trang.
 * Chỉ dùng thông tin của localStorage; chưa liên kết tài khoản Backend.
 */
(function () {
  'use strict';
  const KEY = 'familyconnect.profile-demo.v1';
  function getProfile() {
    try {
      const state = JSON.parse(localStorage.getItem(KEY) || 'null');
      if (state?.version === 1 && state.profile) return state.profile;
    } catch (_) { /* localStorage bị chặn hoặc dữ liệu chưa hợp lệ */ }
    return { name: 'Nguyễn Văn A', avatar: '' };
  }
  const safeImage = s => typeof s === 'string' &&
    (/^data:image\/(jpeg|png);base64,[a-z\d+/=]+$/i.test(s) || /^\.\.\/assets\/images\/[\w-]+\.svg$/.test(s));
  function render() {
    const profile = getProfile();
    const name = (profile.name || 'Nguyễn Văn A').trim();
    const initials = name.split(/\s+/).slice(-2).map(word => word[0] || '').join('').toUpperCase();
    document.querySelectorAll('.topbar-right > .avatar[data-account-trigger]').forEach(link => {
      link.replaceChildren();
      link.setAttribute('aria-label', 'Mở menu tài khoản của ' + name);
      link.dataset.profileName = name;
      link.title = name;
      link.classList.toggle('has-photo', safeImage(profile.avatar));
      if (safeImage(profile.avatar)) {
        const img = document.createElement('img');
        img.src = profile.avatar;
        img.alt = '';
        link.append(img);
      } else {
        link.textContent = initials || 'VA';
      }
    });
  }
  document.addEventListener('DOMContentLoaded', render);
  window.addEventListener('familyconnect:profile-updated', render);
  window.addEventListener('storage', event => { if (event.key === KEY) render(); });
  window.FamilyProfileBadge = Object.freeze({ render });
}());
