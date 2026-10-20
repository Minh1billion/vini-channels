import type { User } from '@/entities/user/types';
import { http } from './http';

export const authApi = {
  login: (email: string, password: string) => http.post<User>('/auth/login', { email, password }),
  logout: () => http.post<void>('/auth/logout'),
  me: () => http.get<User>('/me'),
  changePassword: (current_password: string, new_password: string) =>
    http.post<void>('/me/password', { current_password, new_password }),
};
