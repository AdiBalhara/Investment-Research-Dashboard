const API_BASE_URL = (typeof window !== 'undefined' ? '' : process.env.NEXT_PUBLIC_API_URL) || '';

interface FetchOptions extends RequestInit {
  skipAuth?: boolean;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private getToken(): string | null {
    if (typeof window === 'undefined') return null;
    return localStorage.getItem('access_token');
  }

  async fetch<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
    const { skipAuth = false, ...fetchOptions } = options;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(fetchOptions.headers as Record<string, string> || {}),
    };

    if (!skipAuth) {
      const token = this.getToken();
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
    }

    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...fetchOptions,
      headers,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
      throw new ApiError(response.status, error.detail || 'An error occurred');
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return response.json();
  }

  // Auth endpoints
  async signup(email: string, password: string, fullName?: string) {
    return this.fetch<{ access_token: string; token_type: string }>('/api/auth/signup', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name: fullName }),
      skipAuth: true,
    });
  }

  async login(email: string, password: string) {
    return this.fetch<{ access_token: string; token_type: string }>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
      skipAuth: true,
    });
  }

  async getMe() {
    return this.fetch<UserInfo>('/api/auth/me');
  }

  // Research endpoints
  async research(query: string) {
    return this.fetch<ResearchResult>('/api/research', {
      method: 'POST',
      body: JSON.stringify({ query }),
    });
  }

  // Reports endpoints
  async saveReport(query: string, result: Record<string, unknown>, confidence: number) {
    return this.fetch<Report>('/api/reports', {
      method: 'POST',
      body: JSON.stringify({ query, result, confidence }),
    });
  }

  async listReports(search?: string) {
    const params = search ? `?search=${encodeURIComponent(search)}` : '';
    return this.fetch<ReportListItem[]>(`/api/reports${params}`);
  }

  async getReport(id: string) {
    return this.fetch<Report>(`/api/reports/${id}`);
  }

  async deleteReport(id: string) {
    return this.fetch<void>(`/api/reports/${id}`, { method: 'DELETE' });
  }

  // Watchlist endpoints
  async addToWatchlist(ticker: string, companyName: string) {
    return this.fetch<WatchlistItem>('/api/watchlist', {
      method: 'POST',
      body: JSON.stringify({ ticker, company_name: companyName }),
    });
  }

  async listWatchlist() {
    return this.fetch<WatchlistItem[]>('/api/watchlist');
  }

  async removeFromWatchlist(id: string) {
    return this.fetch<void>(`/api/watchlist/${id}`, { method: 'DELETE' });
  }
}

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

// Types
export interface UserInfo {
  id: string;
  email: string;
  full_name: string | null;
  org_id: string;
  created_at: string;
}

export interface ResearchSection {
  type: string;
  render_as: string;
  title: string;
  data: unknown;
  source?: string | string[] | Record<string, unknown>;
  explanation?: string;
}

export interface ExecutionStep {
  tool: string;
  input: string;
  duration_ms: number;
  status: string;
}

export interface ResearchResult {
  query: string;
  confidence: number;
  sections: ResearchSection[];
  execution_steps: ExecutionStep[];
  reasoning: string;
}

export interface Report {
  id: string;
  query: string;
  result: Record<string, unknown>;
  confidence: number | null;
  created_at: string;
}

export interface ReportListItem {
  id: string;
  query: string;
  confidence: number | null;
  created_at: string;
}

export interface WatchlistItem {
  id: string;
  ticker: string;
  company_name: string;
  added_at: string;
}

export const api = new ApiClient(API_BASE_URL);
