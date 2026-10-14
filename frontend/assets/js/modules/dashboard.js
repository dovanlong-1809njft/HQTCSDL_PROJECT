/* Bước 1: dashboard dữ liệu mẫu, không gọi API/SQL Server, không giả xác thực.
   Các bộ dữ liệu ở đây sẽ được thay bằng /families/{family_id}/dashboard. */
(function () {
  'use strict';
  const families = {
    nguyen: {
      members: 48, generations: 4, posts: 26, heritage: 12,
      activities: [
        { initials: 'VB', name: 'Nguyễn Văn B', action: 'chia sẻ câu chuyện về ngôi nhà của ông bà.', time: '2 giờ trước', type: 'post', tag: 'Bài đăng' },
        { initials: 'TC', name: 'Nguyễn Thị C', action: 'thêm tư liệu “Những mùa Tết sum vầy”.', time: '5 giờ trước', type: 'heritage', tag: 'Tư liệu' },
        { initials: 'VD', name: 'Nguyễn Văn D', action: 'cập nhật hồ sơ một người trong gia phả.', time: 'Hôm qua', type: 'member', tag: 'Thành viên' },
        { initials: 'TE', name: 'Nguyễn Thị E', action: 'chia sẻ lời chúc đến cả gia đình.', time: 'Hôm qua', type: 'post', tag: 'Bài đăng' }
      ],
      events: [
        { id: 'n1', day: 20, month: 10, title: 'Bữa cơm gặp mặt gia đình', time: '18:00 · 20/10/2026', place: 'Nhà ông bà · địa điểm mẫu', description: 'Một buổi tối cùng ăn cơm, trò chuyện và chia sẻ những câu chuyện gần đây.' },
        { id: 'n2', day: 1, month: 11, title: 'Ngày lưu giữ kỷ niệm', time: '09:00 · 01/11/2026', place: 'Không gian gia đình · địa điểm mẫu', description: 'Cùng chọn ảnh cũ, ghi lại lời kể và bổ sung tư liệu vào kho tàng gia đình.' }
      ]
    },
    le: {
      members: 32, generations: 3, posts: 18, heritage: 8,
      activities: [
        { initials: 'VA', name: 'Lê Văn A', action: 'chia sẻ ảnh buổi gặp mặt cuối tuần.', time: '1 giờ trước', type: 'post', tag: 'Bài đăng' },
        { initials: 'TB', name: 'Lê Thị B', action: 'thêm câu chuyện “Một thời tuổi nhỏ”.', time: '3 giờ trước', type: 'heritage', tag: 'Tư liệu' },
        { initials: 'VC', name: 'Lê Văn C', action: 'cập nhật hồ sơ người thân.', time: 'Hôm qua', type: 'member', tag: 'Thành viên' }
      ],
      events: [
        { id: 'l1', day: 25, month: 10, title: 'Gặp mặt cuối tháng', time: '10:00 · 25/10/2026', place: 'Nhà người thân · địa điểm mẫu', description: 'Một cuộc hẹn nhỏ để các thành viên gặp nhau và lên kế hoạch sinh hoạt tháng tới.' }
      ]
    }
  };
  const registrations = new Set(); // Chỉ giữ trong bộ nhớ tab, tải lại sẽ mất.
  let selectedEvent = null;
  const picker = document.getElementById('family-picker');
  if (!picker) return;
  const filter = document.getElementById('activity-filter');
  const list = document.getElementById('activity-list');
  const dialog = document.getElementById('event-dialog');
  const rsvp = document.getElementById('event-rsvp');
  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }
  function renderActivities() {
    const data = families[picker.value];
    const items = data.activities.filter(item => filter.value === 'all' || filter.value === item.type);
    list.replaceChildren();
    items.forEach(item => {
      const row = element('li', 'activity-row');
      const avatar = element('span', 'activity-avatar', item.initials);
      avatar.setAttribute('aria-hidden', 'true');
      const copy = element('div', 'activity-copy');
      const text = element('p');
      text.append(element('strong', '', item.name), document.createTextNode(' ' + item.action));
      copy.append(text, element('span', 'activity-meta', item.time));
      row.append(avatar, copy, element('span', 'activity-tag', item.tag));
      list.append(row);
    });
    document.getElementById('activity-empty').hidden = items.length > 0;
  }
  function openEvent(event) {
    selectedEvent = event;
    document.getElementById('event-dialog-title').textContent = event.title;
    document.getElementById('event-description').textContent = event.description;
    document.getElementById('event-time').textContent = event.time;
    document.getElementById('event-place').textContent = event.place;
    updateRsvp();
    dialog.showModal();
  }
  function updateRsvp() {
    const going = registrations.has(selectedEvent.id);
    rsvp.textContent = going ? 'Hủy xác nhận thử' : 'Thử xác nhận tham gia';
    document.getElementById('event-demo-note').textContent = going
      ? 'Đã xác nhận thử. Dữ liệu chỉ giữ trong tab hiện tại và sẽ mất khi tải lại.'
      : 'Thao tác thử trong giao diện; chưa gửi đăng ký đến máy chủ.';
  }
  function renderEvents() {
    const target = document.getElementById('events-list');
    target.replaceChildren();
    families[picker.value].events.forEach(event => {
      const row = element('article', 'event-row');
      const date = element('div', 'date-box');
      date.setAttribute('aria-hidden', 'true');
      date.append(element('span', '', 'THÁNG ' + event.month), element('strong', '', String(event.day).padStart(2, '0')));
      const copy = element('div', 'event-info');
      const button = element('button', 'btn-link', 'Xem chi tiết →');
      button.type = 'button';
      button.setAttribute('aria-label', 'Xem chi tiết: ' + event.title);
      button.addEventListener('click', () => openEvent(event));
      copy.append(element('h3', '', event.title), element('p', '', event.time), button);
      row.append(date, copy);
      target.append(row);
    });
  }
  function render() {
    const data = families[picker.value];
    ['members', 'generations', 'posts', 'heritage'].forEach(key => {
      document.getElementById('stat-' + key).textContent = String(data[key]);
    });
    renderActivities();
    renderEvents();
  }
  picker.addEventListener('change', () => { render(); window.FamilyUI?.toast('Đã chuyển sang ' + picker.selectedOptions[0].textContent); });
  filter.addEventListener('change', renderActivities);
  document.getElementById('event-close').addEventListener('click', () => dialog.close());
  document.getElementById('event-cancel').addEventListener('click', () => dialog.close());
  rsvp.addEventListener('click', () => {
    const going = registrations.has(selectedEvent.id);
    if (going) registrations.delete(selectedEvent.id);
    else registrations.add(selectedEvent.id);
    updateRsvp();
    window.FamilyUI?.toast(going ? 'Đã hủy xác nhận mẫu.' : 'Đã xác nhận mẫu; chưa gửi đến máy chủ.');
  });
  render();
}());
