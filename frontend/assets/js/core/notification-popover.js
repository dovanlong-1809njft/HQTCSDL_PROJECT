/* Bảng thông báo nổi dùng chung — rút gọn của trang notifications.html.
 * Dữ liệu và trạng thái đọc dùng cùng FamilyStore + NotificationDemo.
 * Không gửi thông báo đẩy/email; chỉ hiển thị dữ liệu mẫu ở trình duyệt.
 */
(function () {
  'use strict';
  const S = window.FamilyStore, N = window.NotificationDemo;
  if (!S || !N) return;

  const make = (tag, className, text) => {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = String(text);
    return node;
  };
  let isOpen = false, category = 'all', unreadOnly = false;
  let button, pop, list, tabs, status, unreadToggle;

  function relative(value) {
    const at = N.parseTime(value);
    if (!Number.isFinite(at)) return 'Không rõ thời gian';
    const d = Date.now() - at;
    if (d < 0) return new Date(at).toLocaleDateString('vi-VN') + ' · Dữ liệu mẫu';
    if (d < 60000) return 'Vừa xong';
    if (d < 3600000) return Math.floor(d / 60000) + ' phút trước';
    if (d < 86400000) return Math.floor(d / 3600000) + ' giờ trước';
    return new Date(at).toLocaleDateString('vi-VN', {timeZone:'Asia/Ho_Chi_Minh'});
  }
  function initials(text) {
    return String(text || '?').trim().split(/\s+/).slice(-2).map(t => t[0] || '').join('').toUpperCase();
  }
  function groupLabel(n) {
    const at = N.parseTime(n.at);
    if (!Number.isFinite(at)) return 'Không rõ thời gian';
    const today = N.dayKey(), key = N.dayKey(at);
    if (key > today) return 'Sắp tới (theo dữ liệu mẫu)';
    if (key === today) return 'Hôm nay';
    if (Date.parse(today + 'T00:00:00Z') - Date.parse(key + 'T00:00:00Z') === 86400000) return 'Hôm qua';
    return 'Trước đó';
  }
  function linkFor(n) {
    const t = n.target || {};
    const familyId = encodeURIComponent(S.getActive());
    if (t.kind === 'post') return 'community.html?family=' + familyId + '#post-' + encodeURIComponent(t.id);
    if (t.kind === 'event') return 'events.html?family=' + familyId + '&event=' + encodeURIComponent(t.id);
    if (t.kind === 'resource') return 'heritage.html';
    if (t.kind === 'member' || t.kind === 'birthday') return 'directory.html';
    return /^(family|genealogy|community|events|heritage|directory|profile|notifications)\.html$/.test(t.page || '') ? t.page : 'notifications.html';
  }
  function markRead(id) {
    const f = S.get(), state = N.settings(f);
    state.readIds = [...new Set([...state.readIds, id])];
    f.notificationData = state;
    S.update(f);
    N.updateBadges();
  }
  function markAllRead() {
    const f = S.get(), state = N.settings(f);
    const ids = N.visible(f).filter(n => category === 'all' || n.category === category).map(n => n.id);
    if (!ids.length) return;
    state.readIds = [...new Set([...state.readIds, ...ids])];
    f.notificationData = state;
    S.update(f);
    render();
  }
  function position() {
    if (!pop || !button) return;
    const rect = button.getBoundingClientRect();
    pop.style.top = Math.max(8, rect.bottom + 9) + 'px';
    pop.style.right = Math.max(10, window.innerWidth - rect.right - 9) + 'px';
    pop.style.maxHeight = Math.max(260, window.innerHeight - rect.bottom - 22) + 'px';
  }
  function render() {
    if (!pop) return;
    const items = N.visible(S.get());
    const shown = items.filter(n => (category === 'all' || n.category === category) && (!unreadOnly || !n.read));
    const unread = items.filter(n => !n.read).length;
    status.textContent = unread ? unread + ' thông báo chưa đọc' : 'Bạn đã đọc hết thông báo';
    unreadToggle.setAttribute('aria-pressed', String(unreadOnly));
    unreadToggle.classList.toggle('is-active', unreadOnly);
    tabs.replaceChildren();
    [['all', 'Tất cả'], ...Object.entries(N.labels)].forEach(([key, label]) => {
      const b = make('button', 'fc-notice-tab' + (category === key ? ' is-active' : ''), label);
      b.type = 'button'; b.setAttribute('aria-pressed', String(category === key));
      b.onclick = () => { category = key; render(); };
      tabs.append(b);
    });
    list.replaceChildren();
    if (!shown.length) {
      list.append(make('div', 'fc-notice-empty', 'Không có thông báo phù hợp với bộ lọc.'));
      return;
    }
    let lastGroup = '';
    shown.slice(0, 20).forEach(n => {
      const group = groupLabel(n);
      if (group !== lastGroup) {
        list.append(make('h3', 'fc-notice-group', group));
        lastGroup = group;
      }
      const row = make('a', 'fc-notice-row' + (n.read ? '' : ' is-unread'));
      row.href = linkFor(n);
      row.addEventListener('click', () => markRead(n.id));
      const symbol = make('span', 'fc-notice-avatar', n.actor ? initials(n.actor) : N.symbols[n.category]);
      symbol.setAttribute('aria-hidden', 'true');
      const content = make('span', 'fc-notice-copy');
      const title = make('strong', '', n.title);
      const preview = make('span', 'fc-notice-excerpt', n.text);
      const meta = make('span', 'fc-notice-meta', N.labels[n.category] + ' · ' + relative(n.at));
      content.append(title, preview, meta);
      row.append(symbol, content);
      if (!n.read) {
        const dot = make('span', 'fc-notice-unread');
        dot.setAttribute('aria-label', 'Chưa đọc');
        row.append(dot);
      }
      list.append(row);
    });
    if (shown.length > 20) list.append(make('p', 'fc-notice-more', 'Còn ' + (shown.length - 20) + ' thông báo · Chọn “Xem toàn bộ” để xem tiếp.'));
  }
  function open() {
    isOpen = true; pop.hidden = false; button.setAttribute('aria-expanded', 'true');
    position(); render();
  }
  function close(returnFocus = false) {
    if (!isOpen) return;
    isOpen = false; pop.hidden = true; button.setAttribute('aria-expanded', 'false');
    if (returnFocus) button.focus();
  }
  function init() {
    button = document.querySelector('.topbar .notification-trigger');
    if (!button) return;
    pop = make('section', 'fc-notification-popover'); pop.id = 'fc-notification-popover';
    pop.setAttribute('role', 'dialog'); pop.setAttribute('aria-label', 'Thông báo nhanh'); pop.hidden = true;
    const header = make('div', 'fc-notice-header');
    const heading = make('div'); heading.append(make('h2', '', 'Thông báo'), (status = make('p', '', '')));
    const closeButton = make('button', 'fc-notice-close', '×');
    closeButton.type = 'button'; closeButton.setAttribute('aria-label', 'Đóng thông báo');
    closeButton.onclick = () => close(true);
    header.append(heading, closeButton);
    const toolbar = make('div', 'fc-notice-toolbar');
    unreadToggle = make('button', 'fc-notice-action', 'Chưa đọc'); unreadToggle.type = 'button';
    unreadToggle.onclick = () => { unreadOnly = !unreadOnly; render(); };
    const markButton = make('button', 'fc-notice-action', 'Đánh dấu đã đọc');
    markButton.type = 'button'; markButton.onclick = markAllRead;
    toolbar.append(unreadToggle, markButton);
    tabs = make('div', 'fc-notice-tabs'); tabs.setAttribute('role', 'group'); tabs.setAttribute('aria-label', 'Lọc theo loại thông báo');
    list = make('div', 'fc-notice-list'); list.setAttribute('aria-live', 'polite');
    const footer = make('div', 'fc-notice-footer');
    const all = make('a', 'fc-notice-full', 'Mở rộng · Xem toàn bộ thông báo →'); all.href = 'notifications.html';
    footer.append(all);
    pop.append(header, toolbar, tabs, list, footer);
    document.body.append(pop);
    button.onclick = () => { if (isOpen) close(true); else open(); };
    document.addEventListener('pointerdown', event => {
      if (isOpen && !pop.contains(event.target) && !button.contains(event.target)) close();
    });
    document.addEventListener('keydown', event => {
      if (event.key === 'Escape' && isOpen) { event.preventDefault(); close(true); }
    });
    window.addEventListener('resize', () => { if (isOpen) position(); });
    window.addEventListener('scroll', () => { if (isOpen) position(); }, { passive: true });
    window.addEventListener('familyconnect:change', () => { if (isOpen) render(); });
    window.addEventListener('storage', event => { if (event.key && event.key.includes('familyconnect') && isOpen) { S.refresh(); render(); } });
    N.updateBadges();
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init, { once: true });
  else init();
}());
