/* FamilyConnect — điều khiển Sidebar Desktop: hover, focus và ghim.
 * Không dùng React hoặc thư viện ngoài. Trên mobile sử dụng drawer trong core/ui.js.
 */
(function () {
  'use strict';
  const PIN_KEY = 'familyconnect.sidebar.pinned.v1';
  const mobile = window.matchMedia('(max-width: 1023px)');

  function initSidebar() {
    const sidebar = document.getElementById('app-sidebar');
    const pinButton = document.getElementById('sidebar-pin');
    if (!sidebar || !pinButton) return;

    let pinned = false;
    try { pinned = window.localStorage.getItem(PIN_KEY) === 'true'; }
    catch (_error) { /* Một số trình duyệt không cho lưu localStorage. */ }

    let hovered = false;
    let focusInside = false;

    function update() {
      const expanded = !mobile.matches && (pinned || hovered || focusInside);
      document.body.classList.add('sidebar-enhanced');
      sidebar.classList.toggle('is-expanded', expanded);
      sidebar.classList.toggle('is-pinned', pinned);
      pinButton.setAttribute('aria-pressed', String(pinned));
      pinButton.setAttribute('aria-label', pinned ? 'Bỏ ghim thanh điều hướng' : 'Ghim thanh điều hướng ở trạng thái mở');
      pinButton.title = pinned ? 'Bỏ ghim Sidebar' : 'Ghim Sidebar luôn mở';
    }

    sidebar.addEventListener('pointerenter', (event) => {
      if (event.pointerType === 'touch' || mobile.matches) return;
      hovered = true;
      update();
    });
    sidebar.addEventListener('pointerleave', () => {
      hovered = false;
      update();
    });
    sidebar.addEventListener('focusin', () => {
      if (mobile.matches) return;
      focusInside = true;
      update();
    });
    sidebar.addEventListener('focusout', (event) => {
      if (sidebar.contains(event.relatedTarget)) return;
      focusInside = false;
      update();
    });
    pinButton.addEventListener('click', () => {
      pinned = !pinned;
      try { window.localStorage.setItem(PIN_KEY, String(pinned)); }
      catch (_error) { /* Vẫn ghim được trong phiên hiện tại. */ }
      update();
    });
    mobile.addEventListener('change', () => {
      hovered = false;
      focusInside = false;
      update();
    });
    update();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initSidebar, { once: true });
  } else {
    initSidebar();
  }
}());
