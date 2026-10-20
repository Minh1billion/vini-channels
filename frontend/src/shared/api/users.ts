import type { Role, User } from '@/entities/user/types';
import { http } from './http';

export type UserCreateInput = { email: string; password: string; role: Role };
export type UserUpdateInput = { role?: Role; is_active?: boolean; password?: string };

export const usersApi = {
  list: () => http.get<User[]>('/users'),
  create: (body: UserCreateInput) => http.post<User>('/users', body),
  update: (id: string, body: UserUpdateInput) => http.patch<User>(`/users/${id}`, body),
};
