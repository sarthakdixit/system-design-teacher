export type User = {
  id: string;
  microsoftOid: string;
  email: string;
  displayName: string;
  createdAt: string;
  lastLoginAt: string;
};

export type LoginResponse = {
  accessToken: string;
  tokenType: string;
  expiresInSeconds: number;
  user: User;
};
