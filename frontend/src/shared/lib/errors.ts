import { ApiError } from '@/shared/api/http';

export const errorMessage = (error: unknown, fallback = 'Có lỗi xảy ra, vui lòng thử lại') =>
  error instanceof ApiError ? error.message : fallback;
