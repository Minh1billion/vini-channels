import type { Scoreboard, ScoreWeights } from '@/entities/scoring/types';
import { periodQuery, type Period } from '@/shared/lib/period';
import { http } from './http';

export const scoringApi = {
  scoreboard: (period: Period) => http.get<Scoreboard>('/scoring', periodQuery(period)),
  weights: () => http.get<ScoreWeights>('/scoring/weights'),
  updateWeights: (body: ScoreWeights) => http.put<ScoreWeights>('/scoring/weights', body),
};
