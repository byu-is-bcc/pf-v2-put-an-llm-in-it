/* Minimal UI for the seed. Talks only to same-origin endpoints. No keys. */

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const text = await response.text();
  let body = null;
  if (text) {
    try {
      body = JSON.parse(text);
    } catch {
      body = text;
    }
  }
  if (!response.ok) {
    const detail = body && body.detail ? body.detail : response.statusText;
    const error = new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    error.status = response.status;
    throw error;
  }
  return body;
}

function el(tag, attrs = {}, children = []) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(attrs)) {
    if (key === "className") node.className = value;
    else if (key.startsWith("on") && typeof value === "function") node.addEventListener(key.slice(2).toLowerCase(), value);
    else node.setAttribute(key, value);
  }
  for (const child of children) {
    node.append(child instanceof Node ? child : document.createTextNode(child));
  }
  return node;
}

async function refreshHealth() {
  const target = document.getElementById("health");
  try {
    const data = await api("/health");
    target.textContent =
      `${data.snippets} snippets · provider ${data.provider} · model ${data.model} · ` +
      `requests today ${data.limits.requests_today}/${data.limits.request_cap}`;
  } catch (error) {
    target.textContent = `Health check failed: ${error.message}`;
    target.classList.add("error");
  }
}

function renderSnippet(snippet) {
  const result = el("p", { className: "result" }, [
    snippet.language || snippet.summary
      ? `language: ${snippet.language || "—"} · ${snippet.summary || ""}`
      : "Not analyzed yet.",
  ]);

  const analyze = el("button", { type: "button" }, ["Analyze with LLM"]);
  analyze.addEventListener("click", async () => {
    analyze.disabled = true;
    result.textContent = "Calling /analyze on the server…";
    result.classList.remove("error");
    try {
      const data = await api(`/snippets/${snippet.id}/analyze`, { method: "POST" });
      result.textContent =
        `${data.language}: ${data.summary} · ` +
        `${data.prompt_tokens + data.completion_tokens} tokens · ` +
        `${data.latency_ms} ms · ${data.provider}/${data.model}`;
      await refreshHealth();
    } catch (error) {
      result.textContent = error.message;
      result.classList.add("error");
    } finally {
      analyze.disabled = false;
    }
  });

  return el("li", { className: "snippet" }, [
    el("h3", {}, [snippet.title]),
    el("pre", {}, [snippet.body]),
    el("p", { className: "meta" }, [`#${snippet.id} · tags: ${snippet.tags || "(none)"}`]),
    el("div", { className: "row" }, [analyze]),
    result,
  ]);
}

async function refreshList() {
  const list = document.getElementById("list");
  list.replaceChildren();
  const snippets = await api("/snippets");
  if (!snippets.length) {
    list.append(el("li", { className: "meta" }, ["No snippets yet."]));
    return;
  }
  for (const snippet of snippets) {
    list.append(renderSnippet(snippet));
  }
}

document.getElementById("create").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const status = document.getElementById("form-status");
  const data = Object.fromEntries(new FormData(form).entries());
  status.textContent = "Saving…";
  status.classList.remove("error");
  try {
    await api("/snippets", { method: "POST", body: JSON.stringify(data) });
    form.reset();
    status.textContent = "Saved.";
    await refreshList();
    await refreshHealth();
  } catch (error) {
    status.textContent = error.message;
    status.classList.add("error");
  }
});

refreshHealth();
refreshList().catch((error) => {
  document.getElementById("list").textContent = error.message;
});
