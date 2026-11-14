import { useCallback, useState } from "react";
import { Outlet } from "react-router-dom";
import { Navbar } from "./Navbar";
import { Sidebar } from "./Sidebar";
import { useAuth } from "@/features/auth/hooks/useAuth";

export function AppLayout() {
  const { user } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const closeSidebar = useCallback(() => setSidebarOpen(false), []);

  return <div className="app-shell">
    <a className="skip-link" href="#main-content">Đến nội dung chính</a>
    <Sidebar role={user?.role ?? "guest"} open={sidebarOpen} onClose={closeSidebar} />
    <div className="app-workspace"><Navbar sidebarOpen={sidebarOpen} onMenuClick={() => setSidebarOpen(true)} /><main id="main-content" className="app-content" tabIndex={-1}><Outlet /></main></div>
  </div>;
}
