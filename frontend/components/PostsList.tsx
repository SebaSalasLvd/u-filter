import { PostCard } from "@/components/PostCard";
import { Post } from "@/types/post";

interface PostsListProps {
  posts: Post[];
}

export function PostsList({ posts }: PostsListProps) {
  if (posts.length === 0) {
    return <div className="empty-state">No hay posts clasificados aún</div>;
  }

  return (
    <div className="posts-list">
      {posts.map((post) => (
        <PostCard key={post.id} post={post} />
      ))}
    </div>
  );
}
