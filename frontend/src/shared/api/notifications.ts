import type { NotificationList, NotificationRecord } from '@/entities/notification/types';
import { http } from './http';

export const notificationsApi = {
  list: (limit = 20) => http.get<NotificationList>('/notifications', { limit }),
  markRead: (id: string) => http.post<NotificationRecord>(`/notifications/${id}/read`),
  markAllRead: () => http.post<{ updated: number }>('/notifications/read-all'),
};
