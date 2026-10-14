/* Tiện ích giao diện chung. Không xử lý xác thực hoặc quyền API. */
(function () {
  'use strict';
  let toastTimer;
  function toast(message) {
    const node = document.getElementById('app-toast');
    if (!node) return;
    clearTimeout(toastTimer);
    node.textContent = message;
    node.hidden = false;
    toastTimer = setTimeout(() => { node.hidden = true; }, 4000);
  }
  function initDrawer() {
    const sidebar = document.getElementById('app-sidebar');
    const toggle = document.getElementById('menu-toggle');
    const close = document.getElementById('menu-close');
    const overlay = document.getElementById('drawer-overlay');
    const shell = document.querySelector('.app-shell');
    if (!sidebar || !toggle || !close || !overlay || !shell) return;
    const mobile = window.matchMedia('(max-width: 1023px)');
    let previousFocus;
    function setOpen(open, restoreFocus = true) {
      if (open && !mobile.matches) return;
      document.body.classList.toggle('drawer-open', open);
      toggle.setAttribute('aria-expanded', String(open));
      overlay.hidden = !open;
      sidebar.inert = mobile.matches && !open;
      shell.inert = open;
      if (open) {
        previousFocus = document.activeElement;
        close.focus();
      } else if (restoreFocus && previousFocus) {
        previousFocus.focus();
        previousFocus = null;
      }
    }
    toggle.addEventListener('click', () => setOpen(true));
    close.addEventListener('click', () => setOpen(false));
    overlay.addEventListener('click', () => setOpen(false));
    sidebar.addEventListener('keydown', (event) => {
      if (!document.body.classList.contains('drawer-open')) return;
      if (event.key === 'Escape') { event.preventDefault(); setOpen(false); }
      if (event.key === 'Tab') {
        const elements = [...sidebar.querySelectorAll('a[href],button:not([disabled])')]
          .filter(el => el.getClientRects().length > 0);
        const first = elements[0], last = elements[elements.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
      }
    });
    mobile.addEventListener('change', () => setOpen(false, false));
    setOpen(false, false);
  }
  window.FamilyUI = Object.freeze({ toast, initDrawer });
}());
