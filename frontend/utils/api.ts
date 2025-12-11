import type { Forum } from "@/types/forum";
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
    try {
      const urlObj = new URL(url);
      const cleanUrl = `${urlObj.origin}${urlObj.pathname}`;
      
      if (!urlObj.hostname.endsWith("u-cursos.cl")) {
        return Promise.resolve({
          exists: false,
          forum: null,
        });
      }
      return request<{ exists: boolean; forum: Forum }>(
        `/links/search?url=${encodeURIComponent(cleanUrl)}`
      );
    } catch (error) {
      console.error("Invalid URL provided to searchForum:", error);
      return Promise.resolve({
        exists: false,
        forum: null,
      });
    }
  },

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

  getCategories: () => 
    request<{ categories: string[] }>('/scraper/categories'),
  
  addForum: (url: string) => 
    request<Forum>("/links", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, name: "Foro U-Cursos" }),
    }),

  runScraper: (domain: string, model: "gpt" | "bert" = "bert") =>
    request<{ message: string; processed: number }>("/scraper/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ domain, model }),
    }),

  runScraperAll: (model: "gpt" | "bert" = "bert") => {
    console.log("Modelo enviado al backend desde api.ts:", model);
    return request<{ total: number; successful: number }>("/scraper/run-all", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ model }),
    });
  },
};