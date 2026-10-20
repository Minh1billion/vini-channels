import type { AuditEntry, AuditQuery } from '@/entities/audit/types';
import { http } from './http';

export const auditApi = {
  list: (query: AuditQuery) => http.get<AuditEntry[]>('/audit', query),
};
