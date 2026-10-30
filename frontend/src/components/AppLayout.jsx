import { useState } from "react";
import { Outlet } from "react-router-dom";
import { Navbar } from "./Navbar";
import { Sidebar } from "./Sidebar";
import { useAuth } from "../hooks/useAuth";

export function AppLayout() {
  const { user } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return <div className="min-h-screen bg-sand lg:flex"><Sidebar role={user?.role ?? "guest"} open={sidebarOpen} onClose={() => setSidebarOpen(false)} /><div className="min-w-0 flex-1"><Navbar onMenuClick={() => setSidebarOpen(true)} /><main className="mx-auto w-full max-w-[1440px] p-4 sm:p-7 lg:p-9"><Outlet /></main></div></div>;
}
