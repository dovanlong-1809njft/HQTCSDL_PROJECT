import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { login as loginRequest, register as registerRequest } from "../services/auth";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem("familyconnect.user");
    return saved ? JSON.parse(saved) : null;
  });
  const [isLoading, setIsLoading] = useState(false);

  const signOut = useCallback(() => {
    localStorage.removeItem("familyconnect.token");
    localStorage.removeItem("familyconnect.user");
    setUser(null);
  }, []);

  useEffect(() => {
    window.addEventListener("familyconnect:unauthorized", signOut);
    return () => window.removeEventListener("familyconnect:unauthorized", signOut);
  }, [signOut]);

  const signIn = useCallback(async (payload) => {
    setIsLoading(true);
    try {
      const session = await loginRequest(payload);
      localStorage.setItem("familyconnect.token", session.accessToken);
      localStorage.setItem("familyconnect.user", JSON.stringify(session.user));
      setUser(session.user);
    } finally {
      setIsLoading(false);
    }
  }, []);

  const signUp = useCallback(async (payload) => {
    setIsLoading(true);
    try {
      const session = await registerRequest(payload);
      localStorage.setItem("familyconnect.token", session.accessToken);
      localStorage.setItem("familyconnect.user", JSON.stringify(session.user));
      setUser(session.user);
    } finally {
      setIsLoading(false);
    }
  }, []);

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
