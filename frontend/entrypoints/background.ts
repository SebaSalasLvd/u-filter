import browser from "webextension-polyfill";

export default defineBackground(() => {
  console.log("Hello background!", { id: browser.runtime.id });
});

browser.runtime.onMessage.addListener(
  async (message: any, sender: browser.Runtime.MessageSender): Promise<any> => {
    if (message.action === "classifyPost") {
      const post: any = message.post;

      // 1. Extract the domain from the sender's tab URL
      let domain = "unknown";
      if (sender.tab && sender.tab.url) {
        try {
          // This extracts just the domain (e.g., "www.reddit.com")
          domain = new URL(sender.tab.url).hostname; 
        } catch (e) {
          console.error("Failed to parse domain from URL", e);
        }
      }

      try {
        const response = await fetch(
          // "https://grupo2.jb.dcc.uchile.cl/proyecto/u-filter/backend",
          "http://127.0.0.1:7020/proyecto/u-filter/backend/scrapper",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            // 2. Add the domain to the JSON body
            body: JSON.stringify({ 
                text: post.text + post.title,
                domain: domain 
            }),
          }
        );
        const data = await response.json();
        post.label = data.label;
        post.score = data.score.toFixed(2);

        // Save to storage
        const prev: any =
          (await browser.storage.local.get("classified"))?.classified || [];
        await browser.storage.local.set({ classified: [...prev, post] });
      } catch (err) {
        console.error("Classification failed:", err);
      }

      try {
        await browser.runtime.sendMessage({
          action: "postClassified",
          post: post,
        });
      } catch (error) {
        console.error("Error sending post:", error);
      }
    }
  }
);
