import { useState, useEffect, useMemo } from "react";
import { PostCard } from "@/components/PostCard";
import { Post } from "@/types/post";

interface PostsListProps {
  posts: Post[];
}

export function PostsList({ posts }: PostsListProps) {
  const [selectedYear, setSelectedYear] = useState<string>("");
  const [selectedLabel, setSelectedLabel] = useState<string>("");

  const years = useMemo(() => {
    const year = posts
      .map((p) => {
        if (!p.date) return null;
        const match = p.date.match(/^(\d{4})/);
        return match ? match[1] : null;
      })
      .filter(Boolean) as string[];
    return Array.from(new Set(year)).sort((a, b) => Number(b) - Number(a));
  }, [posts]);

  const labels = useMemo(() => {
    const l = posts.map((p) => p.label).filter(Boolean) as string[];
    return Array.from(new Set(l));
  }, [posts]);

  const [filteredPosts, setFilteredPosts] = useState<Post[]>(posts);
  useEffect(() => {
    const filtered = posts.filter((post) => {
      const postYear = post.date?.substring(0, 4);
      const matchYear = selectedYear ? postYear === selectedYear : true;
      const matchLabel = selectedLabel ? post.label === selectedLabel : true;
      return matchYear && matchLabel;
    });
    setFilteredPosts(filtered);
  }, [selectedYear, selectedLabel, posts]);

  if (posts.length === 0) {
    return <div className="empty-state">No hay posts clasificados aún</div>;
  }

  return (
    <div>
      <div className="filters">
        <select
          value={selectedYear}
          onChange={(e) => setSelectedYear(e.target.value)}
          className="select-year"
        >
          <option value="">Todos los años</option>
          {years.map((year) => (
            <option key={year} value={year}>
              {year}
            </option>
          ))}
        </select>

        <select
          value={selectedLabel}
          onChange={(e) => setSelectedLabel(e.target.value)}
          className="select-label"
        >
          <option value="">Todas las categorías</option>
          {labels.map((label) => (
            <option key={label} value={label}>
              {label}
            </option>
          ))}
        </select>
      </div>

      {filteredPosts.length === 0 ? (
        <div className="empty-state">
          No hay posts que coincidan con el filtro
        </div>
      ) : (
        <div className="posts-list">
          {filteredPosts.map((post) => (
            <PostCard key={post.id} post={post} />
          ))}
        </div>
      )}
    </div>
  );
}
