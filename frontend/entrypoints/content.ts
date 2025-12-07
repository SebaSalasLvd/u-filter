import browser from "webextension-polyfill";

export default defineContentScript({
  matches: ["*://*.u-cursos.cl/*"],
  async main() {

    const baseForumUrl = getBaseForumUrl();
    if (baseForumUrl) {
      try {
        const resp = await browser.runtime.sendMessage({
          action: "checkAndFetchPosts",
          url: baseForumUrl,
        });

        console.log("U-Filter status:", resp);
      } catch (e) {
      }
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