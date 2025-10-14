import browser from "webextension-polyfill";
import { useState } from "react";
import "./App.css"

export type Post = {
    id: string | number;
    title: string;
    user?: string;
    label?: string;
    labelColor?: string;
    text?: string;
};

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

function PostCard({ post }: { post: Post }) {
    const [open, setOpen] = useState(false);

    return (
        <article className="post">
            <div className="post-header">
                <div className="post-left">
                    <div className="post-title">{post.title}</div>
                    <div className="post-user">por {post.user ?? "unknown"}</div>
                </div>

                <div className="post-right">
                    {post.label && (
                        <span
                            className="post-label"
                            style={{ backgroundColor: post.labelColor ?? "rgba(207, 54, 100, 1)" }}
                        >
                            {post.label}
                        </span>
                    )}

                    <button
                        className={`toggle-btn ${open ? "open" : ""}`}
                        onClick={() => setOpen((s) => !s)}
                        aria-expanded={open}
                        aria-label={open ? "Collapse post text" : "Expand post text"}
                        title={open ? "Collapse" : "Expand"}
                    >
                        <svg
                            className="toggle-icon"
                            width="14"
                            height="14"
                            viewBox="0 0 24 24"
                            aria-hidden="true"
                        >
                            <path d="M8.59 16.59L13.17 12 8.59 7.41 10 6l6 6-6 6z" />
                        </svg>
                    </button>
                </div>
            </div>

            <div className={`post-text-wrapper ${open ? "open" : ""}`} aria-hidden={!open}>
                <div className="post-text">{post.text}</div>
            </div>

        </article>
  );
}
