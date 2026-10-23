/**
 * api.ts
 * ======
 * Unified API Client for KrishiBondhu Next.js Frontend
 * Communicates with FastAPI backend (NEXT_PUBLIC_BACKEND_URL)
 * with robust error handling and fallback capabilities.
 */

export const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export interface ApiResponse<T = unknown> {
  success: boolean;
  data?: T;
  error?: {
    code: string;
    message_bn?: string;
    message?: string;
  };
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl.replace(/\/+$/, "");
  }

  private getAuthHeaders(token?: string): Record<string, string> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      Accept: "application/json",
    };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    return headers;
  }

  async get<T>(endpoint: string, token?: string): Promise<ApiResponse<T>> {
    try {
      const res = await fetch(`${this.baseUrl}${endpoint}`, {
        method: "GET",
        headers: this.getAuthHeaders(token),
      });
      const data = await res.json();
      return data;
    } catch (err) {
      return {
        success: false,
        error: {
          code: "NETWORK_ERROR",
          message_bn: "সার্ভারে সংযোগ করা সম্ভব হচ্ছে না।",
          message: err instanceof Error ? err.message : "Network error",
        },
      };
    }
  }

  async post<T>(
    endpoint: string,
    body: unknown,
    token?: string
  ): Promise<ApiResponse<T>> {
    try {
      const res = await fetch(`${this.baseUrl}${endpoint}`, {
        method: "POST",
        headers: this.getAuthHeaders(token),
        body: JSON.stringify(body),
      });
      const data = await res.json();
      return data;
    } catch (err) {
      return {
        success: false,
        error: {
          code: "NETWORK_ERROR",
          message_bn: "সার্ভারে সংযোগ করা সম্ভব হচ্ছে না।",
          message: err instanceof Error ? err.message : "Network error",
        },
      };
    }
  }

  async patch<T>(
    endpoint: string,
    body: unknown,
    token?: string
  ): Promise<ApiResponse<T>> {
    try {
      const res = await fetch(`${this.baseUrl}${endpoint}`, {
        method: "PATCH",
        headers: this.getAuthHeaders(token),
        body: JSON.stringify(body),
      });
      const data = await res.json();
      return data;
    } catch (err) {
      return {
        success: false,
        error: {
          code: "NETWORK_ERROR",
          message_bn: "সার্ভারে সংযোগ করা সম্ভব হচ্ছে না।",
          message: err instanceof Error ? err.message : "Network error",
        },
      };
    }
  }

  async delete<T>(endpoint: string, token?: string): Promise<ApiResponse<T>> {
    try {
      const res = await fetch(`${this.baseUrl}${endpoint}`, {
        method: "DELETE",
        headers: this.getAuthHeaders(token),
      });
      const data = await res.json();
      return data;
    } catch (err) {
      return {
        success: false,
        error: {
          code: "NETWORK_ERROR",
          message_bn: "সার্ভারে সংযোগ করা সম্ভব হচ্ছে না।",
          message: err instanceof Error ? err.message : "Network error",
        },
      };
    }
  }
}

export const api = new ApiClient(`${BACKEND_URL}/api/v1`);
