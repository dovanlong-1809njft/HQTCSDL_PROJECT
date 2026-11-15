import assert from "node:assert/strict";
import { after, test } from "node:test";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";
import { mkdirSync, writeFileSync } from "node:fs";
import { createServer } from "../../apps/web/node_modules/vite/dist/node/index.js";

const web = fileURLToPath(new URL("../../apps/web/", import.meta.url));
const require = createRequire(new URL("../../apps/web/package.json", import.meta.url));
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");
const { StaticRouter } = require("react-router-dom/server");
const { QueryClient, QueryClientProvider } = await import("../../apps/web/node_modules/@tanstack/react-query/build/modern/index.js");
const server = await createServer({ root: web, server: { middlewareMode: true }, appType: "custom" });
after(() => server.close());
const { AuthProvider } = await server.ssrLoadModule("/src/features/auth/hooks/useAuth.jsx");
const { Sidebar } = await server.ssrLoadModule("/src/shared/layouts/Sidebar.jsx");
const { Dashboard } = await server.ssrLoadModule("/src/features/dashboard/pages/Dashboard.jsx");
const { Navbar } = await server.ssrLoadModule("/src/shared/layouts/Navbar.jsx");
const { Login } = await server.ssrLoadModule("/src/features/auth/pages/Login.jsx");
const { Register } = await server.ssrLoadModule("/src/features/auth/pages/Register.jsx");

function render(component, role = "member", rows) {
  const user = { id: "ui-test", fullName: "Thành viên kiểm thử", role };
  globalThis.localStorage = { getItem: (key) => role === null ? null : key === "familyconnect.user" ? JSON.stringify(user) : "ui-test-token" };
  const cache = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  if (rows) cache.setQueryData(["dashboard-statistics", user.id, role], rows);
  const markup = renderToStaticMarkup(React.createElement(QueryClientProvider, { client: cache },
    React.createElement(AuthProvider, null, React.createElement(StaticRouter, { location: "/dashboard" }, component))));
  cache.clear();
  return markup;
}

test("navigation keeps restricted pages out of guest and member menus", () => {
  const guest = render(React.createElement(Sidebar, { role: "guest", open: false }), "guest");
  assert.match(guest, /href="\/dashboard"/);
  assert.doesNotMatch(guest, /href="\/(family-tree|heritage|admin-config|member-approval|reports)"/);
  const member = render(React.createElement(Sidebar, { role: "member", open: false }));
  assert.match(member, /href="\/family-tree"/);
  assert.match(member, /href="\/heritage"/);
  assert.doesNotMatch(member, /href="\/(admin-config|member-approval|family-management|reports)"/);
  assert.match(member, /href="\/profile"/);
  const head = render(React.createElement(Sidebar, { role: "family_head", open: false }), "family_head");
  assert.match(head, /href="\/member-approval"/);
  assert.match(head, /href="\/family-management"/);
  assert.doesNotMatch(head, /href="\/(admin-config|reports)"/);
  const admin = render(React.createElement(Sidebar, { role: "admin", open: false }), "admin");
  for (const path of ["admin-config", "member-approval", "reports"]) assert.ok(admin.includes(`href="/${path}"`));
});

test("member overview has working destinations without fabricated statistics", () => {
  const markup = render(React.createElement(Dashboard));
  assert.match(markup, /<h1>Không gian gia đình<\/h1>/);
  assert.match(markup, /href="\/family-tree"/);
  assert.match(markup, /href="\/heritage"/);
  assert.doesNotMatch(markup, /class="stat-grid"|Thống kê theo gia đình/);
  const guest = render(React.createElement(Dashboard), "guest");
  assert.doesNotMatch(guest, /href="\/(family-tree|heritage)"/);
  assert.match(guest, /xác minh/);
});

test("admin statistics retain totals and an accessible data table", () => {
  const rows = [{ family_id: "1", family_name: "Gia đình kiểm thử", member_count: 1234, post_count: 5, event_count: 2 }];
  const markup = render(React.createElement(Dashboard), "admin", rows);
  assert.match(markup, /1\.234/);
  assert.match(markup, /Số liệu hoạt động theo gia đình/);
  assert.match(markup, /scope="row"[^>]*>Gia đình kiểm thử/);
  assert.match(render(React.createElement(Dashboard), "admin", []), /Chưa có gia đình trong phạm vi thống kê/);
});

test("auth forms retain their labels, autocomplete and real submit controls", () => {
  const login = render(React.createElement(Login), null);
  for (const label of ["Email", "Mật khẩu"]) assert.ok(login.includes(`>${label}</label>`));
  assert.match(login, /autoComplete="current-password"/i);
  assert.match(login, /type="submit"/);
  assert.doesNotMatch(login, /demo@familyconnect|Family123|Quên mật khẩu/);
  const register = render(React.createElement(Register), null);
  assert.match(register, /Họ và tên/);
  assert.match(register, /Nhập lại mật khẩu/);
  assert.match(register, /autoComplete="new-password"/i);
});

test("mobile menu declares its state and account has a named sign-out action", () => {
  const markup = render(React.createElement(Navbar, { sidebarOpen: true }));
  assert.match(markup, /aria-controls="app-sidebar" aria-expanded="true"/);
  assert.match(markup, /aria-label="Đăng xuất"/);
});

// Static, local visual fixture only; never included in the production build.
if (process.argv.includes("--preview")) {
  const body = render(React.createElement("div", { className: "app-shell" },
    React.createElement(Sidebar, { role: "member", open: false }),
    React.createElement("div", { className: "app-workspace" }, React.createElement(Navbar, { sidebarOpen: false }),
      React.createElement("main", { className: "app-content" }, React.createElement(Dashboard)))));
  mkdirSync(`${web}/.taste-skill/preview`, { recursive: true });
  writeFileSync(`${web}/.taste-skill/preview/dashboard.html`, `<!doctype html><html lang="vi" data-motion><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>FamilyConnect — Kiểm tra giao diện</title><link rel="stylesheet" href="/src/styles/index.css"><link rel="stylesheet" href="/assets/motion/motion.css"><body>${body}</body></html>`);
}
