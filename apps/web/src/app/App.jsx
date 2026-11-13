import { lazy, Suspense } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "@/shared/layouts/AppLayout";
import { AuthProvider } from "@/features/auth/hooks/useAuth";
import { Login } from "@/features/auth/pages/Login";
import { Register } from "@/features/auth/pages/Register";
import { ProtectedRoute } from "@/features/auth/components/ProtectedRoute";
import { AdminConfig } from "@/features/admin-config/pages/AdminConfig";
import { MemberApproval } from "@/features/member-approval/pages/MemberApproval";
import { Reports } from "@/features/reports/pages/Reports";

const Dashboard = lazy(() => import("@/features/dashboard/pages/Dashboard").then((module) => ({ default: module.Dashboard })));
const Heritage = lazy(() => import("@/features/heritage/pages/Heritage").then((module) => ({ default: module.Heritage })));
const FamilyTree = lazy(() => import("@/features/family-tree/pages/FamilyTree").then((module) => ({ default: module.FamilyTree })));
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
                <Route path="/dashboard" element={<Suspense fallback={<p role="status">Đang tải tổng quan…</p>}><Dashboard /></Suspense>} />
                <Route element={<ProtectedRoute allowedRoles={["admin", "family_head", "member"]} />}>
                  <Route path="/heritage" element={<Suspense fallback={<p role="status">Đang tải di sản…</p>}><Heritage /></Suspense>} />
                  <Route path="/family-tree" element={<Suspense fallback={<p role="status">Đang tải gia phả…</p>}><FamilyTree /></Suspense>} />
                </Route>
                <Route element={<ProtectedRoute allowedRoles={["admin"]} />}>
                  <Route path="/admin-config" element={<AdminConfig />} />
                  <Route path="/reports" element={<Reports />} />
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
