import axios from 'axios';
import { useAuth } from '../store/auth';

export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8080/api';
export const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8080/ws';

export const api = axios.create({ baseURL: API_URL });

api.interceptors.request.use((cfg) => {
  const token = useAuth.getState().token;
  if (token) cfg.headers.Authorization = `Bearer ${token}`;
  return cfg;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err?.response?.status === 401) useAuth.getState().logout();
    return Promise.reject(err);
  }
);

export const auth = {
  login: (email, password) => api.post('/auth/login', { email, password }).then((r) => r.data),
  register: (payload) => api.post('/auth/register', payload).then((r) => r.data),
};

export const interviews = {
  create: (role, level) => api.post('/interviews', { role, level }).then((r) => r.data),
  list: () => api.get('/interviews').then((r) => r.data),
  get: (id) => api.get(`/interviews/${id}`).then((r) => r.data),
  answer: (id, payload) => api.post(`/interviews/${id}/answers`, payload).then((r) => r.data),
  complete: (id) => api.post(`/interviews/${id}/complete`).then((r) => r.data),
};

export const analytics = {
  dashboard: () => api.get('/analytics/dashboard').then((r) => r.data),
};
