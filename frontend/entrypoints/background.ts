import browser from "webextension-polyfill";

export default defineBackground(() => {
    console.log('Hello background!', { id: browser.runtime.id });
});

browser.runtime.onMessage.addListener(
    async (
        message: any,
        sender: browser.Runtime.MessageSender
    ): Promise<any> => {
        if (message.action === "classifyPost") {
            const post: any = message.post;
            try {
                const response = await fetch("https://grupo2.jb.dcc.uchile.cl/proyecto/u-filter/backend", {
                                                method: "POST",
                                                headers: { "Content-Type": "application/json" },
                                                body: JSON.stringify({ 'text': post.text })});

                const data = await response.json();
                console.log("Post classified: →", data.label);
                post.label = data.label;
                post.score = data.score.toFixed(2);

                // Save to storage
                const prev: any = (await browser.storage.local.get('classified'))?.classified || [];
                await browser.storage.local.set({ classified: [...prev, post] });
            }
                
            catch (err) {
                console.error("Classification failed:", err);
            }
            
            try {
                await browser.runtime.sendMessage({
                    action: 'postClassified',
                    post: post,
                });
            } 
            catch (error) {
                console.error('Error sending post:', error);
            }
        }
    }
);