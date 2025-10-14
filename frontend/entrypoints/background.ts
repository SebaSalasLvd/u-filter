import browser from "webextension-polyfill";

export default defineBackground(() => {
    console.log('Hello background!', { id: browser.runtime.id });
});

browser.runtime.onMessage.addListener(
        async (
            message: any,
            sender: browser.Runtime.MessageSender
        ): Promise<any> => {
            if (message.action === "fetchPosts") {
                const [tab] = await browser.tabs.query({ active: true, currentWindow: true });
                if (!tab.id) return;

                const posts: any = await browser.tabs.sendMessage(tab.id, { action: "getPosts" });
                console.log(posts)

                for (const post of posts) {
                    try {
                        const response = await fetch("https://grupo2.jb.dcc.uchile.cl/proyecto/u-filter/backend", {
                                                        method: "POST",
                                                        headers: { "Content-Type": "application/json" },
                                                        body: JSON.stringify({ 'text': post.text })});

                        const data = await response.json();
                        console.log("Post classified: →", data.label);
                        post.label = data.label;
                        post.score = data.score.toFixed(2);
                    } 
                    
                    catch (err) {
                        console.error("Classification failed:", err);
                    }
                }
                return posts
            }
        }
);