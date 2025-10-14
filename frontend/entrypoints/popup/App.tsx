import browser from "webextension-polyfill";
import { useState } from "react";

export default function App() {
    const [posts, setPosts] = useState<any[]>([]);

    async function fetchPosts() {
        const response = await browser.runtime.sendMessage({ action: "fetchPosts" });
        setPosts(Array.isArray(response) ? response : []);
    }

    return (
        <div>
            <button onClick={fetchPosts}>Load Posts</button>
            <ul>
                {posts.map((p) => (
                    <li key={p.id}>
                        <b>{p.title}</b>: <br></br>
                        <i>{p.label}, score {p.score}: </i> <br></br>
                        (<i>User: {p.user}</i>)
                        <p><span>{p.text}</span></p>
                        
                    </li>
                ))}
            </ul>
        </div>
    );
}
