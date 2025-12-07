import { useState, useEffect, useCallback } from "react";
import browser from "webextension-polyfill";
import type { Post } from "@/types/post";

export type ForumStatus = "loading" | "invalid_url" | "not_found" | "found" | "error" | "created" | "scraping";

type BackgroundResponse =
  | { status: "postsFetched"; posts: Post[] }
  | { status: "forumNotFound"; message: string }
  | { status: "forumAdded"; forum: unknown }
  | { status: "scrapingCompleted"; result: unknown }
  | { status: "error"; message: string }
  | { error: string };

export function usePosts() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [status, setStatus] = useState<ForumStatus>("loading");
  const [currentUrl, setCurrentUrl] = useState<string | null>(null);

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
      
      
      setCurrentUrl(forumUrl);

      const response = (await browser.runtime.sendMessage({
        action: "checkAndFetchPosts",
        url: forumUrl,
      })) as BackgroundResponse;

      if ("error" in response) {
        console.error("Error checking forum:", response.error);
        setStatus("error");
        return;
      }

      if (response.status === "postsFetched") {
        setPosts(response.posts);
        if (response.posts.length === 0) {
           setStatus("created"); 
        } else {
           setStatus("found");
        }
      } else if (response.status === "forumNotFound") {
        setPosts([]);
        setStatus("not_found");
      } else {
        console.error("Error checking forum:", response.message);
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

  useEffect(() => {
    checkCurrentTab();
  }, [checkCurrentTab]);

  return { posts, status, addForum, scrapeForum, checkCurrentTab };
}
