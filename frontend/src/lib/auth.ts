'use client';

import { useState, useEffect, useCallback } from 'react';
import { api, UserInfo } from './api';

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
}

export function setToken(token: string): void {
  localStorage.setItem('access_token', token);
}

export function removeToken(): void {
  localStorage.removeItem('access_token');
}

export function isAuthenticated(): boolean {
  return !!getToken();
}

export async function loginUser(email: string, password: string): Promise<void> {
  const response = await api.login(email, password);
  setToken(response.access_token);
}

export async function signupUser(email: string, password: string, fullName?: string): Promise<void> {
  const response = await api.signup(email, password, fullName);
  setToken(response.access_token);
}

export function logoutUser(): void {
  removeToken();
  window.location.href = '/login';
}

export function useAuth() {
  const [user, setUser] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchUser = useCallback(async () => {
    const token = getToken();
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      const userData = await api.getMe();
      setUser(userData);
    } catch {
      removeToken();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  return { user, loading, isAuthenticated: !!user, refresh: fetchUser };
}
