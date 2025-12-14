const askBtn = document.getElementById("ask-btn");
const questionInput = document.getElementById("question");
const pipelineSelect = document.getElementById("pipeline");
const statusEl = document.getElementById("status");
const answerCard = document.getElementById("answer-card");
const answerEl = document.getElementById("answer");
const contextEl = document.getElementById("context");
const thumbUpBtn = document.getElementById("thumb-up");
const thumbDownBtn = document.getElementById("thumb-down");
const feedbackStatus = document.getElementById("feedback-status");
const refreshMetricsBtn = document.getElementById("refresh-metrics");
const metricsEl = document.getElementById("metrics");

let lastAnswerPayload = null;

async function askQuestion() {
  const question = questionInput.value.trim();
  const pipeline_id = pipelineSelect.value;

  if (!question) {
    statusEl.textContent = "Please enter a question.";
    return;
  }

  statusEl.textContent = "Thinking...";
  answerCard.style.display = "none";
  feedbackStatus.textContent = "";
  lastAnswerPayload = null;

  const start = performance.now();
  try {
    const resp = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, pipeline_id }),
    });
    if (!resp.ok) {
      const errText = await resp.text();
      throw new Error(`HTTP ${resp.status}: ${errText}`);
    }
    const data = await resp.json();
    const latencyMs = performance.now() - start;

    statusEl.textContent = `Done in ${latencyMs.toFixed(0)} ms`;
    answerEl.textContent = data.answer;
    contextEl.innerHTML = "";
    (data.context || []).forEach((c, idx) => {
      const block = document.createElement("pre");
      block.textContent = `[${idx + 1}] ` + c;
      contextEl.appendChild(block);
    });
    answerCard.style.display = "block";

    lastAnswerPayload = {
      question,
      answer: data.answer,
      pipeline_id: data.pipeline_id,
      latency_ms: data.latency_ms || latencyMs,
    };
  } catch (err) {
    console.error(err);
    statusEl.textContent = "Error: " + err.message;
  }
}

async function sendFeedback(thumbsUp) {
  if (!lastAnswerPayload) {
    feedbackStatus.textContent = "Ask a question first.";
    return;
  }
  feedbackStatus.textContent = "Saving...";
  try {
    const resp = await fetch("/api/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...lastAnswerPayload,
        thumbs_up: thumbsUp,
      }),
    });
    if (!resp.ok) {
      const txt = await resp.text();
      throw new Error(`HTTP ${resp.status}: ${txt}`);
    }
    feedbackStatus.textContent = "Saved ✓";
    refreshMetrics();
  } catch (err) {
    console.error(err);
    feedbackStatus.textContent = "Error saving feedback.";
  }
}

async function refreshMetrics() {
  metricsEl.textContent = "Loading...";
  try {
    const resp = await fetch("/api/metrics");
    if (!resp.ok) {
      const txt = await resp.text();
      throw new Error(`HTTP ${resp.status}: ${txt}`);
    }
    const data = await resp.json();
    const stats = data.per_pipeline || {};

    const table = document.createElement("table");
    const header = document.createElement("tr");
    header.innerHTML =
      "<th>Pipeline</th><th>Total</th><th>Positive</th><th>Positive rate</th>";
    table.appendChild(header);

    Object.entries(stats).forEach(([pid, s]) => {
      const tr = document.createElement("tr");
      tr.innerHTML = `<td>${pid}</td><td>${s.total}</td><td>${s.positive}</td><td>${(
        s.positive_rate * 100
      ).toFixed(1)}%</td>`;
      table.appendChild(tr);
    });

    metricsEl.innerHTML = "";
    metricsEl.appendChild(table);
  } catch (err) {
    console.error(err);
    metricsEl.textContent = "Error loading metrics.";
  }
}

askBtn.addEventListener("click", askQuestion);
questionInput.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
    askQuestion();
  }
});
thumbUpBtn.addEventListener("click", () => sendFeedback(true));
thumbDownBtn.addEventListener("click", () => sendFeedback(false));
refreshMetricsBtn.addEventListener("click", refreshMetrics);

refreshMetrics();
