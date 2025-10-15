import browser from "webextension-polyfill";

export default defineContentScript({
  matches: ["*://*.u-cursos.cl/*"],
  main() {
    const posts = getAllPosts();
    let current = 0;
    async function sendNext() {
      if (current >= posts.length) return;

      const post = posts[current];
      try {
        await browser.runtime.sendMessage({
          action: "classifyPost",
          post: post,
        });
      } catch (error) {
        console.error("Error sending post:", error);
      }

      current++;
      await sendNext();
    }

    sendNext();
  },
});

function getAllPosts() {
  const posts = Array.from(document.querySelectorAll('[id^="raiz"]')).map(
    (el) => ({
      id: el.id || -1,
      text: el.querySelector(".ta")?.textContent || "",
      user: el.querySelector(".usuario")?.textContent || "",
      title: el.querySelector("#mensaje-titulo")?.textContent || "",
      date:
        (el.querySelector(".tiempo_rel")?.textContent || "").match(
          /\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}/
        )?.[0] ?? " ",
      link: el.querySelector(".permalink")?.getAttribute("href") || "",
      label: "-",
      score: "-",
    })
  );
  return posts;
}
