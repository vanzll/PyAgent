const sessionStorageKey = "pyagent-active-session";

const form = document.getElementById("chat-form");
const promptInput = document.getElementById("prompt");
const submitButton = document.getElementById("submit-button");
const newSessionButton = document.getElementById("new-session-button");
const chatThread = document.getElementById("chat-thread");
const eventLog = document.getElementById("event-log");
const snapshotCards = document.getElementById("snapshot-cards");
const summaryText = document.getElementById("summary-text");
const artifactList = document.getElementById("artifacts");
const tablePreviews = document.getElementById("table-previews");
const chartPreviews = document.getElementById("chart-previews");
const statusPill = document.getElementById("status-pill");
const promptChips = document.querySelectorAll(".prompt-chip");
const sessionIdLabel = document.getElementById("session-id-label");
const sessionFocusLabel = document.getElementById("session-focus-label");

const state = {
  sessionId: null,
  currentRunId: null,
  activePollToken: 0,
  eventSource: null,
};

function renderEmptyState(container, message) {
  container.innerHTML = `<div class="empty-state">${message}</div>`;
}

function appendEvent(message) {
  const item = document.createElement("div");
  item.className = "event-item";
  item.textContent = message;
  eventLog.prepend(item);
}

function setStatus(status) {
  if (!statusPill) {
    return;
  }
  statusPill.className = `status-pill ${status}`;
  statusPill.textContent = status;
}

function setSubmitting(submitting) {
  if (!submitButton) {
    return;
  }
  submitButton.disabled = submitting;
  submitButton.textContent = submitting ? "Running..." : "Send";
}

