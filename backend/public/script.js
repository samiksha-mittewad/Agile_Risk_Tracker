const API_BASE_URL = window.location.origin;

const complexityLabels = {
  0: "Low",
  1: "Medium",
  2: "High",
};

const formData = {
  progress: 50,
  days_left: 10,
  team_size: 5,
  budget: 50,
  complexity: 1,
};

const fields = ["progress", "days_left", "team_size", "budget", "complexity"];
const riskForm = document.querySelector("#risk-form");
const trelloForm = document.querySelector("#trello-form");
const manualMessage = document.querySelector("#manual-message");
const trelloMessage = document.querySelector("#trello-message");
const trelloResults = document.querySelector("#trello-results");
const refreshHistoryButton = document.querySelector("#refresh-history");
const historyList = document.querySelector("#history-list");

const riskColors = {
  Low: "#22c55e",
  Medium: "#facc15",
  High: "#ef4444",
};

function normalizeRisk(label) {
  return String(label || "Waiting").toLowerCase();
}

function setMessage(element, text, isError = false) {
  element.textContent = text;
  element.classList.toggle("error", isError);
}

function updateSliderFill(input) {
  if (input.type !== "range") return;

  const min = Number(input.min);
  const max = Number(input.max);
  const value = Number(input.value);
  const percent = ((value - min) / (max - min)) * 100;
  input.style.background = `linear-gradient(90deg, #34d399 ${percent}%, rgba(30, 41, 59, 0.95) ${percent}%)`;
}

function syncSummary() {
  document.querySelector("#summary-progress").textContent = `${formData.progress}%`;
  document.querySelector("#summary-budget").textContent = `${formData.budget}%`;
  document.querySelector("#summary-complexity").textContent = complexityLabels[formData.complexity];
}

function syncFieldDisplay(name) {
  const valueElement = document.querySelector(`#${name}-value`);
  if (!valueElement) return;

  if (name === "progress" || name === "budget") {
    valueElement.textContent = `${formData[name]}%`;
    return;
  }

  if (name === "complexity") {
    valueElement.textContent = complexityLabels[formData.complexity];
    return;
  }

  valueElement.textContent = formData[name];
}

function getRiskExplanation(label) {
  const reasons = [];

  if (formData.progress < 40) {
    reasons.push("progress is still low");
  }
  if (formData.days_left <= 5) {
    reasons.push("the deadline is close");
  }
  if (formData.days_left < 0) {
    reasons.push("the project is already overdue");
  }
  if (formData.team_size <= 3) {
    reasons.push("the team is small");
  }
  if (formData.budget >= 80) {
    reasons.push("budget usage is high");
  }
  if (formData.complexity === 2) {
    reasons.push("task complexity is high");
  }

  if (reasons.length) {
    return `This is ${label.toLowerCase()} risk because ${reasons.slice(0, 3).join(", ")}.`;
  }

  if (label === "Low") {
    return "This is low risk because progress, timeline, team size, and budget look balanced.";
  }
  if (label === "Medium") {
    return "This is medium risk because the project has some warning signs and should be monitored.";
  }

  return "This is high risk because the current project signals suggest a strong chance of delay.";
}

function updateManualOutput(result) {
  const label = result.label || "Waiting";
  const riskClass = normalizeRisk(label);
  const indicator = document.querySelector("#manual-indicator");

  document.querySelector("#risk-level").textContent = label;
  document.querySelector("#risk-level").className = riskClass;
  document.querySelector("#confidence").textContent = `${result.confidence ?? "--"}%`;
  document.querySelector("#risk-explanation").textContent = result.explanation || getRiskExplanation(label);
  indicator.className = `risk-indicator ${riskClass}`;
}

async function postJson(path, payload) {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  const data = await response.json();
  if (!response.ok || data.error) {
    throw new Error(data.error || "Request failed");
  }

  return data;
}

async function getJson(path) {
  const response = await fetch(`${API_BASE_URL}${path}`);
  const data = await response.json();

  if (!response.ok || data.error) {
    throw new Error(data.error || "Request failed");
  }

  return data;
}

function extractBoardId(value) {
  const trimmed = value.trim();
  const match = trimmed.match(/trello\.com\/b\/([^/]+)/i);
  return match ? match[1] : trimmed;
}

