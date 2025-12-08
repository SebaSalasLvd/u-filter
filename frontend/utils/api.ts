import type { Forum } from "@/types/forum";
import type { Post } from "@/types/post";
import type { PaginatedResponse } from "@/types/post"; 

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:7020/api";

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
  searchForum: (url: string) => 
    request<{ exists: boolean; forum: Forum }>(`/links/search?url=${encodeURIComponent(url)}`),
  
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