function formatMetric(value, currency = false) {
  if (value === null || value === undefined || value === "") {
    return "n/a";
  }
  if (typeof value === "number") {
    const absolute = Math.abs(value);
    if (currency) {
      if (absolute >= 1000000000000) return `$${(value / 1000000000000).toFixed(2)}T`;
      if (absolute >= 1000000000) return `$${(value / 1000000000).toFixed(1)}B`;
      if (absolute >= 1000000) return `$${(value / 1000000).toFixed(1)}M`;
      return `$${value.toFixed(1)}`;
    }
    return value.toFixed(1);
  }
  return value;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function renderMessages(messages) {
  if (!messages.length) {
    renderEmptyState(
      chatThread,
      "Start a session by asking about a ticker. The assistant will answer in chat and populate the workspace."
    );
    return;
  }

  chatThread.innerHTML = "";
  messages.forEach((message) => {
    const node = document.createElement("article");
    node.className = `chat-message ${message.role}`;
    const runMeta = message.run_id ? `<span class="message-run">Run ${message.run_id}</span>` : "";
    const focus = message.tickers && message.tickers.length ? message.tickers.join(", ") : "General market context";
    node.innerHTML = `
      <div class="message-meta">
        <span class="message-role">${message.role === "assistant" ? "Agent" : "You"}</span>
        <span class="message-focus">${escapeHtml(focus)}</span>
        ${runMeta}
      </div>
      <div class="message-body">${escapeHtml(message.content).replaceAll("\n", "<br>")}</div>
    `;
    chatThread.appendChild(node);
  });
  chatThread.scrollTop = chatThread.scrollHeight;
}

function renderArtifacts(artifacts) {
  if (!artifacts.length) {
    renderEmptyState(artifactList, "Artifacts will appear here after the agent completes a turn.");
    return;
  }

  artifactList.innerHTML = "";
  artifacts.forEach((artifact) => {
    const node = document.createElement("div");
    node.className = "artifact-item";
    node.innerHTML = `
      <div>
        <a href="${artifact.url || "#"}">${escapeHtml(artifact.label)}</a>
        <div>${escapeHtml(artifact.name)}</div>
      </div>
      <span class="artifact-kind">${escapeHtml(artifact.kind)}</span>
    `;
    artifactList.appendChild(node);
  });
}

function renderSnapshotCards(cards) {
  if (!cards.length) {
    renderEmptyState(snapshotCards, "Snapshot cards will appear after the agent grounds the turn in market data.");
    return;
  }

  snapshotCards.innerHTML = "";
  cards.forEach((card) => {
    const wrapper = document.createElement("div");
    wrapper.className = "snapshot-card";
    wrapper.innerHTML = `
      <h3>${escapeHtml(card.ticker)}</h3>
      <p><strong>${escapeHtml(card.name)}</strong><br>${escapeHtml(card.sector)}</p>
      <div class="snapshot-metrics">
        <div><span>Last Price</span><strong>${formatMetric(card.latest_close, true)}</strong></div>
        <div><span>P/E</span><strong>${formatMetric(card.pe_ratio)}</strong></div>
        <div><span>Market Cap</span><strong>${formatMetric(card.market_cap, true)}</strong></div>
        <div><span>Revenue</span><strong>${formatMetric(card.latest_revenue, true)}</strong></div>
        <div><span>Net Income</span><strong>${formatMetric(card.latest_net_income, true)}</strong></div>
        <div><span>Filing</span><strong>${escapeHtml(card.recent_filing_form || "n/a")}</strong></div>
      </div>
      <p>${escapeHtml(card.description || "")}</p>
    `;
    snapshotCards.appendChild(wrapper);
  });
}

function renderTables(previews) {
  if (!previews.length) {
    renderEmptyState(tablePreviews, "Comparison tables will appear here.");
    return;
  }

  tablePreviews.innerHTML = "";
  previews.forEach((preview) => {
    const wrapper = document.createElement("div");
    wrapper.className = "preview-card";
    const thead = `<tr>${preview.columns.map((column) => `<th>${escapeHtml(column)}</th>`).join("")}</tr>`;
    const rows = preview.rows
      .map((row) => `<tr>${row.map((cell) => `<td>${escapeHtml(cell === null || cell === undefined ? "" : cell)}</td>`).join("")}</tr>`)
      .join("");
    wrapper.innerHTML = `<h3>${escapeHtml(preview.name)}</h3><table class="preview-table"><thead>${thead}</thead><tbody>${rows}</tbody></table>`;
    tablePreviews.appendChild(wrapper);
  });
}

function renderCharts(previews) {
  if (!previews.length) {
    renderEmptyState(chartPreviews, "Generated charts will appear here.");
    return;
  }

  chartPreviews.innerHTML = "";
  previews.forEach((preview) => {
    const wrapper = document.createElement("div");
    wrapper.className = "preview-card chart-card";
    wrapper.innerHTML = `
      <h3>${escapeHtml(preview.label || preview.name)}</h3>
      <img src="${preview.url}" alt="${escapeHtml(preview.label || preview.name)}">
    `;
    chartPreviews.appendChild(wrapper);
  });
}

async function fetchSession(sessionId) {
  const response = await fetch(`/api/sessions/${sessionId}`);
  if (!response.ok) {
    throw new Error("Unable to fetch session");
  }
  const payload = await response.json();
  renderSession(payload);
  return payload;
}

function renderSession(payload) {
  state.sessionId = payload.session_id;
  state.currentRunId = payload.run_id || null;
  if (sessionIdLabel) {
    sessionIdLabel.textContent = payload.session_id;
  }
  if (sessionFocusLabel) {
    sessionFocusLabel.textContent = payload.tickers.length ? payload.tickers.join(", ") : "No tickers yet";
  }
  renderMessages(payload.messages || []);
  summaryText.textContent = payload.summary_text || "No research brief yet.";
  renderSnapshotCards(payload.snapshot_cards || []);
  renderArtifacts(payload.artifacts || []);
  renderTables(payload.preview_tables || []);
  renderCharts(payload.preview_charts || []);
  setStatus(payload.status || "idle");
}

function closeEventStream() {
  if (state.eventSource) {
    state.eventSource.close();
    state.eventSource = null;
  }
}

async function createSession(initialTickers = "") {
  const formData = new FormData();
  if (initialTickers) {
    formData.set("tickers", initialTickers);
  }
  const response = await fetch("/api/sessions", { method: "POST", body: formData });
  if (!response.ok) {
    throw new Error("Unable to create session");
  }
  const payload = await response.json();
  state.sessionId = payload.session_id;
  localStorage.setItem(sessionStorageKey, payload.session_id);
  appendEvent(`session created: ${payload.session_id}`);
  return payload.session_id;
}

async function ensureSession() {
  if (state.sessionId) {
    return state.sessionId;
  }

  const storedSessionId = localStorage.getItem(sessionStorageKey);
  if (storedSessionId) {
    try {
      await fetchSession(storedSessionId);
      return storedSessionId;
    } catch (error) {
      localStorage.removeItem(sessionStorageKey);
    }
  }

  const sessionId = await createSession("");
  await fetchSession(sessionId);
  return sessionId;
}

async function pollSessionUntilSettled(sessionId, runId, pollToken) {
  while (pollToken === state.activePollToken) {
    try {
      const payload = await fetchSession(sessionId);
      if (pollToken !== state.activePollToken) {
        return;
      }
      if ((payload.status === "completed" || payload.status === "failed") && payload.run_id === runId) {
        setSubmitting(false);
        return;
      }
    } catch (error) {
      if (pollToken !== state.activePollToken) {
        return;
      }
      appendEvent(error.message || "Polling failed");
    }

    await new Promise((resolve) => window.setTimeout(resolve, 1200));
  }
}

function startSessionEvents(sessionId, runId) {
  closeEventStream();
  const stream = new EventSource(`/api/sessions/${sessionId}/events`);
  state.eventSource = stream;

  stream.addEventListener("session", (evt) => {
    const data = JSON.parse(evt.data);
    setStatus(data.status || "idle");
  });
  stream.addEventListener("user", (evt) => {
    const data = JSON.parse(evt.data);
    appendEvent(`user: ${data.content}`);
  });
  stream.addEventListener("status", (evt) => {
    const data = JSON.parse(evt.data);
    if (data.run_id && data.run_id !== runId) {
      return;
    }
    setStatus(data.status || "running");
    appendEvent(data.message || data.status || "status");
  });
  stream.addEventListener("artifact", (evt) => {
    const data = JSON.parse(evt.data);
    if (data.run_id && data.run_id !== runId) {
      return;
    }
    appendEvent(`artifact ready: ${data.name}`);
  });
  stream.addEventListener("completed", async (evt) => {
    const data = JSON.parse(evt.data);
    if (data.run_id && data.run_id !== runId) {
      return;
    }
    state.activePollToken += 1;
    setStatus("completed");
    appendEvent("turn completed");
    closeEventStream();
    await fetchSession(sessionId);
    setSubmitting(false);
  });
  stream.addEventListener("failed", async (evt) => {
    const data = JSON.parse(evt.data);
    if (data.run_id && data.run_id !== runId) {
      return;
    }
    state.activePollToken += 1;
    setStatus("failed");
    appendEvent(`turn failed: ${data.message || "unknown error"}`);
    closeEventStream();
    await fetchSession(sessionId);
    setSubmitting(false);
  });
  stream.onerror = () => {
    closeEventStream();
    appendEvent("event stream unavailable, using polling fallback");
  };
}

function clearWorkspaceForPendingRun() {
  summaryText.textContent = "Working...";
  renderEmptyState(snapshotCards, "Waiting for the agent to update the workspace.");
  renderEmptyState(tablePreviews, "Waiting for table artifacts.");
  renderEmptyState(chartPreviews, "Waiting for chart artifacts.");
  renderEmptyState(artifactList, "Waiting for downloadable artifacts.");
}

promptChips.forEach((chip) => {
  chip.addEventListener("click", () => {
    promptInput.value = chip.dataset.prompt || "";
    promptInput.focus();
  });
});

newSessionButton.addEventListener("click", async () => {
  try {
    closeEventStream();
    state.activePollToken += 1;
    eventLog.innerHTML = "";
    renderEmptyState(chatThread, "Starting a new session…");
    const sessionId = await createSession("");
    await fetchSession(sessionId);
  } catch (error) {
    appendEvent(error.message || "Unable to start a new session");
  }
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const prompt = promptInput.value.trim();
  if (!prompt) {
    return;
  }

  try {
    const sessionId = await ensureSession();
    setSubmitting(true);
    setStatus("running");
    clearWorkspaceForPendingRun();

    const formData = new FormData();
    formData.set("prompt", prompt);

    const response = await fetch(`/api/sessions/${sessionId}/messages`, {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      throw new Error("Unable to send message");
    }

    const payload = await response.json();
    state.currentRunId = payload.run_id;
    promptInput.value = "";
    appendEvent(`run created: ${payload.run_id}`);
    await fetchSession(sessionId);
    startSessionEvents(sessionId, payload.run_id);
    const pollToken = ++state.activePollToken;
    pollSessionUntilSettled(sessionId, payload.run_id, pollToken);
  } catch (error) {
    state.activePollToken += 1;
    setStatus("failed");
    setSubmitting(false);
    appendEvent(error.message || "Unable to send message");
    summaryText.textContent = error.message || "Unable to send message";
  }
});

if (chatThread) {
  renderEmptyState(chatThread, "Ask about a ticker to start the conversation.");
}
if (snapshotCards) {
  renderEmptyState(snapshotCards, "Key metrics will appear after the agent queries market data.");
}
if (tablePreviews) {
  renderEmptyState(tablePreviews, "Structured comparison tables will appear here.");
}
if (chartPreviews) {
  renderEmptyState(chartPreviews, "Generated charts will appear here.");
}
if (artifactList) {
  renderEmptyState(artifactList, "Downloadable outputs will appear here.");
}

ensureSession().catch((error) => {
  setStatus("failed");
  appendEvent(error.message || "Unable to initialize the session");
});
