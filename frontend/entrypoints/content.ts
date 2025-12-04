import browser from "webextension-polyfill";

export default defineContentScript({
  matches: ["*://*.u-cursos.cl/*"],
  async main() {

    const baseForumUrl = getBaseForumUrl();
    if (baseForumUrl) {
      const resp = await browser.runtime.sendMessage({
        action: "registerForum",
        url: baseForumUrl,
      });

      console.log("Wola", resp);
    }
  },
});


function getBaseForumUrl(): string | null {
  const url = new URL(window.location.href);
  const parts = url.pathname.split("/");

  const foroIndex = parts.indexOf("foro");
  if (foroIndex === -1) return null;

  const cleanPath = parts.slice(0, foroIndex + 1).join("/");
  return `${url.origin}${cleanPath}`;
}