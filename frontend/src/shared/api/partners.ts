import type { Partner } from '@/entities/partner/types';
import { http } from './http';

export type PartnerListParams = { q?: string; include_archived?: boolean; tag?: string };

export type PartnerInput = {
  name: string;
  industry: string | null;
  tags: string[];
  notes: string;
};

export const partnersApi = {
  list: (params: PartnerListParams = {}) => http.get<Partner[]>('/partners', params),
  create: (body: PartnerInput) => http.post<Partner>('/partners', body),
  update: (id: string, body: Partial<PartnerInput>) => http.patch<Partner>(`/partners/${id}`, body),
  archive: (id: string) => http.delete<Partner>(`/partners/${id}`),
  restore: (id: string) => http.post<Partner>(`/partners/${id}/restore`),
};
