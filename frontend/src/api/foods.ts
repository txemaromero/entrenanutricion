import { api } from './client';
import type { Food, FoodCategory, FoodInput, Paginated } from './types';

export interface FoodListParams {
  search?: string;
  category?: FoodCategory | '';
  ordering?: string;
  limit?: number;
  offset?: number;
}

const clean = (params: object) =>
  Object.fromEntries(
    Object.entries(params).filter(([, value]) => value !== undefined && value !== ''),
  );

/** Food library (values per 100 g): everyone signed in reads it, nutritionists and admins edit. */
export const foodsApi = {
  list: (params: FoodListParams = {}) =>
    api
      .get<Paginated<Food>>('/foods', { params: clean({ limit: 100, ...params }) })
      .then((r) => r.data),
  get: (id: number) => api.get<Food>(`/foods/${id}`).then((r) => r.data),
  create: (input: FoodInput) => api.post<Food>('/foods', input).then((r) => r.data),
  update: (id: number, input: FoodInput) =>
    api.put<Food>(`/foods/${id}`, input).then((r) => r.data),
  remove: (id: number) => api.delete(`/foods/${id}`),
};
