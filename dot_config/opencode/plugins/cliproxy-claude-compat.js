// CLIProxyAPI's Claude route rejects the thinking-binding extension emitted by
// OpenCode 2.0.12 for Fable 5.1 and Opus 5. Keep adaptive thinking and effort,
// removing only that unsupported extension from these proxy providers.
export default {
  id: "local.cliproxy-claude-compat",
  async setup(ctx) {
    const providerIDs = ctx.options.providerIDs ?? ["claude-personal", "claude-work"];

    for (const providerID of providerIDs) {
      await ctx.session.hook("http.request", async (event) => {
        const body = await event.request.clone().json();
        if (!body.thinking || !("block_binding" in body.thinking)) return;

        delete body.thinking.block_binding;
        const headers = new Headers(event.request.headers);
        headers.delete("content-length");
        const beta = (headers.get("anthropic-beta") ?? "")
          .split(",")
          .map((value) => value.trim())
          .filter((value) => value && value !== "thinking-binding-controls-2026-08-01");
        if (beta.length) headers.set("anthropic-beta", beta.join(","));
        else headers.delete("anthropic-beta");

        event.request = new Request(event.request, {
          headers,
          body: JSON.stringify(body),
        });
      }, { providerID });
    }
  },
};
