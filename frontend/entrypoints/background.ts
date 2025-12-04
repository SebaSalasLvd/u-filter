import browser from "webextension-polyfill";
import type { Forum } from "../types/forum";

export default defineBackground(() => {
  console.log("Background running", { id: browser.runtime.id });
});

const BASE = "https://grupo2.jb.dcc.uchile.cl/proyecto/u-filter/backend";

type Message = { action: string; [k: string]: any };
type Handler = (msg: Message, sender: browser.Runtime.MessageSender) => any;

const handlers: Record<string, Handler> = {};
const register = (name: string, fn: Handler) => (handlers[name] = fn);

register("registerForum", async (msg: Message) => {
  const url = msg.url as string;
  if (!url) return { error: "missing url" };

  try {
    const existsResp = await fetch(
      `${BASE}/foros?url=${encodeURIComponent(url)}`
    );
    const existsData = (await existsResp.json()) as { exists?: boolean; forum?: Forum };

    if (existsData?.exists) {
      return { status: "exists", forum: existsData.forum };
    }

    // register
    const registerResp = await fetch(`${BASE}/foros`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url }),
    });

    const registerData = (await registerResp.json()) as Forum | { error?: string };
    return {
      status: registerResp.ok ? "created" : "error",
      data: registerData,
    };
  } catch (err) {
    console.error("registerForum failed:", err);
    return { error: String(err) };
  }
});


browser.runtime.onMessage.addListener(
  async (rawMsg: unknown, sender: browser.Runtime.MessageSender) => {
    const msg = rawMsg as Message;
    const fn = handlers[msg.action];
    if (!fn) return { error: `Unknown action '${msg.action}'` };

    try {
      return await fn(msg, sender);
    } catch (err) {
      console.error(`Handler '${msg.action}' failed:`, err);
      return { error: String(err) };
    }
  }
);
