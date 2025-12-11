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

export function usePosts(selectedModel: "gpt" | "bert") {
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
  
  const [availableCategories, setAvailableCategories] = useState<string[]>([]);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [selectedYear, setSelectedYear] = useState<string>("");
  const [isLoadingCategories, setIsLoadingCategories] = useState(false);

  const handleData = (data: PaginatedResponse) => {
    if (!data) return;
    setPosts(data.posts || []);
    if (data.meta) {
      setMeta(data.meta);
    }
  };

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
        categories: selectedCategories.length > 0 ? selectedCategories : undefined,
        model: selectedModel,
        year: selectedYear || undefined,
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
  }, [selectedCategories, selectedModel, selectedYear]);

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

  const scrapeForum = async (model: "gpt" | "bert") => {
    if (!currentUrl) return;
    setStatus("scraping");
    try {
      const response = (await browser.runtime.sendMessage({
        action: "scrapeForum",
        url: currentUrl,
        model,
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
        loadCategories();
      }
    } catch (e) {
      console.error("Error scraping forum:", e);
      setStatus("error");
    }
  };

  const triggerUpdateAll = async (model: "gpt" | "bert") => {
    console.log("Modelo recibido en usePosts.ts (triggerUpdateAll):", model);
    setIsGlobalLoading(true);
    try {
      const response = await browser.runtime.sendMessage({
        action: "scrapeAll",
        model,
      });
      console.log("Respuesta del background script en usePosts.ts:", response);
      checkCurrentTab();
      loadCategories();
    } catch (e) {
      console.error("Error en triggerUpdateAll:", e);
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
        categories: selectedCategories.length > 0 ? selectedCategories : undefined,
        model: selectedModel,
        year: selectedYear || undefined,
      })) as BackgroundResponse;

      if (response.status === "pageFetched" && 'data' in response) {
        handleData(response.data);
        document.querySelector('.content-area')?.scrollTo(0,0);
      }
    } catch (e) {
      console.error("Error cambiando página:", e);
    }
  };

  const handleCategoriesChange = (categories: string[]) => {
    setSelectedCategories(categories);
    setMeta(prev => ({ ...prev, page: 1 }));
  };

  const handleYearChange = (year: string) => {
    setSelectedYear(year);
    setMeta(prev => ({ ...prev, page: 1 }));
  };
  
  useEffect(() => {
    loadCategories();
  }, [loadCategories]);

  useEffect(() => {
    if (currentUrl) {
      checkCurrentTab();
    }
  }, [selectedCategories, selectedModel, selectedYear]);

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
    availableCategories,
    selectedCategories,
    handleCategoriesChange,
    isLoadingCategories,
    selectedYear,
    handleYearChange
  };
}