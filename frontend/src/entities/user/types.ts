export type Role = 'admin' | 'manager' | 'analyst' | 'viewer';

export interface User {
  id: string;
  email: string;
  role: Role;
  is_active: boolean;
}
