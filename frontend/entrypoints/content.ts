import browser from "webextension-polyfill";

export default defineContentScript({
    matches: ['*://*.u-cursos.cl/*'],
    main() {
        console.log('Hello content.');
        browser.runtime.onMessage.addListener(
            async (
                message: any,
                sender: browser.Runtime.MessageSender
            ): Promise<any> => {
                if (message.action === "getPosts") {
                    const posts = Array.from(document.querySelectorAll('[id^="raiz"]')).map((el) => ({
                        id: el.id || -1,
                        text: el.querySelector(".ta")?.textContent || "",
                        user: el.querySelector(".usuario")?.textContent || "",
                        title: el.querySelector("#mensaje-titulo")?.textContent || "",
                        label: "-",
                        score: "-",
                    }));
                    console.log(posts)
                    // Send the posts to background for sorting
                    // browser.runtime.sendMessage({ type: "processPosts", data: posts });
                    return posts
                }
            }
        );
    },
});

