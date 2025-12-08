import browser from "webextension-polyfill";
import { api, ApiError } from "@/utils/api";

export default defineBackground(() => {
  console.log("Background service worker started");
});

type CheckPostsMsg = { action: "checkAndFetchPosts"; url: string };
type AddForumMsg = { action: "addForum"; url: string };
type ScrapeForumMsg = { action: "scrapeForum"; url: string };
type ExtensionMessage = CheckPostsMsg | AddForumMsg | ScrapeForumMsg | ScrapeAllMsg | FetchPageMsg;
type ScrapeAllMsg = { action: "scrapeAll" };
type FetchPageMsg = { action: "fetchPage"; page: number };


const handleMessage = async (message: ExtensionMessage) => {
  try {
    switch (message.action) {
      case "checkAndFetchPosts":
        return await handleCheckPosts(message.url);
      case "addForum":
        return await handleAddForum(message.url);
      case "scrapeForum":
        return await handleScrapeForum(message.url);
      case "scrapeAll":
        return await handleScrapeAll(); // Nuevo handler
      case "fetchPage":
        return await handleFetchPage(message.page);
        
      default:
        throw new Error("Unknown action");
    }
  } catch (err) {
    console.error(`Error handling ${message.action}:`, err);
    return { 
      status: "error", 
      message: err instanceof Error ? err.message : "Unknown error" 
    };
  }
};

async function handleScrapeAll() {
  try {
    const result = await api.runScraperAll();
    return { status: "scrapingAllCompleted", result };
  } catch (err) {
    console.error("Error scraping all:", err);
    throw err;
  }
}

async function handleCheckPosts(url: string) {
  if (!url) throw new Error("URL is required");
  
  let globalData = { posts: [], meta: { page: 1, total_pages: 1 } };

  try {
    // Pedimos explícitamente la página 1
    globalData = await api.getPosts(1); 
  } catch (err) {
    console.error("Error posts globales:", err);
    return { status: "error", message: "Error al cargar posts" };
  }

  try {
    const { exists } = await api.searchForum(url);
    if (!exists) {
      return { status: "forumNotFound", data: globalData }; // Devolvemos objeto data completo
    }
    return { status: "postsFetched", data: globalData };

  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      return { status: "forumNotFound", data: globalData };
    }
    throw err;
  }
}

// 2. Nuevo Manejador para Cambios de Página
async function handleFetchPage(page: number) {
  try {
    const data = await api.getPosts(page);
    return { status: "pageFetched", data };
  } catch (e) {
    throw e;
  }
}


async function handleAddForum(url: string) {
  if (!url) throw new Error("URL is required");
  
  const forum = await api.addForum(url);
  return { status: "forumAdded", forum };
}

async function handleScrapeForum(url: string) {
  if (!url) throw new Error("URL is required");
  
  const result = await api.runScraper(url);
  return { status: "scrapingCompleted", result };
}

browser.runtime.onMessage.addListener((msg, sender) => {
  return handleMessage(msg as ExtensionMessage);
});