function prepareCanvas(canvas) {
  const rect = canvas.getBoundingClientRect();
  const scale = window.devicePixelRatio || 1;
  const cssHeight = Number(canvas.dataset.height || canvas.getAttribute("height") || 220);

  canvas.dataset.height = cssHeight;
  canvas.style.height = `${cssHeight}px`;
  canvas.width = rect.width * scale;
  canvas.height = cssHeight * scale;

  const ctx = canvas.getContext("2d");
  ctx.setTransform(scale, 0, 0, scale, 0, 0);
  return {
    ctx,
    width: rect.width,
    height: cssHeight,
  };
}

function drawEmptyChart(canvas, message) {
  const { ctx, width, height } = prepareCanvas(canvas);
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#9ba9bd";
  ctx.font = "14px Inter, sans-serif";
  ctx.textAlign = "center";
  ctx.fillText(message, width / 2, height / 2);
}

function drawDistribution(counts) {
  const canvas = document.querySelector("#risk-distribution-chart");
  const total = Object.values(counts).reduce((sum, count) => sum + count, 0);

  if (!total) {
    drawEmptyChart(canvas, "No prediction history yet");
    return;
  }

  const { ctx, width, height } = prepareCanvas(canvas);
  const labels = ["Low", "Medium", "High"];
  const max = Math.max(...labels.map((label) => counts[label] || 0), 1);
  const barWidth = Math.min(72, (width - 80) / labels.length);
  const gap = (width - (barWidth * labels.length)) / (labels.length + 1);

  ctx.clearRect(0, 0, width, height);
  ctx.strokeStyle = "#253247";
  ctx.beginPath();
  ctx.moveTo(24, height - 42);
  ctx.lineTo(width - 12, height - 42);
  ctx.stroke();

  labels.forEach((label, index) => {
    const count = counts[label] || 0;
    const barHeight = ((height - 86) * count) / max;
    const x = gap + index * (barWidth + gap);
    const y = height - 42 - barHeight;

    ctx.fillStyle = riskColors[label];
    ctx.fillRect(x, y, barWidth, barHeight || 4);
    ctx.fillStyle = "#edf3ff";
    ctx.font = "700 16px Inter, sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(count, x + barWidth / 2, y - 10);
    ctx.fillStyle = "#9ba9bd";
    ctx.font = "12px Inter, sans-serif";
    ctx.fillText(label, x + barWidth / 2, height - 16);
  });
}

