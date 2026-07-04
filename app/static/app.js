let currentEvents = [];

const form = document.querySelector("#analyze-form");
const textarea = document.querySelector("#expense-text");
const question = document.querySelector("#question");
const previewPanel = document.querySelector("#preview-panel");
const preview = document.querySelector("#preview");
const saveButton = document.querySelector("#save-button");
const monthInput = document.querySelector("#month-input");
const loadButton = document.querySelector("#load-button");
const expenseList = document.querySelector("#expense-list");
const summary = document.querySelector("#summary");
const receivables = document.querySelector("#receivables");
const personInput = document.querySelector("#person-input");
const personButton = document.querySelector("#person-button");

const money = new Intl.NumberFormat("ko-KR");

function currentMonth() {
  return new Date().toISOString().slice(0, 7);
}

function renderPreview(events) {
  preview.innerHTML = events
    .map((data, index) => {
      const rows = {
        이벤트: `${index + 1}`,
        날짜: data.date,
        제목: data.title,
        카테고리: data.category,
        "총 금액": `${money.format(data.total_amount)}원`,
        결제자: data.payer === "me" ? "나" : data.payer,
        "내 실제 결제": `${money.format(data.payment_amount)}원`,
        "내 부담액": `${money.format(data.my_share)}원`,
        "받을 돈": `${money.format(data.receivable_amount)}원`,
        "줄 돈": `${money.format(data.payable_amount)}원`,
        정산: data.settlement_type,
        "인원 수": data.people_count || "-",
        참여자: data.participants.map((item) => item.name).join(", ") || "-",
        메모: data.memo || "-",
      };
      return `<div class="event-preview">${Object.entries(rows)
        .map(([key, value]) => `<dt>${key}</dt><dd>${value}</dd>`)
        .join("")}</div>`;
    })
    .join("");
  previewPanel.classList.remove("hidden");
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  question.classList.add("hidden");
  previewPanel.classList.add("hidden");
  currentEvents = [];

  const response = await fetch("/api/expenses/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: textarea.value }),
  });
  const result = await response.json();

  if (result.status === "needs_clarification") {
    question.textContent = result.question;
    question.classList.remove("hidden");
    return;
  }

  currentEvents = result.events;
  renderPreview(currentEvents);
});

saveButton.addEventListener("click", async () => {
  if (!currentEvents.length) return;
  const response = await fetch("/api/expenses", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ events: currentEvents }),
  });
  if (response.ok) {
    currentEvents = [];
    previewPanel.classList.add("hidden");
    textarea.value = "";
    await loadDashboard();
  }
});

async function loadExpenses(month) {
  const response = await fetch(`/api/expenses?month=${encodeURIComponent(month)}`);
  const result = await response.json();
  expenseList.innerHTML = result.items
    .map(
      (item) =>
        `<li><strong>${item.date} ${item.title}</strong><br>${item.category} · 결제 ${money.format(item.payment_amount)}원 · 내 부담 ${money.format(item.my_share)}원</li>`,
    )
    .join("");
}

async function loadSummary(month) {
  const response = await fetch(`/api/summaries/monthly?month=${encodeURIComponent(month)}`);
  const result = await response.json();
  summary.innerHTML = [
    `<p><strong>전체</strong>: 결제 ${money.format(result.total.payment_amount)}원, 받을 돈 ${money.format(result.total.receivable_amount)}원, 내 부담 ${money.format(result.total.my_share)}원</p>`,
    ...result.categories.map(
      (item) =>
        `<p><strong>${item.category}</strong>: 결제 ${money.format(item.payment_amount)}원, 받을 돈 ${money.format(item.receivable_amount)}원, 내 부담 ${money.format(item.my_share)}원</p>`,
    ),
  ].join("");
}

async function loadReceivables(personName = "") {
  const url = personName ? `/api/receivables/${encodeURIComponent(personName)}` : "/api/receivables";
  const response = await fetch(url);
  const result = await response.json();
  const items = personName ? [result] : result.items;
  receivables.innerHTML = items
    .map(
      (item) =>
        `<p><strong>${item.person_name}</strong>: ${money.format(item.total_amount)}원</p>` +
        item.records.map((record) => `<p>${record.date} ${record.title} ${money.format(record.amount)}원</p>`).join(""),
    )
    .join("");
}

async function loadDashboard() {
  const month = monthInput.value || currentMonth();
  monthInput.value = month;
  await Promise.all([loadExpenses(month), loadSummary(month), loadReceivables()]);
}

loadButton.addEventListener("click", loadDashboard);
personButton.addEventListener("click", () => loadReceivables(personInput.value.trim()));

loadDashboard();
