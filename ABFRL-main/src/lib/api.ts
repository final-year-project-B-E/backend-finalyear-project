import { Product, User } from '@/types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export interface ApiOrder {
  id: number;
  order_number: string;
  final_amount: number;
  order_status: string;
  created_at: string;
  items: Array<{ id: number; product_name: string; quantity: number; total_price: number }>;
}

async function request<T>(path: string, options: RequestInit = {}, token?: string): Promise<T> {
  const headers: HeadersInit = { 'Content-Type': 'application/json', ...(options.headers || {}) };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `Request failed: ${res.status}`);
  }
  return res.json();
}

export const api = {
  signup: (payload: { email: string; password: string; first_name: string; last_name: string }) =>
    request<{ user: User; token: string }>('/auth/signup', { method: 'POST', body: JSON.stringify(payload) }),

  login: (payload: { email: string; password: string }) =>
    request<{ user: User; token: string }>('/auth/login', { method: 'POST', body: JSON.stringify(payload) }),

  me: (token: string) => request<{ user: User }>('/auth/me', {}, token),

  logout: (token: string) => request<{ message: string }>('/auth/logout', { method: 'POST' }, token),

  products: (params?: { category?: string; occasion?: string; min_price?: number; max_price?: number }) => {
    const search = new URLSearchParams();
    if (params?.category) search.set('category', params.category);
    if (params?.occasion) search.set('occasion', params.occasion);
    if (params?.min_price !== undefined) search.set('min_price', String(params.min_price));
    if (params?.max_price !== undefined) search.set('max_price', String(params.max_price));
    return request<{ products: Product[] }>(`/products${search.toString() ? `?${search.toString()}` : ''}`);
  },

  getCart: (userId: number) => request<{ cart_items: any[] }>(`/user/${userId}/cart`),

  addToCart: (userId: number, productId: number, quantity: number) =>
    request(`/user/${userId}/cart/add/${productId}?quantity=${quantity}`, { method: 'POST' }),

  checkout: (userId: number, payload: { shipping_address: string; billing_address: string; payment_method: string }) =>
    request<{ order: ApiOrder }>(`/user/${userId}/checkout`, { method: 'POST', body: JSON.stringify(payload) }),

  orders: (userId: number) => request<{ orders: ApiOrder[] }>(`/user/${userId}/orders`),

  chat: (payload: { message: string; user_id?: number; session_id?: string; channel?: string }) =>
    request<{ reply: string; session_id?: string }>('/sales', { method: 'POST', body: JSON.stringify(payload) }),
};
