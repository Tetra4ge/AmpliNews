import axios from 'axios';
import { supabase } from './supabase';

const API_BASE_URL =
  import.meta.env.VITE_MODE === 'production'
    ? import.meta.env.VITE_API_PRO_URL
    : import.meta.env.VITE_API_DEV_URL || 'http://127.0.0.1:8000';

export const api = axios.create({
  baseURL: API_BASE_URL,
});

// Attach the current Supabase access_token to every request as a Bearer token,
// so the FastAPI backend can validate it via `get_current_user`.
api.interceptors.request.use(async (config) => {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export interface UserProfileResponse {
  user_id: string;
  baseline_political_leaning: number;
  total_articles_read: number;
  most_read_topic: string | null;
}

export interface UserSyncRequest {
  selected_topics: string[];
  baseline_leaning: number;
}

export function fetchUserProfile() {
  return api.get<UserProfileResponse>('/api/user/profile');
}

export function syncUser(payload: UserSyncRequest) {
  return api.post('/api/auth/sync', payload);
}

export interface Article {
  article_id: string;
  title: string;
  source: string;
  url: string;
  published_date: string;
  match_percentage: number;
  bias: string;
  bias_score: number;
  credibility: number;
  reasoning: string;
}

export interface FeedResponse {
  feed: Article[];
}

export function fetchFeed() {
  return api.get<FeedResponse>('/api/articles/feed');
}

export function fetchArticleById(id: string) {
  return api.get(`/api/articles/${id}`);
}

export interface ReadPayload {
  article_id: string;
  read_duration_seconds: number;
  liked?: boolean;
  rejected_biased?: boolean;
}

export function logArticleRead(payload: ReadPayload) {
  return api.post('/api/articles/read', payload);
}

export interface OpposingViewResponse {
  article_id: string;
  title: string;
  bias: string;
  bias_score: number;
  credibility: number;
  similarity: number;
}

export function fetchOpposingView(articleId: string) {
  return api.post<OpposingViewResponse>('/api/agent/opposing-view', { article_id: articleId });
}

