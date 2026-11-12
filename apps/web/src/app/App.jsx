import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "@/shared/layouts/AppLayout";
import { AuthProvider } from "@/features/auth/hooks/useAuth";
import { Dashboard } from "@/features/dashboard/pages/Dashboard";
import { Login } from "@/features/auth/pages/Login";
import { Register } from "@/features/auth/pages/Register";
import { ProtectedRoute } from "@/features/auth/components/ProtectedRoute";
import { AdminConfig } from "@/features/admin-config/pages/AdminConfig";
import { MemberApproval } from "@/features/member-approval/pages/MemberApproval";

const queryClient = new QueryClient({ defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } } });

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route element={<ProtectedRoute />}>
              <Route element={<AppLayout />}>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route element={<ProtectedRoute allowedRoles={["admin"]} />}>
                  <Route path="/admin-config" element={<AdminConfig />} />
                </Route>
                <Route element={<ProtectedRoute allowedRoles={["admin", "family_head"]} />}>
                  <Route path="/member-approval" element={<MemberApproval />} />
                </Route>
              </Route>
            </Route>
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </QueryClientProvider>
  );
}
