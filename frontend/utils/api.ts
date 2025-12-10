import type { Forum } from "@/types/forum";
import type { Post } from "@/types/post";
import type { PaginatedResponse } from "@/types/post"; 

const API_BASE = import.meta.env.VITE_API_URL || "https://grupo2.jb.dcc.uchile.cl/proyecto/u-filter/api";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, options);
  if (!res.ok) {
    throw new ApiError(res.status, `API Error: ${res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  searchForum: (url: string) => {
    // 1. Validation Logic
    // If the URL does NOT have "u-cursos.cl" OR it does NOT have "foro"
    const cleanUrl = url.split('?')[0];
    if (!cleanUrl.includes("u-cursos.cl") || !cleanUrl.includes("foro")) {
      // We return a fake resolved promise so the calling code handles it gracefully.
      // Adjust 'exists' to true or false depending on how you want the UI to react.
      // If exists=true, the UI probably won't let you add it (which seems to be your goal).
      return Promise.resolve({ 
        exists: true, 
        forum: null as unknown as Forum // Mocking the forum or passing null
      });
    }

    // 2. Original Request Logic
    return request<{ exists: boolean; forum: Forum }>(`/links/search?url=${encodeURIComponent(cleanUrl)}`);
  },
  
  // MODIFICADO: Acepta page, domain y categories
  getPosts: (page: number = 1, domain?: string, categories?: string[]) => {
    const params = new URLSearchParams();
    params.append('page', page.toString());
    
    if (domain) {
      params.append('domain', domain);
    }
    
    if (categories && categories.length > 0) {
      params.append('categories', categories.join(','));
    }
    
    return request<PaginatedResponse>(`/scraper/list?${params.toString()}`);
  },
  
  // NUEVO: Obtener categorías disponibles
  getCategories: () => 
    request<{ categories: string[] }>('/scraper/categories'),
  
  addForum: (url: string) => 
    request<Forum>("/links", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, name: "Foro U-Cursos" }),
    }),

  runScraper: (domain: string) => 
    request<{ message: string; processed: number }>("/scraper/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ domain }),
    }),

  runScraperAll: () =>
    request<{ total: number; successful: number }>("/scraper/run-all", {
      method: "POST",
    }),
};