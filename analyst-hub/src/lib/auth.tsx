import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";

export type UserRole =
  | "ADMIN"
  | "FRAUD_ANALYST"
  | "INVESTIGATOR"
  | "PROVIDER_REVIEWER"
  | "EXECUTIVE";

export const ROLE_LABELS: Record<UserRole, string> = {
  ADMIN: "Administrator",
  FRAUD_ANALYST: "Fraud Analyst",
  INVESTIGATOR: "Investigator",
  PROVIDER_REVIEWER: "Provider Reviewer",
  EXECUTIVE: "Executive / Management",
};

export interface AuthUser {
  name: string;
  email: string;
  title: string;
  role: UserRole;
  department: string;
  account_status: "Active" | "Suspended";
  employee_id: string;
  last_login: string;
}

const STORAGE_KEY = "fraudguard.auth.user";

/**
 * Mocked authentication state. The prototype has no backend auth yet, so the
 * session lives in localStorage. Replace `login`/`logout` with the real auth
 * endpoints later — the rest of the app only depends on `useAuth()`.
 */
export const DEMO_USER: AuthUser = {
  name: "Analyst",
  email: "analyst@fraudguard.ai",
  title: "Payment Integrity Analyst",
  role: "ADMIN",
  department: "Payment Integrity — Special Investigations Unit",
  account_status: "Active",
  employee_id: "FG-A-1042",
  last_login: "Today",
};

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  login: (email?: string) => AuthUser;
  logout: () => void;
  setRole: (role: UserRole) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function readStored(): AuthUser | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as AuthUser) : null;
  } catch {
    return null;
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);

  // Read after mount so SSR and hydration agree.
  useEffect(() => {
    setUser(readStored() ?? DEMO_USER);
  }, []);

  const persist = useCallback((next: AuthUser | null) => {
    setUser(next);
    if (typeof window === "undefined") return;
    if (next) window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    else window.localStorage.removeItem(STORAGE_KEY);
  }, []);

  const login = useCallback(
    (email?: string) => {
      const next: AuthUser = { ...DEMO_USER, email: email?.trim() || DEMO_USER.email };
      persist(next);
      return next;
    },
    [persist],
  );

  const logout = useCallback(() => persist(null), [persist]);

  const setRole = useCallback(
    (role: UserRole) => persist({ ...(user ?? DEMO_USER), role }),
    [persist, user],
  );

  const value = useMemo<AuthContextValue>(
    () => ({ user, isAuthenticated: !!user, login, logout, setRole }),
    [user, login, logout, setRole],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
