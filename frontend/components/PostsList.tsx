import { useState, useMemo } from "react";
import { PostCard } from "@/components/PostCard";
import { Post } from "@/types/post";

interface PostsListProps {
  posts: Post[];
  availableCategories: string[];
  selectedCategories: string[];
  selectedModel: "gpt" | "bert";
  onCategoriesChange: (categories: string[]) => void;
  isLoadingCategories?: boolean;
}

export function PostsList({ 
  posts, 
  availableCategories,
  selectedCategories,
  selectedModel,
  onCategoriesChange,
  isLoadingCategories = false
}: PostsListProps) {
  const [selectedYear, setSelectedYear] = useState<string>("");
  const [isCategoryFilterExpanded, setIsCategoryFilterExpanded] = useState(false);

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

  const filteredPosts = useMemo(() => {
    return posts.filter((post) => {
      const postYear = post.date?.substring(0, 4);
      const matchYear = selectedYear ? postYear === selectedYear : true;
      const matchCategories = selectedCategories.length > 0 
        ? selectedCategories.includes(post.label ?? "Otro")
        : true;
      const matchModel = post.model === selectedModel;
      console.log(selectedModel)
      return matchYear && matchCategories && matchModel;
    });
  }, [posts, selectedYear, selectedCategories, selectedModel]);

  const toggleCategory = (category: string) => {
    if (selectedCategories.includes(category)) {
      onCategoriesChange(selectedCategories.filter(c => c !== category));
    } else {
      onCategoriesChange([...selectedCategories, category]);
    }
  };

  const clearAllCategories = () => {
    onCategoriesChange([]);
  };

  const selectAllCategories = () => {
    onCategoriesChange([...availableCategories]);
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      'Compra': '#3b82f6',
      'Venta': '#f59e0b',
      'Arriendo': '#ef4444',
      'Clases Particulares': '#8b5cf6',
      'Oferta laboral/practica': '#06b6d4',
      'Otro': '#6b7280',
    };
    return colors[category] || '#64748b';
  };

  if (posts.length === 0) {
    return <div className="empty-state">No hay posts clasificados aún</div>;
  }

  return (
    <div>
      <div className="filters-container">
        <div className="filter-section">
          <label className="filter-label">📅 Año</label>
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
        </div>

        {availableCategories.length > 0 && (
          <div className="filter-section category-filter-wrapper">
            <label className="filter-label">🏷️ Categorías</label>
            <div className="category-filter">
              <div 
                className="filter-header" 
                onClick={() => setIsCategoryFilterExpanded(!isCategoryFilterExpanded)}
              >
                <span className="filter-title">
                  {selectedCategories.length > 0 
                    ? `${selectedCategories.length} seleccionada${selectedCategories.length > 1 ? 's' : ''}`
                    : 'Todas las categorías'
                  }
                </span>
                <span className="expand-icon">
                  {isCategoryFilterExpanded ? '▼' : '▶'}
                </span>
              </div>

              {isCategoryFilterExpanded && (
                <div className="filter-content">
                  {isLoadingCategories ? (
                    <div className="filter-loading">Cargando categorías...</div>
                  ) : (
                    <>
                      <div className="filter-actions">
                        <button 
                          onClick={selectAllCategories} 
                          className="filter-action-btn"
                          disabled={selectedCategories.length === availableCategories.length}
                        >
                          Todas
                        </button>
                        <button 
                          onClick={clearAllCategories} 
                          className="filter-action-btn"
                          disabled={selectedCategories.length === 0}
                        >
                          Limpiar
                        </button>
                      </div>

                      <div className="category-list">
                        {availableCategories.map((category) => (
                          <label 
                            key={category} 
                            className="category-item"
                            style={{
                              borderLeft: `3px solid ${getCategoryColor(category)}`
                            }}
                          >
                            <input
                              type="checkbox"
                              checked={selectedCategories.includes(category)}
                              onChange={() => toggleCategory(category)}
                              className="category-checkbox"
                            />
                            <span className="category-name">{category}</span>
                          </label>
                        ))}
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {selectedCategories.length > 0 && (
        <div className="active-filters-badge">
          <span>
            🔍 Filtrando: <strong>{selectedCategories.join(', ')}</strong>
          </span>
          <button 
            onClick={clearAllCategories}
            className="clear-filter-btn"
          >
            ✕
          </button>
        </div>
      )}

      {filteredPosts.length === 0 ? (
        <div className="empty-state">No hay posts que coincidan con el filtro</div>
      ) : (
        <div className="posts-list">
          {(() => {
            const seen = new Set<string>();
            const nodes: any[] = [];
            for (const post of filteredPosts) {
              const keyBase = post.url ? String(post.url) : `${post.id}-${post.date ?? ''}`;
              const key = keyBase;
              if (seen.has(key)) continue;
              seen.add(key);
              nodes.push(<PostCard key={key} post={post} />);
            }
            return nodes;
          })()}
        </div>
      )}
    </div>
  );
}