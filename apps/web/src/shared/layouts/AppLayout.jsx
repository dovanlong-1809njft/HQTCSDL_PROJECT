import { useCallback, useState } from "react";
import { Outlet } from "react-router-dom";
import { Navbar } from "./Navbar";
import { Sidebar } from "./Sidebar";
import { useAuth } from "@/features/auth/hooks/useAuth";

function validateRequiredFields(event) {
  const form = event.target;
  if (form.noValidate) return;
  for (const field of form.elements) {
    if (!field.required || !field.willValidate || ["checkbox", "radio", "file"].includes(field.type)) continue;
    const value = field.value.trim();
    field.setCustomValidity(!value ? "Vui lòng nhập đầy đủ thông tin bắt buộc."
      : field.minLength > 0 && value.length < field.minLength ? `Cần nhập ít nhất ${field.minLength} ký tự, không tính khoảng trắng ở đầu và cuối.` : "");
  }
  if (!form.reportValidity()) {
    event.preventDefault();
    event.stopPropagation();
  }
}

export function AppLayout() {
  const { user } = useAuth();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const closeSidebar = useCallback(() => setSidebarOpen(false), []);

  return <div className="app-shell" onSubmitCapture={validateRequiredFields} onInputCapture={(event) => {
    for (const field of event.target.form?.elements || []) field.setCustomValidity?.("");
  }}>
    <a className="skip-link" href="#main-content">Đến nội dung chính</a>
    <Sidebar role={user?.role ?? "guest"} open={sidebarOpen} onClose={closeSidebar} />
    <div className="app-workspace"><Navbar sidebarOpen={sidebarOpen} onMenuClick={() => setSidebarOpen(true)} /><main id="main-content" className="app-content" tabIndex={-1}><Outlet /></main></div>
  </div>;
}
