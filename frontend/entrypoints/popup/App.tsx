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
    meta,       // <-- Nuevo: Metadatos de paginación
    changePage  // <-- Nuevo: Función para cambiar página
  } = usePosts();

  // Determinamos si debemos mostrar el botón de "Agregar"
  const showAddButton = status === "not_found";

  return (
    <div className="popup-root">
      
      {/* 1. HEADER SUPERIOR: Botones de Acción */}
      <header className="top-header">
        <div>
          {showAddButton && (
            <button onClick={addForum} className="action-btn btn-add">
              + Agregar este Foro
            </button>
          )}
        </div>

        <button 
          onClick={triggerUpdateAll} 
          disabled={isGlobalLoading}
          className="action-btn btn-refresh"
        >
          {isGlobalLoading ? "..." : "🔄 Actualizar Todo"}
        </button>
      </header>

      {/* 2. BARRA DE NAVEGACIÓN */}
      <NavBar />
      
      {/* 3. ÁREA DE CONTENIDO PRINCIPAL */}
      <div className="content-area">
        
        {/* Estados de Carga / Proceso */}
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

        {/* LÓGICA CLAVE: 
            Si el status es 'not_found', 'created' o 'found', mostramos la lista.
            Aunque esté vacía en 'not_found', ya no bloqueamos la UI.
        */}
        {(status === "found" || status === "created" || status === "not_found") && (
          <>
            {/* Si es nuevo, mostramos el botón de Scrapear manualmente */}
            {status === "created" && (
              <div style={{ marginBottom: 10, textAlign: 'center' }}>
                 <p style={{fontSize: '0.8em', color: '#666'}}>Foro registrado. Falta analizar.</p>
                 <button onClick={scrapeForum} className="action-btn btn-add">
                   Analizar Posts Ahora
                 </button>
              </div>
            )}

            {/* Si no encontrado y lista vacía, mensaje sutil, si no, la lista */}
            {posts.length === 0 ? (
              <div className="empty-state">
                {status === "not_found" 
                  ? "Este foro no está en la base de datos aún. Usa el botón superior para agregarlo." 
                  : "No hay posts registrados."}
              </div>
            ) : (
              <>
                <PostsList posts={posts} />
                
                {/* --- CONTROLES DE PAGINACIÓN --- */}
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
                      style={{ opacity: meta.page === 1 ? 0.5 : 1, cursor: meta.page === 1 ? 'default' : 'pointer' }}
                    >
                      Anterior
                    </button>
                    
                    <span style={{ fontSize: '0.8em', color: '#ffffffff' }}>
                      Pág {meta.page} de {meta.total_pages}
                    </span>
                    
                    <button 
                      disabled={meta.page === meta.total_pages}
                      onClick={() => changePage(meta.page + 1)}
                      className="action-btn"
                      style={{ opacity: meta.page === meta.total_pages ? 0.5 : 1, cursor: meta.page === meta.total_pages ? 'default' : 'pointer' }}
                    >
                      Siguiente
                    </button>
                  </div>
                )}
                {/* ------------------------------- */}
              </>
            )}
          </>
        )}
      </div>
    </div>
  );
}