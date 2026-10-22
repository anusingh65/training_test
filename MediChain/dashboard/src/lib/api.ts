const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = {
  base: API,

  async get(path: string) {
    const res = await fetch(`${API}${path}`);
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    return res.json();
  },

  async post(path: string, body: unknown) {
    const res = await fetch(`${API}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    return res.json();
  },

  async postFile(path: string, file: File, params?: Record<string, string>) {
    const url = new URL(`${API}${path}`);
    if (params) Object.entries(params).forEach(([k, v]) => url.searchParams.set(k, v));
    const form = new FormData();
    form.append("file", file);
    const res = await fetch(url.toString(), { method: "POST", body: form });
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
    return res.json();
  },

  wsUrl(path: string) {
    return `${API.replace(/^http/, "ws")}${path}`;
  },
};
