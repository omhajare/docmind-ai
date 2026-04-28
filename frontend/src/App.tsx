import { lazy, Suspense, useEffect } from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Toaster } from "@/components/ui/sonner";

import { AuthProvider, useAuth } from "@/auth/AuthContext";
import { setAuthInterceptors } from "@/api/client";
import ProtectedRoute from "@/components/shared/ProtectedRoute";
import { Skeleton } from "@/components/ui/skeleton";

import LoginPage from "@/components/auth/LoginPage";
import SignupPage from "@/components/auth/SignupPage";
import ForgotPasswordPage from "@/components/auth/ForgotPasswordPage";
import ResetPasswordPage from "@/components/auth/ResetPasswordPage";
import DashboardPage from "@/components/dashboard/DashboardPage";
import LandingPage from "@/components/landing/LandingPage";

// Lazy-loaded pages
const ResearchPage = lazy(() => import("@/components/research/ResearchPage"));
const AdminPage = lazy(() => import("@/components/admin/AdminPage"));

function LazyFallback() {
  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="space-y-4 w-80">
        <Skeleton className="h-8 w-48 mx-auto" />
        <Skeleton className="h-4 w-64 mx-auto" />
        <Skeleton className="h-32 w-full rounded-xl" />
      </div>
    </div>
  );
}

function AppRoutes() {
  const { accessToken, refresh, logout } = useAuth();

  useEffect(() => {
    setAuthInterceptors(
      () => accessToken,
      refresh,
      () => { logout(); }
    );
  }, [accessToken, refresh, logout]);

  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/forgot-password" element={<ForgotPasswordPage />} />
      <Route path="/reset-password" element={<ResetPasswordPage />} />
      <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
      <Route path="/research" element={<ProtectedRoute><Suspense fallback={<LazyFallback />}><ResearchPage /></Suspense></ProtectedRoute>} />
      <Route path="/admin" element={<Suspense fallback={<LazyFallback />}><AdminPage /></Suspense>} />
    </Routes>
  );
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
        <Toaster />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
