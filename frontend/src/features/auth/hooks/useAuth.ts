import { useMutation } from "@tanstack/react-query";
import { useMsal } from "@azure/msal-react";
import { env } from "@/config/env";
import { msalLoginRequest } from "@/config/msal";
import { exchangeMicrosoftToken } from "@/features/auth/api";
import { useAuthStore } from "@/features/auth/store";
import type { LoginResponse } from "@/features/auth/types";

const MOCK_MICROSOFT_TOKEN = "mock-token-for-dev-only";

type UseAuthResult = {
  isAuthenticated: boolean;
  isLoggingIn: boolean;
  loginError: Error | null;
  login: () => Promise<void>;
  logout: () => void;
};

export function useAuth(): UseAuthResult {
  const accessToken = useAuthStore((s) => s.accessToken);
  const setSession = useAuthStore((s) => s.setSession);
  const clearSession = useAuthStore((s) => s.clearSession);

  const msalEnabled = env.VITE_AUTH_MODE === "msal";
  const msal = msalEnabled ? useMsalSafe() : null;

  const loginMutation = useMutation<LoginResponse>({
    mutationFn: async () => {
      const microsoftToken = msalEnabled
        ? await acquireMicrosoftToken(msal!)
        : MOCK_MICROSOFT_TOKEN;
      return exchangeMicrosoftToken(microsoftToken);
    },
    onSuccess: (response) => {
      setSession(response.accessToken, response.user);
    },
  });

  const logout = () => {
    clearSession();
    if (msalEnabled && msal) {
      void msal.instance.logoutPopup().catch(() => {
        /* swallowed: even if MSAL logout fails, our local session is already cleared */
      });
    }
  };

  return {
    isAuthenticated: accessToken !== null,
    isLoggingIn: loginMutation.isPending,
    loginError: loginMutation.error,
    login: async () => {
      await loginMutation.mutateAsync();
    },
    logout,
  };
}

function useMsalSafe() {
  return useMsal();
}

async function acquireMicrosoftToken(msal: ReturnType<typeof useMsal>): Promise<string> {
  const result = await msal.instance.loginPopup(msalLoginRequest);
  return result.idToken;
}
