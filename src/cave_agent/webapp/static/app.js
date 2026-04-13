const form = document.getElementById("run-form");
const tickersInput = document.getElementById("tickers");
const promptInput = document.getElementById("prompt");
const eventLog = document.getElementById("event-log");
const snapshotCards = document.getElementById("snapshot-cards");
const summaryText = document.getElementById("summary-text");
const artifactList = document.getElementById("artifacts");
const tablePreviews = document.getElementById("table-previews");
const chartPreviews = document.getElementById("chart-previews");
const statusPill = document.getElementById("status-pill");
const promptChips = document.querySelectorAll(".prompt-chip");
const submitButton = form.querySelector('button[type="submit"]');
let activePollToken = 0;

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
  statusPill.className = `status-pill ${status}`;
  statusPill.textContent = status;
}

function setSubmitting(submitting) {
  submitButton.disabled = submitting;
  submitButton.textContent = submitting ? "Running Agent..." : "Run Agent";
}

function formatMetric(value, currency = false) {
  if (value === null || value === undefined || value === "") {
    return "n/a";
  }
  if (typeof value === "number") {
    const absolute = Math.abs(value);
    if (currency) {
      if (absolute >= 1_000_000_000_000) return `$${(value / 1_000_000_000_000).toFixed(2)}T`;
      if (absolute >= 1_000_000_000) return `$${(value / 1_000_000_000).toFixed(1)}B`;
      if (absolute >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
      return `$${value.toFixed(1)}`;
    }
    return value.toFixed(1);
  }
  return value;
}

function renderArtifacts(runId, artifacts) {
  if (!artifacts.length) {
    renderEmptyState(artifactList, "Artifacts will appear here when the run completes.");
    return;
  }

  artifactList.innerHTML = "";
  artifacts.forEach((artifact) => {
    const node = document.createElement("div");
    node.className = "artifact-item";
    node.innerHTML = `
      <div>
        <a href="/api/runs/${runId}/artifacts/${artifact.name}">${artifact.label}</a>
        <div>${artifact.name}</div>
      </div>
      <span class="artifact-kind">${artifact.kind}</span>
    `;
    artifactList.appendChild(node);
  });
}

function renderSnapshotCards(cards) {
  if (!cards.length) {
    renderEmptyState(snapshotCards, "Snapshot cards will appear after the agent grounds the run in market data.");
    return;
  }

  snapshotCards.innerHTML = "";
  cards.forEach((card) => {
    const wrapper = document.createElement("div");
    wrapper.className = "snapshot-card";
    wrapper.innerHTML = `
      <h3>${card.ticker}</h3>
      <p><strong>${card.name}</strong><br>${card.sector}</p>
      <div class="snapshot-metrics">
        <div><span>Last Price</span><strong>${formatMetric(card.latest_close, true)}</strong></div>
        <div><span>P/E</span><strong>${formatMetric(card.pe_ratio)}</strong></div>
        <div><span>Market Cap</span><strong>${formatMetric(card.market_cap, true)}</strong></div>
        <div><span>Latest Revenue</span><strong>${formatMetric(card.latest_revenue, true)}</strong></div>
        <div><span>Net Income</span><strong>${formatMetric(card.latest_net_income, true)}</strong></div>
        <div><span>Recent Filing</span><strong>${card.recent_filing_form || "n/a"}</strong></div>
      </div>
      <p>${card.description || ""}</p>
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
    const thead = `<tr>${preview.columns.map((column) => `<th>${column}</th>`).join("")}</tr>`;
    const rows = preview.rows.map((row) => `<tr>${row.map((cell) => `<td>${cell ?? ""}</td>`).join("")}</tr>`).join("");
    wrapper.innerHTML = `<h3>${preview.name}</h3><table class="preview-table"><thead>${thead}</thead><tbody>${rows}</tbody></table>`;
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
    wrapper.innerHTML = `<h3>${preview.label || preview.name}</h3><img src="${preview.url}" alt="${preview.label || preview.name}">`;
    chartPreviews.appendChild(wrapper);
  });
}

async function fetchRun(runId) {
  const response = await fetch(`/api/runs/${runId}`);
  if (!response.ok) {
    throw new Error("Unable to fetch run result");
  }
  const payload = await response.json();
  summaryText.textContent = payload.summary_text || payload.error_message || "No summary generated.";
  renderSnapshotCards(payload.snapshot_cards || []);
  renderArtifacts(runId, payload.artifacts || []);
  renderTables(payload.preview_tables || []);
  renderCharts(payload.preview_charts || []);
  return payload;
}

async function pollRunUntilDone(runId, pollToken) {
  while (pollToken === activePollToken) {
    try {
      const payload = await fetchRun(runId);
      if (pollToken !== activePollToken) {
        return;
      }

      if (payload.status) {
        setStatus(payload.status);
      }
      if (payload.status === "completed" || payload.status === "failed") {
        setSubmitting(false);
        return;
      }
    } catch (error) {
      if (pollToken !== activePollToken) {
        return;
      }
      appendEvent(error.message || "Polling failed");
    }

    await new Promise((resolve) => window.setTimeout(resolve, 1200));
  }
}

promptChips.forEach((chip) => {
  chip.addEventListener("click", () => {
    tickersInput.value = chip.dataset.tickers || "";
    promptInput.value = chip.dataset.prompt || "";
    tickersInput.focus();
  });
});

renderEmptyState(snapshotCards, "Snapshot cards will appear after the agent grounds the run in market data.");
renderEmptyState(tablePreviews, "Comparison tables will appear here.");
renderEmptyState(chartPreviews, "Generated charts will appear here.");
renderEmptyState(artifactList, "Artifacts will appear here when the run completes.");

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  eventLog.innerHTML = "";
  summaryText.textContent = "Working...";
  setStatus("running");
  setSubmitting(true);
  renderEmptyState(snapshotCards, "Waiting for the agent to finish the run.");
  renderEmptyState(tablePreviews, "Waiting for the agent to generate table artifacts.");
  renderEmptyState(chartPreviews, "Waiting for the agent to generate chart artifacts.");
  renderEmptyState(artifactList, "Waiting for the agent to export run artifacts.");

  try {
    const formData = new FormData(form);
    const response = await fetch("/api/runs", {
      method: "POST",
      body: formData,
    });
    if (!response.ok) {
      throw new Error("Run creation failed");
    }

    const payload = await response.json();
    const runId = payload.run_id;
    appendEvent(`run created: ${runId}`);
    const pollToken = ++activePollToken;
    pollRunUntilDone(runId, pollToken);

    const stream = new EventSource(`/api/runs/${runId}/events`);
    stream.addEventListener("status", (evt) => {
      const data = JSON.parse(evt.data);
      setStatus(data.status || "running");
      appendEvent(data.message || data.status || "status");
    });
    stream.addEventListener("artifact", (evt) => {
      const data = JSON.parse(evt.data);
      appendEvent(`artifact ready: ${data.name}`);
    });
    stream.addEventListener("completed", async () => {
      setStatus("completed");
      appendEvent("run completed");
      activePollToken += 1;
      stream.close();
      await fetchRun(runId);
      setSubmitting(false);
    });
    stream.addEventListener("failed", async (evt) => {
      const data = JSON.parse(evt.data);
      setStatus("failed");
      appendEvent(`run failed: ${data.message}`);
      activePollToken += 1;
      stream.close();
      await fetchRun(runId);
      setSubmitting(false);
    });
    stream.onerror = () => {
      stream.close();
      appendEvent("event stream unavailable, using polling fallback");
    };
  } catch (error) {
    activePollToken += 1;
    setStatus("failed");
    summaryText.textContent = error.message || "Unable to start the run.";
    appendEvent(summaryText.textContent);
    setSubmitting(false);
  }
});
