import type {
  NotificationList,
  NotificationRecord,
  PushConfig,
  PushSubscriptionInput,
} from '@/entities/notification/types';
import { http } from './http';

export const notificationsApi = {
  list: (limit = 20) => http.get<NotificationList>('/notifications', { limit }),
  markRead: (id: string) => http.post<NotificationRecord>(`/notifications/${id}/read`),
  markAllRead: () => http.post<{ updated: number }>('/notifications/read-all'),
  pushConfig: () => http.get<PushConfig>('/notifications/push/config'),
  pushSubscribe: (input: PushSubscriptionInput) =>
    http.post<void>('/notifications/push/subscribe', input),
  pushUnsubscribe: (endpoint: string) =>
    http.post<void>('/notifications/push/unsubscribe', { endpoint }),
};
