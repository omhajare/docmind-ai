import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  type ReactNode,
} from "react";
import { authApi, type User } from "@/api/auth.api";

interface AuthContextType {
  accessToken: string | null;
  user: User | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  refresh: () => Promise<string | null>;
  setAccessToken: (token: string | null) => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const refresh = useCallback(async (): Promise<string | null> => {
    try {
      const { data } = await authApi.refresh();
      setAccessToken(data.access_token);
      return data.access_token;
    } catch {
      setAccessToken(null);
      setUser(null);
      return null;
    }
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const { data } = await authApi.login({ email, password });
    setAccessToken(data.access_token);
    setUser(data.user);
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi.logout();
    } catch {
      // Ignore errors on logout
    }
    setAccessToken(null);
    setUser(null);
  }, []);

  // Silent refresh on mount to restore session
  useEffect(() => {
    const tryRefresh = async () => {
      const token = await refresh();
      if (token) {
        // We have a token but need user info — decode from JWT
        try {
          const payload = JSON.parse(atob(token.split(".")[1]));
          setUser({ id: payload.user_id, email: payload.email, full_name: "" });
        } catch {
          // If decode fails, we'll get user info on next login
        }
      }
      setIsLoading(false);
    };
    tryRefresh();
  }, [refresh]);

  return (
    <AuthContext.Provider
      value={{ accessToken, user, isLoading, login, logout, refresh, setAccessToken }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
