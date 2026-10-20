import type { Role } from './types';

export const roleLabels: Record<Role, string> = {
  admin: 'Quản trị viên',
  manager: 'Quản lý đối tác',
  analyst: 'Chuyên viên phân tích',
  viewer: 'Người xem',
};

export type Ability =
  | 'partners:write'
  | 'sync:read'
  | 'sync:write'
  | 'providers:write'
  | 'users:write'
  | 'scoring:read'
  | 'scoring:write'
  | 'audit:read';

const abilities: Record<Role, ReadonlySet<Ability>> = {
  admin: new Set<Ability>([
    'partners:write',
    'sync:read',
    'sync:write',
    'providers:write',
    'users:write',
    'scoring:read',
    'scoring:write',
    'audit:read',
  ]),
  manager: new Set<Ability>(['partners:write', 'sync:read', 'sync:write', 'scoring:read']),
  analyst: new Set<Ability>(['sync:read', 'scoring:read', 'scoring:write']),
  viewer: new Set<Ability>(),
};

export const roleCan = (role: Role, ability: Ability) => abilities[role].has(ability);

export const displayName = (email: string) => email.split('@')[0] ?? email;
