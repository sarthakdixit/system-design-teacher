import { z } from "zod";

export const UserSchema = z
  .object({
    id: z.string(),
    microsoft_oid: z.string(),
    email: z.string().email(),
    display_name: z.string(),
    created_at: z.string(),
    last_login_at: z.string(),
  })
  .transform((u) => ({
    id: u.id,
    microsoftOid: u.microsoft_oid,
    email: u.email,
    displayName: u.display_name,
    createdAt: u.created_at,
    lastLoginAt: u.last_login_at,
  }));

export const LoginResponseSchema = z
  .object({
    access_token: z.string(),
    token_type: z.string(),
    expires_in_seconds: z.number().int().positive(),
    user: UserSchema,
  })
  .transform((r) => ({
    accessToken: r.access_token,
    tokenType: r.token_type,
    expiresInSeconds: r.expires_in_seconds,
    user: r.user,
  }));
