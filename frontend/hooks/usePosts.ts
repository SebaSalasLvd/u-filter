import { useState, useEffect, useCallback } from "react";
import browser from "webextension-polyfill";
import type { Post, PaginationMeta, PaginatedResponse } from "@/types/post";

export type ForumStatus = "loading" | "invalid_url" | "not_found" | "found" | "error" | "created" | "scraping";

// Actualizamos los tipos para que coincidan con la respuesta paginada del background
type BackgroundResponse =
  | { status: "postsFetched"; data: PaginatedResponse }
  | { status: "forumNotFound"; data: PaginatedResponse }
  | { status: "pageFetched"; data: PaginatedResponse }
  | { status: "forumAdded"; forum: unknown }
  | { status: "scrapingCompleted"; result: unknown }
  | { status: "scrapingAllCompleted"; result: unknown }
  | { status: "error"; message: string }
  | { error: string };

export function usePosts() {
  const [posts, setPosts] = useState<Post[]>([]);
  // Estado inicial de paginación
  const [meta, setMeta] = useState<PaginationMeta>({ page: 1, total_pages: 1, per_page: 10, total_items: 0 });
  const [status, setStatus] = useState<ForumStatus>("loading");
  const [currentUrl, setCurrentUrl] = useState<string | null>(null);
  const [isGlobalLoading, setIsGlobalLoading] = useState(false);

  // Helper para actualizar posts y meta simultáneamente
  const handleData = (data: PaginatedResponse) => {
    if (!data) return;
    setPosts(data.posts || []);
    if (data.meta) {
      setMeta(data.meta);
    }
  };

  const checkCurrentTab = useCallback(async () => {
    setStatus("loading");
    try {
      const tabs = await browser.tabs.query({ active: true, currentWindow: true });
      const activeTab = tabs[0];
      
      if (!activeTab?.url) {
        setStatus("invalid_url");
        return;
      }

      const forumUrl = new URL(activeTab.url);
      setCurrentUrl(forumUrl.toString());

      const response = (await browser.runtime.sendMessage({
        action: "checkAndFetchPosts",
        url: forumUrl.toString(),
      })) as BackgroundResponse;

      if ("error" in response) {
        console.error("Error checking forum:", response.error);
        setStatus("error");
        return;
      }

      // Lógica unificada: tanto found como not_found traen datos paginados
      if (response.status === "postsFetched" || response.status === "forumNotFound") {
        
        // 1. Guardamos los datos (posts + meta)
        if ('data' in response) {
          handleData(response.data);
        }

        // 2. Determinamos el status de la UI
        if (response.status === "forumNotFound") {
          setStatus("not_found");
        } else {
          // Si es postsFetched, verificamos si hay posts para decidir si mostrar "created" (vacío) o "found"
          // Usamos response.data.posts con seguridad
          const hasPosts = response.data && response.data.posts && response.data.posts.length > 0;
          setStatus(hasPosts ? "found" : "created");
        }
      } else {
        setStatus("error");
      }
    } catch (e) {
      console.error("Error in usePosts:", e);
      setStatus("error");
    }
  }, []);

  const addForum = async () => {
    if (!currentUrl) return;
    try {
      const response = (await browser.runtime.sendMessage({
        action: "addForum",
        url: currentUrl,
      })) as BackgroundResponse;

      if ("error" in response) {
        console.error("Error adding forum:", response.error);
        return;
      }

      if (response.status === "forumAdded") {
        setStatus("created");
      }
    } catch (e) {
      console.error("Error adding forum:", e);
      setStatus("error");
    }
  };

  const scrapeForum = async () => {
    if (!currentUrl) return;
    setStatus("scraping");
    try {
      const response = (await browser.runtime.sendMessage({
        action: "scrapeForum",
        url: currentUrl,
      })) as BackgroundResponse;

      if ("error" in response || (response.status === "error")) {
        console.error("Error scraping forum");
        setStatus("error");
        return;
      }

      if (response.status === "scrapingCompleted") {
        const result = response.result as any;
        if (result && result.error) {
            console.error("Scraper error:", result.error);
            setStatus("error");
            return;
        }
        checkCurrentTab();
      }
    } catch (e) {
      console.error("Error scraping forum:", e);
      setStatus("error");
    }
  };

  const triggerUpdateAll = async () => {
    setIsGlobalLoading(true);
    try {
      const response = await browser.runtime.sendMessage({
        action: "scrapeAll",
      });
      console.log("Update all response:", response);
      checkCurrentTab();
    } catch (e) {
      console.error("Error updating all:", e);
    } finally {
      setIsGlobalLoading(false);
    }
  };

  // Función para cambiar de página
  const changePage = async (newPage: number) => {
    if (newPage < 1 || newPage > meta.total_pages) return;
    
    try {
      const response = (await browser.runtime.sendMessage({
        action: "fetchPage",
        page: newPage
      })) as BackgroundResponse; // Casting explícito

      if (response.status === "pageFetched" && 'data' in response) {
        handleData(response.data);
        // Scroll al top de la lista
        document.querySelector('.content-area')?.scrollTo(0,0);
      }
    } catch (e) {
      console.error("Error cambiando página:", e);
    }
  };
  
  useEffect(() => {
    checkCurrentTab();
  }, [checkCurrentTab]);

  return { 
    posts, 
    meta,           // EXPORTADO
    changePage,     // EXPORTADO
    status, 
    addForum, 
    scrapeForum, 
    checkCurrentTab, 
    triggerUpdateAll, 
    isGlobalLoading 
  };
}