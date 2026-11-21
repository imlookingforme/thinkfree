const RAW_BASE = (import.meta as any).env?.VITE_API_URL || '';
const API_BASE = `${RAW_BASE.replace(/\/+$/, '')}/api/v1`;

export const apiClient = {
  get: async (url: string) => {
    const res = await fetch(`${API_BASE}${url}`, {
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    });
    if (!res.ok) {
      const err = await res.json().catch(() => null);
      throw new Error(err?.detail || err?.message || `Request failed with status ${res.status}`);
    }
    return { data: await res.json() };
  },
  post: async (url: string, body?: any) => {
    const res = await fetch(`${API_BASE}${url}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: body ? JSON.stringify(body) : undefined,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => null);
      throw new Error(err?.detail || err?.message || `Request failed with status ${res.status}`);
    }
    return { data: await res.json() };
  },
};
