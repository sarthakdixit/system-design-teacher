import { z } from "zod";

const EnvSchema = z.object({
  VITE_API_BASE_URL: z.string().url(),
  VITE_AUTH_MODE: z.enum(["msal", "mock"]).default("mock"),
  VITE_MICROSOFT_CLIENT_ID: z.string().min(1),
  VITE_MICROSOFT_TENANT_ID: z.string().min(1),
});

export const env = EnvSchema.parse({
  VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL,
  VITE_AUTH_MODE: import.meta.env.VITE_AUTH_MODE,
  VITE_MICROSOFT_CLIENT_ID: import.meta.env.VITE_MICROSOFT_CLIENT_ID,
  VITE_MICROSOFT_TENANT_ID: import.meta.env.VITE_MICROSOFT_TENANT_ID,
});

export type Env = typeof env;
