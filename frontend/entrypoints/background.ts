import browser from "webextension-polyfill";
import { api, ApiError } from "@/utils/api";

export default defineBackground(() => {
  console.log("Background service worker started");
});

type CheckPostsMsg = { action: "checkAndFetchPosts"; url: string };
type AddForumMsg = { action: "addForum"; url: string };
type ExtensionMessage = CheckPostsMsg | AddForumMsg;

const handleMessage = async (message: ExtensionMessage) => {
  try {
    switch (message.action) {
      case "checkAndFetchPosts":
        return await handleCheckPosts(message.url);
      case "addForum":
        return await handleAddForum(message.url);
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

async function handleCheckPosts(url: string) {
  if (!url) throw new Error("URL is required");

  try {
    const { exists } = await api.searchForum(url);
    
    if (!exists) {
      return { status: "forumNotFound" };
    }

    const posts = await api.getPosts(url);
    return { status: "postsFetched", posts };

  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      return { status: "forumNotFound" };
    }
    throw err;
  }
}

async function handleAddForum(url: string) {
  if (!url) throw new Error("URL is required");
  
  const forum = await api.addForum(url);
  return { status: "forumAdded", forum };
}

browser.runtime.onMessage.addListener((msg, sender) => {
  return handleMessage(msg as ExtensionMessage);
});