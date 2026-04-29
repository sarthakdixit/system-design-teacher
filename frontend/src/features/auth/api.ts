import { apiClient } from "@/shared/api/client";
import { LoginResponseSchema, UserSchema } from "@/features/auth/schema";
import type { LoginResponse, User } from "@/features/auth/types";

export async function exchangeMicrosoftToken(microsoftToken: string): Promise<LoginResponse> {
  const { data } = await apiClient.post("/api/v1/auth/microsoft/callback", {
    microsoft_token: microsoftToken,
  });
  return LoginResponseSchema.parse(data);
}

export async function fetchCurrentUser(): Promise<User> {
  const { data } = await apiClient.get("/api/v1/auth/me");
  return UserSchema.parse(data);
}
