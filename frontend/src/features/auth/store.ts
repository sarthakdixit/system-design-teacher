import { create } from "zustand";
import type { User } from "@/features/auth/types";

type AuthState = {
  accessToken: string | null;
  user: User | null;
  setSession: (accessToken: string, user: User) => void;
  setUser: (user: User) => void;
  clearSession: () => void;
};

export const useAuthStore = create<AuthState>((set) => ({
  accessToken: null,
  user: null,
  setSession: (accessToken, user) => set({ accessToken, user }),
  setUser: (user) => set({ user }),
  clearSession: () => set({ accessToken: null, user: null }),
}));
