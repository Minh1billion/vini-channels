import type { SearchResults } from '@/entities/search/types';
import { http } from './http';

export const searchApi = {
  query: (q: string, limit = 5) => http.get<SearchResults>('/search', { q, limit }),
};
