import "./App.css";
import { usePosts } from "@/hooks/usePosts";
import { PostsList } from "@/components/PostsList";

export default function App() {
  const { posts } = usePosts();

  return (
    <div className="popup-root">
      <PostsList posts={posts} />
    </div>
  );
}
