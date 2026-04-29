import { Configuration, LogLevel, PublicClientApplication } from "@azure/msal-browser";
import { env } from "@/config/env";

const msalConfig: Configuration = {
  auth: {
    clientId: env.VITE_MICROSOFT_CLIENT_ID,
    authority: `https://login.microsoftonline.com/${env.VITE_MICROSOFT_TENANT_ID}`,
    redirectUri: window.location.origin,
  },
  cache: {
    cacheLocation: "sessionStorage",
    storeAuthStateInCookie: false,
  },
  system: {
    loggerOptions: {
      loggerCallback: (level, message) => {
        if (level === LogLevel.Error) {
          console.error("[MSAL]", message);
        }
      },
      logLevel: LogLevel.Warning,
    },
  },
};

export const msalInstance = new PublicClientApplication(msalConfig);

export const msalLoginRequest = {
  scopes: ["openid", "profile", "email"],
};
