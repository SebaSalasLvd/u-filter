import "./App.css";
import { usePosts } from "@/hooks/usePosts";
import { PostsList } from "@/components/PostsList";
import { NavBar } from "@/components/NavBar";

export default function App() {
  const { posts } = usePosts();

  return (
    <div className="popup-root">
      <NavBar />
      <PostsList posts={posts} />
    </div>
  );
}
