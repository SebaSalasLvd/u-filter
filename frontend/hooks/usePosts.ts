import { useState, useEffect } from "react";
import browser from "webextension-polyfill";
import type { Post } from "@/types/post";

export function usePosts() {
  const [posts, setPosts] = useState<Post[]>([]);

  // Load stored posts
  useEffect(() => {
    const loadPosts = async () => {
      const stored = await browser.storage.local.get("classified");
      const storedPosts: Post[] = Array.isArray(stored?.classified)
        ? stored.classified
        : [];
      setPosts(storedPosts);
    };
    loadPosts();
  }, []);

  // Listen for new classifications
  useEffect(() => {
    const handleMessage = (message: any) => {
      if (message.action === "postClassified") {
        const post: Post = message.post;
        setPosts((prev) => {
          const alreadyExists = prev.some((p) => p.id === post.id);
          if (alreadyExists) return prev;
          return [...prev, post];
        });
      }
    };

    browser.runtime.onMessage.addListener(handleMessage);
    return () => browser.runtime.onMessage.removeListener(handleMessage);
  }, []);

  return { posts };
}
