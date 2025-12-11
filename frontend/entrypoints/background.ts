import browser from "webextension-polyfill";
import { api, ApiError } from "@/utils/api";

export default defineBackground(() => {
  console.log("Background service worker started");
});

type CheckPostsMsg = { action: "checkAndFetchPosts"; url: string; categories?: string[]; model?: "gpt" | "bert" };
type AddForumMsg = { action: "addForum"; url: string };
type ScrapeForumMsg = { action: "scrapeForum"; url: string; model: "gpt" | "bert" };
type ScrapeAllMsg = { action: "scrapeAll"; model: "gpt" | "bert" };
type FetchPageMsg = { action: "fetchPage"; page: number; categories?: string[]; model?: "gpt" | "bert" };
type GetCategoriesMsg = { action: "getCategories" };

type ExtensionMessage = CheckPostsMsg | AddForumMsg | ScrapeForumMsg | ScrapeAllMsg | FetchPageMsg | GetCategoriesMsg;

const handleMessage = async (message: ExtensionMessage) => {
  try {
    switch (message.action) {
      case "checkAndFetchPosts":
        return await handleCheckPosts(message.url, message.categories, message.model);
      case "addForum":
        return await handleAddForum(message.url);
      case "scrapeForum":
        return await handleScrapeForum(message.url, message.model);
      case "scrapeAll":
        return await handleScrapeAll(message.model);
      case "fetchPage":
        return await handleFetchPage(message.page, message.categories, message.model);
      case "getCategories":
        return await handleGetCategories();
      default:
        throw new Error("Unknown action");
    }
  } catch (err) {
    console.error(`Error handling ${(message as any).action}:`, err);
    return { 
      status: "error", 
      message: err instanceof Error ? err.message : "Unknown error" 
    };
  }
};

async function handleScrapeAll(model: "gpt" | "bert" = "bert") {
  try {
    const result = await api.runScraperAll(model);
    return { status: "scrapingAllCompleted", result };
  } catch (err) {
    console.error("Error en handleScrapeAll:", err);
    throw err;
  }
}

async function handleCheckPosts(url: string, categories?: string[], model: "gpt" | "bert" | string = "bert") {
  if (!url) throw new Error("URL is required");
  
  let globalData = { posts: [], meta: { page: 1, total_pages: 1, per_page: 10, total_items: 0 } };

  try {
    globalData = await api.getPosts(1, undefined, categories, model);
  } catch (err) {
    console.error("Error posts globales:", err);
  }

  try {
    const { exists } = await api.searchForum(url);
    if (!exists) {
      return { status: "forumNotFound", data: globalData };
    }
    return { status: "postsFetched", data: globalData };

  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      return { status: "forumNotFound", data: globalData };
    }
    throw err;
  }
}

async function handleFetchPage(page: number, categories?: string[], model?: string) {
  try {
    const data = await api.getPosts(page, undefined, categories, model);
    return { status: "pageFetched", data };
  } catch (e) {
    throw e;
  }
}

async function handleGetCategories() {
  try {
    const result = await api.getCategories();
    return { status: "categoriesFetched", categories: result.categories };
  } catch (err) {
    console.error("Error getting categories:", err);
    throw err;
  }
}

async function handleAddForum(url: string) {
  if (!url) throw new Error("URL is required");
  
  const forum = await api.addForum(url);
  return { status: "forumAdded", forum };
}

async function handleScrapeForum(url: string, model: "gpt" | "bert") {
  // Validación extra por seguridad
  const safeModel = model === "gpt" ? "gpt" : "bert";
  const result = await api.runScraper(url, safeModel);
  return { status: "scrapingCompleted", result };
}

browser.runtime.onMessage.addListener((msg, sender) => {
  return handleMessage(msg as ExtensionMessage);
});