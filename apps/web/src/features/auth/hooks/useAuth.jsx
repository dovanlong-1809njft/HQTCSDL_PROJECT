import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { login as loginRequest, register as registerRequest } from "../api/authApi";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const queryClient = useQueryClient();
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem("familyconnect.user");
    return saved ? JSON.parse(saved) : null;
  });
  const [isLoading, setIsLoading] = useState(false);

  const signOut = useCallback(() => {
    localStorage.removeItem("familyconnect.token");
    localStorage.removeItem("familyconnect.user");
    queryClient.clear();
    setUser(null);
  }, [queryClient]);

  useEffect(() => {
    function syncSession(event) {
      if (event.storageArea !== localStorage || ![null, "familyconnect.token", "familyconnect.user"].includes(event.key)) return;
      const saved = localStorage.getItem("familyconnect.user");
      queryClient.clear();
      setUser(localStorage.getItem("familyconnect.token") && saved ? JSON.parse(saved) : null);
    }

    window.addEventListener("familyconnect:unauthorized", signOut);
    window.addEventListener("storage", syncSession);
    return () => {
      window.removeEventListener("familyconnect:unauthorized", signOut);
      window.removeEventListener("storage", syncSession);
    };
  }, [queryClient, signOut]);

  const signIn = useCallback(async (payload) => {
    setIsLoading(true);
    try {
      const session = await loginRequest(payload);
      queryClient.clear();
      localStorage.setItem("familyconnect.token", session.accessToken);
      localStorage.setItem("familyconnect.user", JSON.stringify(session.user));
      setUser(session.user);
    } finally {
      setIsLoading(false);
    }
  }, [queryClient]);

  const signUp = useCallback(async (payload) => {
    setIsLoading(true);
    try {
      const session = await registerRequest(payload);
      queryClient.clear();
      localStorage.setItem("familyconnect.token", session.accessToken);
      localStorage.setItem("familyconnect.user", JSON.stringify(session.user));
      setUser(session.user);
    } finally {
      setIsLoading(false);
    }
  }, [queryClient]);

  const value = useMemo(() => ({
    user,
    isAuthenticated: Boolean(user && localStorage.getItem("familyconnect.token")),
    isLoading,
    signIn,
    signUp,
    signOut,
  }), [user, isLoading, signIn, signUp, signOut]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth cần được dùng bên trong AuthProvider.");
  return context;
}
