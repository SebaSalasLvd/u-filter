import "./App.css";
import { usePosts } from "@/hooks/usePosts";
import { PostsList } from "@/components/PostsList";
import { NavBar } from "@/components/NavBar";

export default function App() {
  const { posts, status, addForum, scrapeForum } = usePosts();

  return (
    <div className="popup-root">
      <NavBar />
      
      <div style={{ padding: "0 10px" }}>
        {status === "loading" && (
          <div className="empty-state">Cargando...</div>
        )}

        {status === "scraping" && (
          <div className="empty-state">
            <p>Clasificando posts con IA...</p>
            <p style={{ fontSize: "0.8em" }}>Esto puede tomar unos segundos.</p>
          </div>
        )}
        
        {status === "invalid_url" && (
          <div className="empty-state">
            Navega a un foro de U-Cursos para ver los posts clasificados.
          </div>
        )}

        {status === "not_found" && (
          <div className="empty-state" style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "10px" }}>
            <p>Este foro no está registrado en U-Filter.</p>
            <button onClick={addForum}>
              Agregar Foro
            </button>
          </div>
        )}

        {status === "created" && (
          <div className="empty-state" style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "10px" }}>
            <p>Foro registrado exitosamente.</p>
            <p>Aún no hay posts clasificados.</p>
            <button onClick={scrapeForum} style={{ backgroundColor: "#4CAF50", color: "white" }}>
              Clasificar Posts Ahora
            </button>
          </div>
        )}

        {status === "error" && (
          <div className="empty-state">
            Ocurrió un error al conectar con el servidor.
          </div>
        )}

        {status === "found" && <PostsList posts={posts} />}
      </div>
    </div>
  );
}