function drawTrend(history) {
  const canvas = document.querySelector("#risk-trend-chart");
  const points = [...history].reverse().slice(-18);

  if (points.length < 2) {
    drawEmptyChart(canvas, "Run at least two predictions");
    return;
  }

  const { ctx, width, height } = prepareCanvas(canvas);
  const chartLeft = 34;
  const chartRight = width - 16;
  const chartTop = 18;
  const chartBottom = height - 40;

  ctx.clearRect(0, 0, width, height);
  ctx.strokeStyle = "#253247";
  ctx.lineWidth = 1;

  ["High", "Medium", "Low"].forEach((label, index) => {
    const y = chartTop + index * ((chartBottom - chartTop) / 2);
    ctx.beginPath();
    ctx.moveTo(chartLeft, y);
    ctx.lineTo(chartRight, y);
    ctx.stroke();
    ctx.fillStyle = "#9ba9bd";
    ctx.font = "12px Inter, sans-serif";
    ctx.textAlign = "left";
    ctx.fillText(label, 0, y + 4);
  });

  const xStep = (chartRight - chartLeft) / (points.length - 1);
  const yForRisk = (prediction) => chartBottom - (prediction / 2) * (chartBottom - chartTop);

  ctx.beginPath();
  points.forEach((point, index) => {
    const x = chartLeft + index * xStep;
    const y = yForRisk(point.prediction);
    if (index === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  });
  ctx.strokeStyle = "#4dd4ac";
  ctx.lineWidth = 3;
  ctx.stroke();

  points.forEach((point, index) => {
    const x = chartLeft + index * xStep;
    const y = yForRisk(point.prediction);
    ctx.fillStyle = riskColors[point.label] || "#64748b";
    ctx.beginPath();
    ctx.arc(x, y, 5, 0, Math.PI * 2);
    ctx.fill();
  });
}

function renderHistoryRows(history) {
  if (!history.length) {
    historyList.innerHTML = '<p class="form-message">Predictions will appear here after you run the model.</p>';
    return;
  }

  historyList.innerHTML = history.slice(0, 6).map((item) => {
    const riskClass = normalizeRisk(item.label);
    const source = item.source === "trello" ? "Trello" : "Manual";
    const time = new Date(`${item.timestamp}Z`).toLocaleString([], {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });

    return `
      <article class="history-row">
        <span class="badge ${riskClass}">${item.label}</span>
        <div>
          <strong>${source} prediction</strong>
          <span>Progress ${item.progress}% | Budget ${item.budget}% | Team ${item.team_size}</span>
        </div>
        <strong>${item.confidence}%</strong>
        <span>${time}</span>
      </article>
    `;
  }).join("");
}

async function loadHistory() {
  try {
    const result = await getJson("/history?limit=50");
    const summary = result.summary || {};
    const history = result.history || [];

    document.querySelector("#history-total").textContent = summary.total || 0;
    document.querySelector("#history-confidence").textContent = `${summary.average_confidence || 0}%`;
    document.querySelector("#history-latest").textContent = summary.latest?.label || "None";

    drawDistribution(summary.counts || {});
    drawTrend(history);
    renderHistoryRows(history);
  } catch (error) {
    historyList.innerHTML = `<p class="form-message error">${error.message}</p>`;
  }
}

function renderTrelloTasks(tasks) {
  if (!tasks.length) {
    trelloResults.innerHTML = '<p class="form-message">No cards were returned for this board.</p>';
    return;
  }

  trelloResults.innerHTML = tasks.map((task, index) => {
    const riskClass = normalizeRisk(task.label);
    const inputs = task.inputs || {};

    return `
      <article class="task-card">
        <div class="task-topline">
          <strong>Task ${index + 1}</strong>
          <span class="badge ${riskClass}">${task.label}</span>
        </div>
        <div>
          <span class="muted-label">Confidence</span>
          <strong class="confidence">${task.confidence}%</strong>
          <p class="risk-explanation">${task.explanation || "Risk explanation was not returned."}</p>
        </div>
        <div class="task-meta">
          <span>Progress: ${inputs.progress ?? "--"}%</span>
          <span>Days: ${inputs.days_left ?? "--"}</span>
          <span>Team: ${inputs.team_size ?? "--"}</span>
          <span>Budget: ${inputs.budget ?? "--"}%</span>
        </div>
      </article>
    `;
  }).join("");
}

fields.forEach((name) => {
  const input = document.querySelector(`#${name}`);

  input.addEventListener("input", (event) => {
    formData[name] = Number(event.target.value);
    updateSliderFill(event.target);
    syncFieldDisplay(name);
    syncSummary();
  });
});

riskForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = riskForm.querySelector("button");
  const originalText = button.textContent;

  setMessage(manualMessage, "Predicting risk...");
  button.textContent = "Analyzing...";
  button.disabled = true;

  try {
    const result = await postJson("/predict", formData);
    updateManualOutput(result);
    setMessage(manualMessage, result.message || "Prediction complete.");
    loadHistory();
  } catch (error) {
    setMessage(manualMessage, error.message, true);
  } finally {
    button.textContent = originalText;
    button.disabled = false;
  }
});

trelloForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = trelloForm.querySelector("button");
  const boardId = extractBoardId(document.querySelector("#board_id").value);

  if (!boardId) {
    setMessage(trelloMessage, "Enter a Trello board ID or URL.", true);
    return;
  }

  setMessage(trelloMessage, "Fetching Trello cards and predicting risk...");
  trelloResults.innerHTML = "";
  button.disabled = true;

  try {
    const result = await postJson("/trello", { board_id: boardId });
    renderTrelloTasks(result.tasks || []);
    setMessage(trelloMessage, `Processed ${(result.tasks || []).length} Trello task(s).`);
    loadHistory();
  } catch (error) {
    setMessage(trelloMessage, error.message, true);
  } finally {
    button.disabled = false;
  }
});

refreshHistoryButton.addEventListener("click", loadHistory);
window.addEventListener("resize", loadHistory);
fields.forEach(syncFieldDisplay);
fields.forEach((name) => updateSliderFill(document.querySelector(`#${name}`)));
syncSummary();
loadHistory();
