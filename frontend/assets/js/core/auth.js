/* FamilyConnect — xác thực MÔ PHỎNG cho Frontend HTML/CSS/JS.
 * CẢNH BÁO: localStorage KHÔNG phải một hệ thống xác thực hoặc phân quyền bảo mật.
 * Dữ liệu tài khoản chỉ có trên trình duyệt này; OAuth Google/Facebook, email reset và
 * session thực phải được xử lý phía Backend sau này. Không dùng để triển khai công khai.
 */
(function () {
  'use strict';
  const K_SESSION = 'familyconnect.demo.session.v1';
  const K_USERS = 'familyconnect.demo.accounts.v1';
  const K_PROFILE = 'familyconnect.profile-demo.v1';
  const K_PROFILE_OWNER = 'familyconnect.demo.profile-owner.v1';
  const PROFILE_PREFIX = 'familyconnect.demo.user-profile.';
  const K_THEME = 'familyconnect.theme.v1';
  const DEMO_EMAIL = 'demo@familyconnect.local';
  const DEMO_PASSWORD = 'Demo@12345';

  const readJSON = (key, fallback) => { try { return JSON.parse(localStorage.getItem(key) || 'null') ?? fallback; } catch (_) { return fallback; } };
  const storeJSON = (key, value) => { localStorage.setItem(key, JSON.stringify(value)); };
  function getSession() {
    const s = readJSON(K_SESSION, null);
    if (s && readJSON('familyconnect.demo.blocked.v1', []).includes(s.id)) return null;
    return s && s.mode === 'frontend-preview' && typeof s.id === 'string' && typeof s.name === 'string' ? s : null;
  }
  function getTheme() { try { return localStorage.getItem(K_THEME) === 'dark' ? 'dark' : 'light'; } catch (_) { return 'light'; } }
  function setTheme(theme) {
    const safe = theme === 'dark' ? 'dark' : 'light';
    document.documentElement.dataset.theme = safe;
    try { localStorage.setItem(K_THEME, safe); } catch (_) { /* Chấp nhận chế độ không lưu. */ }
    window.dispatchEvent(new CustomEvent('familyconnect:theme-changed', { detail: { theme: safe } }));
    return safe;
  }
  document.documentElement.dataset.theme = getTheme(); // Áp dụng sớm, tránh nháy sáng khi chuyển trang.

  function profilesSwitch(id, name, email) {
    try {
      const previous = localStorage.getItem(K_PROFILE_OWNER);
      const current = localStorage.getItem(K_PROFILE);
      if (previous && previous !== id && current) localStorage.setItem(PROFILE_PREFIX + previous, current);
      const saved = localStorage.getItem(PROFILE_PREFIX + id);
      if (saved) localStorage.setItem(K_PROFILE, saved);
      else if (!previous || previous !== id) {
        const initial = { version: 1, profile: { name, bio: 'Giữ gìn cội nguồn, hướng tới tương lai.', email: email || '', avatar: '', cover: '' } };
        if (id === 'demo' && !previous && current) { /* Tôn trọng hồ sơ mẫu đã chỉnh trước khi có đăng nhập. */ }
        else localStorage.setItem(K_PROFILE, JSON.stringify(initial));
      }
      localStorage.setItem(K_PROFILE_OWNER, id);
    } catch (_) { /* Browser chặn storage. */ }
  }
  function startSession(account) {
    profilesSwitch(account.id, account.name, account.email);
    const session = { id: account.id, name: account.name, email: account.email || '', mode: 'frontend-preview', startedAt: Date.now() };
    storeJSON(K_SESSION, session);
    return session;
  }
  function signOut() {
    const current = getSession();
    if (current) { try { const profile = localStorage.getItem(K_PROFILE); if (profile) localStorage.setItem(PROFILE_PREFIX + current.id, profile); } catch (_) {} }
    try { localStorage.removeItem(K_SESSION); } catch (_) {}
    window.location.replace('login.html?logged_out=1');
  }
  const accounts = () => {
    const list = readJSON(K_USERS, []);
    return Array.isArray(list) ? list.filter(a => typeof a === 'object' && a !== null) : [];
  };
  const bytesToB64 = bytes => btoa(String.fromCharCode(...new Uint8Array(bytes)));
  const b64ToBytes = s => Uint8Array.from(atob(s), c => c.charCodeAt(0));
  async function derive(password, salt) {
    if (!window.crypto?.subtle) throw Error('Trình duyệt không hỗ trợ Web Crypto. Hãy mở ứng dụng qua http://localhost:5500.');
    const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(password), 'PBKDF2', false, ['deriveBits']);
    const bits = await crypto.subtle.deriveBits({ name: 'PBKDF2', salt, iterations: 120000, hash: 'SHA-256' }, key, 256);
    return bytesToB64(bits);
  }
  async function register({ name, username, email, password }) {
    name = String(name || '').trim(); username = String(username || '').trim().toLowerCase(); email = String(email || '').trim().toLowerCase();
    if (name.length < 2 || name.length > 80) throw Error('Họ và tên phải có từ 2 đến 80 ký tự.');
    if (!/^[a-z0-9_]{3,32}$/.test(username)) throw Error('Tên tài khoản gồm 3–32 ký tự chữ thường, số hoặc dấu gạch dưới.');
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) || email.length > 120) throw Error('Vui lòng nhập email hợp lệ.');
    if (password.length < 8 || password.length > 128) throw Error('Mật khẩu phải có từ 8 đến 128 ký tự.');
    if (email === DEMO_EMAIL || username === 'demo' || accounts().some(a => a.email === email || a.username === username)) throw Error('Email hoặc tên tài khoản đã được dùng trong bản xem trước.');
    const salt = crypto.getRandomValues(new Uint8Array(16));
    const hash = await derive(password, salt);
    const account = { id: 'preview-' + crypto.randomUUID(), name, username, email, salt: bytesToB64(salt), hash, createdAt: Date.now() };
    try { storeJSON(K_USERS, [...accounts(), account]); } catch (_) { throw Error('Không thể lưu tài khoản mẫu trên trình duyệt. Hãy kiểm tra bộ nhớ hoặc chế độ riêng tư.'); }
    return { username, email };
  }
  async function login(identity, password) {
    identity = String(identity || '').trim().toLowerCase();
    if (!identity || !password) throw Error('Vui lòng nhập tên tài khoản và mật khẩu.');
    if ((identity === DEMO_EMAIL || identity === 'demo') && password === DEMO_PASSWORD) return startSession({ id: 'demo', name: 'Nguyễn Văn A', email: DEMO_EMAIL });
    const account = accounts().find(a => a.username === identity || a.email === identity);
    if(account&&readJSON('familyconnect.demo.blocked.v1',[]).includes(account.id))throw Error('Tài khoản mẫu đã bị khóa.');
    if (!account || !account.hash || !account.salt) throw Error('Tên tài khoản hoặc mật khẩu không chính xác.');
    let candidate;
    try { candidate = await derive(password, b64ToBytes(account.salt)); }
    catch (_) { throw Error('Không thể xác minh tài khoản mẫu trên trình duyệt này.'); }
    if (candidate !== account.hash) throw Error('Tên tài khoản hoặc mật khẩu không chính xác.');
    return startSession(account);
  }
  function targetPage(raw) {
    // Chỉ điều hướng nội bộ tới các trang trong whitelist; không dùng URL do bên ngoài cung cấp.
    const allowed = ['dashboard','family','genealogy','directory','community','events','heritage','ai-assistant','reports','notifications','profile','admin','workspace'];
    const normalized = String(raw || '').split(/[?#]/)[0];
    const file = normalized.split('/').pop();
    return allowed.some(name => name + '.html' === file) ? file : 'dashboard.html';
  }
  function landingPage(){const current=getSession();if(!current)return 'login.html';const data=readJSON('familyconnect.family-demo.v1',null);const joined=Object.values(data?.families||{}).some(f=>f.memberships?.[current.id]?.status==='active'||current.id==='demo'&&['le','nguyen'].includes(f.id)&&!f.memberships?.demo);return joined||current.id==='demo'&&!data?'dashboard.html':'workspace.html';}
  function requireSession() {
    const pathname = location.pathname.split('/').pop();
    if (['login.html','register.html','index.html',''].includes(pathname)) return;
    if (!getSession()) {
      location.replace('login.html?next=' + encodeURIComponent(targetPage(pathname)));
    }
  }
  requireSession();
  window.FamilyDemoAuth = Object.freeze({ getSession, landingPage, login, register, signOut, getTheme, setTheme, targetPage, DEMO_EMAIL, DEMO_PASSWORD });
}());
