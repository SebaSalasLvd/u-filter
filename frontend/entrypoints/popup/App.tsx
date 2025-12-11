import { useState } from "react";
import "./App.css";
import { usePosts } from "@/hooks/usePosts";
import { PostsList } from "@/components/PostsList";
import { NavBar } from "@/components/NavBar";

export default function App() {
  const { 
    posts, 
    status, 
    addForum, 
    scrapeForum, 
    triggerUpdateAll, 
    isGlobalLoading,
    meta,
    changePage,
    availableCategories,
    selectedCategories,
    handleCategoriesChange,
    isLoadingCategories
  } = usePosts();

  const [selectedModel, setSelectedModel] = useState<"gpt" | "bert">("bert");

  const showAddButton = status === "not_found";

  const handleScrapeForum = async () => {
    if (status === "created" || status === "not_found") {
      await scrapeForum(selectedModel);
    }
  };

  return (
    <div className="popup-root">
      <NavBar />
      
      <div className="top-header">
        <div>
          {showAddButton && (
            <button onClick={addForum} className="action-btn btn-add">
              + Agregar este Foro
            </button>
          )}
        </div>

        <div className="model-selector">
          <select
            id="model-select"
            value={selectedModel}
            onChange={(e) => setSelectedModel(e.target.value as "gpt" | "bert")}
            className="select-model"
          >
            <option value="bert">BERT</option>
            <option value="gpt">GPT</option>
          </select>
        </div>

        <button 
          onClick={triggerUpdateAll} 
          disabled={isGlobalLoading}
          className="action-btn btn-refresh"
        >
          {isGlobalLoading ? "..." : "🔄 Actualizar Todo"}
        </button>
      </div>
    
      <div className="content-area">
        {status === "loading" && <div className="empty-state">Cargando...</div>}
        
        {status === "scraping" && (
          <div className="empty-state">
            <p>Clasificando posts con IA...</p>
          </div>
        )}

        {status === "invalid_url" && (
          <div className="empty-state">
            Navega a un foro de U-Cursos para activar.
          </div>
        )}

        {status === "error" && (
          <div className="empty-state error">
            Error de conexión.
          </div>
        )}

        {(status === "found" || status === "created" || status === "not_found") && (
          <>
            {status === "created" && (
              <div style={{ marginBottom: 10, textAlign: 'center' }}>
                 <p style={{fontSize: '0.8em', color: '#666'}}>Foro registrado. Falta analizar.</p>
                 <button onClick={handleScrapeForum} className="action-btn btn-add">
                   Analizar Posts Ahora
                 </button>
              </div>
            )}

            {posts.length === 0 ? (
              <div className="empty-state">
                {status === "not_found" 
                  ? "Este foro no está en la base de datos aún. Usa el botón superior para agregarlo." 
                  : selectedCategories.length > 0
                    ? "No hay posts con las categorías seleccionadas."
                    : "No hay posts registrados."}
              </div>
            ) : (
              <>
                <PostsList 
                  posts={posts}
                  availableCategories={availableCategories}
                  selectedCategories={selectedCategories}
                  onCategoriesChange={handleCategoriesChange}
                  isLoadingCategories={isLoadingCategories}
                  selectedModel={selectedModel}
                />
                
                {meta.total_pages > 1 && (
                  <div className="pagination-controls" style={{ 
                    display: 'flex', 
                    justifyContent: 'center', 
                    alignItems: 'center', 
                    gap: '10px', 
                    padding: '15px 0',
                    marginTop: '10px',
                    borderTop: '1px solid #eee'
                  }}>
                    <button 
                      disabled={meta.page === 1}
                      onClick={() => changePage(meta.page - 1)}
                      className="action-btn"
                      style={{ 
                        opacity: meta.page === 1 ? 0.5 : 1, 
                        cursor: meta.page === 1 ? 'default' : 'pointer' 
                      }}
                    >
                      Anterior
                    </button>
                    
                    <span style={{ fontSize: '0.8em', color: '#fff' }}>
                      Pág {meta.page} de {meta.total_pages}
                    </span>
                    
                    <button 
                      disabled={meta.page === meta.total_pages}
                      onClick={() => changePage(meta.page + 1)}
                      className="action-btn"
                      style={{ 
                        opacity: meta.page === meta.total_pages ? 0.5 : 1, 
                        cursor: meta.page === meta.total_pages ? 'default' : 'pointer' 
                      }}
                    >
                      Siguiente
                    </button>
                  </div>
                )}
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}