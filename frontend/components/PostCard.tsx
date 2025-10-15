import React from 'react';

export type Post = {
    id: string | number;
    title: string;
    user?: string;
    label?: string;
    labelColor?: string;
    text?: string;
};

export const PostCard: React.FC<{ post: Post }> = ({ post }) => {
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