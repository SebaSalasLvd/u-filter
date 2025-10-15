import browser from "webextension-polyfill";
import { useState } from "react";
import "./App.css"
import type { Post } from "@/components/PostCard";
import { PostCard } from "@/components/PostCard";

export default function App() {
    const [posts, setPosts] = useState<Post[]>([]);

    // Load persisted posts on popup open
    useEffect(() => {
        const loadPosts = async () => {
            const stored = await browser.storage.local.get('classified');
            const storedPosts: Post[] = Array.isArray(stored?.classified) ? stored.classified : [];
            setPosts(storedPosts);
        };
        loadPosts();
    }, []);

    useEffect(() => {
        const handleMessage = (message: any) => {
            if (message.action === "postClassified") {
                const post: Post = message.post;
                console.log("Received classification:", post);
                setPosts((prev) => {
                    const alreadyExists = prev.some((p) => p.id === post.id);
                    if (alreadyExists) return prev;
                        return [...prev, post];
                });
            }
        };

        browser.runtime.onMessage.addListener(handleMessage);
        return () => {
            browser.runtime.onMessage.removeListener(handleMessage);
        };
    }, []);

    return (
        <div className="popup-root">
            <div className="posts-list">
                {posts.map((p) => (
                    <PostCard key={p.id} post={p} />
                ))}
            </div>
        </div>
    );
}
