import { useState, useEffect, useCallback } from "react";
import browser from "webextension-polyfill";
import type { Post, PaginationMeta, PaginatedResponse } from "@/types/post";

export type ForumStatus = "loading" | "invalid_url" | "not_found" | "found" | "error" | "created" | "scraping";

type BackgroundResponse =
  | { status: "postsFetched"; data: PaginatedResponse }
  | { status: "forumNotFound"; data: PaginatedResponse }
  | { status: "pageFetched"; data: PaginatedResponse }
  | { status: "categoriesFetched"; categories: string[] }
  | { status: "forumAdded"; forum: unknown }
  | { status: "scrapingCompleted"; result: unknown }
  | { status: "scrapingAllCompleted"; result: unknown }
  | { status: "error"; message: string }
  | { error: string };

export function usePosts() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [meta, setMeta] = useState<PaginationMeta>({ 
    page: 1, 
    total_pages: 1, 
    per_page: 10, 
    total_items: 0 
  });
  const [status, setStatus] = useState<ForumStatus>("loading");
  const [currentUrl, setCurrentUrl] = useState<string | null>(null);
  const [isGlobalLoading, setIsGlobalLoading] = useState(false);
  
  // NUEVO: Estados para filtros de categorías
  const [availableCategories, setAvailableCategories] = useState<string[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [isLoadingCategories, setIsLoadingCategories] = useState(false);

  const handleData = (data: PaginatedResponse) => {
    if (!data) return;
    setPosts(data.posts || []);
    if (data.meta) {
      setMeta(data.meta);
    }
  };

  // NUEVO: Cargar categorías disponibles
  const loadCategories = useCallback(async () => {
    setIsLoadingCategories(true);
    try {
      const response = (await browser.runtime.sendMessage({
        action: "getCategories"
      })) as BackgroundResponse;

      if (response.status === "categoriesFetched") {
        setAvailableCategories(response.categories);
      }
    } catch (e) {
      console.error("Error loading categories:", e);
    } finally {
      setIsLoadingCategories(false);
    }
  }, []);

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
        categories: selectedCategories.length > 0 ? selectedCategories : undefined
      })) as BackgroundResponse;

      if ("error" in response) {
        console.error("Error checking forum:", response.error);
        setStatus("error");
        return;
      }

      if (response.status === "postsFetched" || response.status === "forumNotFound") {
        if ('data' in response) {
          handleData(response.data);
        }

        if (response.status === "forumNotFound") {
          setStatus("not_found");
        } else {
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
  }, [selectedCategories]);

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
        loadCategories(); // Recargar categorías después de scrapear
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
      loadCategories(); // Recargar categorías después de actualizar todo
    } catch (e) {
      console.error("Error updating all:", e);
    } finally {
      setIsGlobalLoading(false);
    }
  };

  const changePage = async (newPage: number) => {
    if (newPage < 1 || newPage > meta.total_pages) return;
    
    try {
      const response = (await browser.runtime.sendMessage({
        action: "fetchPage",
        page: newPage,
        categories: selectedCategories.length > 0 ? selectedCategories : undefined
      })) as BackgroundResponse;

      if (response.status === "pageFetched" && 'data' in response) {
        handleData(response.data);
        document.querySelector('.content-area')?.scrollTo(0,0);
      }
    } catch (e) {
      console.error("Error cambiando página:", e);
    }
  };

  // NUEVO: Función para cambiar las categorías seleccionadas
  const handleCategoriesChange = (categories: string[]) => {
    setSelectedCategories(categories);
    // Reset a página 1 cuando cambian los filtros
    setMeta(prev => ({ ...prev, page: 1 }));
  };
  
  // Cargar categorías al montar
  useEffect(() => {
    loadCategories();
  }, [loadCategories]);

  // Recargar posts cuando cambian las categorías
  useEffect(() => {
    if (currentUrl) {
      checkCurrentTab();
    }
  }, [selectedCategories]);

  useEffect(() => {
    checkCurrentTab();
  }, []);

  return { 
    posts, 
    meta,
    changePage,
    status, 
    addForum, 
    scrapeForum, 
    checkCurrentTab, 
    triggerUpdateAll, 
    isGlobalLoading,
    // NUEVO: Exports de filtros
    availableCategories,
    selectedCategories,
    handleCategoriesChange,
    isLoadingCategories
  };
}