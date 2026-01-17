// ===============================
// URLパラメータ → role / class_id / uid を取得
// ===============================
const params = new URLSearchParams(window.location.search);
document.getElementById("role").value = params.get("role");

document.getElementById("classId").value = decodeURIComponent(
  window.location.pathname.split("/")[2]
);

document.getElementById("uid").value = params.get("uid");

let userRole = params.get("role");
let classId = decodeURIComponent(document.getElementById("classId").value);
let uid = params.get("uid");


// ===============================
let today = new Date();
let currentMonth = today.getMonth();
let currentYear = today.getFullYear();
let loadedEvents = []; // Firestore から取得

const grid = document.getElementById("calendarGrid");
const monthLabel = document.getElementById("monthLabel");


// ===============================
// Firestore からイベント取得
// ===============================
async function loadEvents() {
  const res = await fetch(`/api/events?class_id=${classId}&role=${userRole}&uid=${uid}`);
  loadedEvents = await res.json();
  renderCalendar(currentMonth, currentYear);
}


// ===============================
// カレンダー描画
// ===============================
function renderCalendar(month, year) {
  grid.innerHTML = "";
  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();

  monthLabel.textContent = `${year}年 ${month + 1}月`;

  // 空白
  for (let i = 0; i < firstDay; i++) grid.appendChild(document.createElement("div"));

  for (let d = 1; d <= daysInMonth; d++) {
    const cell = document.createElement("div");
    cell.className = "day";
    cell.textContent = d;

    const dateStr = `${year}-${month + 1}-${d}`;

    // 今日
    if (
      d === today.getDate() &&
      month === today.getMonth() &&
      year === today.getFullYear()
    ) {
      cell.classList.add("today");
    }

    // 対象日のイベント
    const events = loadedEvents.filter(e => e.date === dateStr);

    if (events.length > 0) {
      cell.classList.add("has-event");

      events.slice(0, 2).forEach(e => {
        const p = document.createElement("div");
        p.className = "event-preview";
        p.textContent = (e.time ? e.time + " " : "") + e.title;
        cell.appendChild(p);
      });

      if (events.length > 2) {
        const more = document.createElement("div");
        more.className = "event-preview";
        more.textContent = "…その他";
        cell.appendChild(more);
      }
    }

    cell.addEventListener("click", () => openModal(dateStr));
    grid.appendChild(cell);
  }
}


// ===============================
// 月移動
// ===============================
function prevMonth() {
  currentMonth--;
  if (currentMonth < 0) { currentMonth = 11; currentYear--; }
  renderCalendar(currentMonth, currentYear);
}

function nextMonth() {
  currentMonth++;
  if (currentMonth > 11) { currentMonth = 0; currentYear++; }
  renderCalendar(currentMonth, currentYear);
}


// ===============================
// モーダル表示
// ===============================
const modalBg = document.getElementById("modalBg");
const modalDate = document.getElementById("modalDate");
const eventList = document.getElementById("eventList");

function openModal(date) {
  modalDate.textContent = date;
  modalBg.style.display = "flex";
  showEvents(date);
}

function closeModal() {
  modalBg.style.display = "none";
}


// ===============================
// イベント表示
// ===============================
function showEvents(date) {
  eventList.innerHTML = "";

  const events = loadedEvents.filter(e => e.date === date);

  if (events.length === 0) {
    eventList.innerHTML = "<div>予定なし</div>";
    return;
  }

  events.forEach(e => {
    const div = document.createElement("div");
    div.className = "event-card";

    div.innerHTML = `
      <div>${e.time || "時間指定なし"}</div>
      <div>${e.title}</div>
      ${e.memo ? `<div>${e.memo}</div>` : ""}
    `;

    // 削除ボタン
    const canDelete =
      (userRole === "teacher" && e.role === "teacher") ||
      (userRole === "student" && e.role === "student" && e.uid === uid);

    if (canDelete) {
      const btn = document.createElement("button");
      btn.className = "delete-btn";
      btn.textContent = "×";
      btn.onclick = () => deleteEvent(e.id);
      div.appendChild(btn);
    }

    eventList.appendChild(div);
  });
}


// ===============================
// 予定追加
// ===============================
async function addEvent() {
  const date = modalDate.textContent;
  const time = document.getElementById("eventTime").value;
  const title = document.getElementById("eventTitle").value.trim();
  const memo = document.getElementById("eventMemo").value.trim();

  if (!title) return alert("予定を入力してください！");

  const res = await fetch("/api/events", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      class_id: classId,
      date,
      time,
      title,
      memo,
      role: userRole,
      uid: uid
    })
  });

  const data = await res.json();

  if (data.ok) {
    await loadEvents();
    showEvents(date);
  }
}


// ===============================
// 予定削除
// ===============================
async function deleteEvent(eventId) {
  const res = await fetch("/api/events", {
    method: "DELETE",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      class_id: classId,
      id: eventId,
      role: userRole,
      uid: uid
    })
  });

  const data = await res.json();
  if (data.ok) {
    await loadEvents();
    showEvents(modalDate.textContent);
  }
}


// ===============================
// 初期ロード
// ===============================
loadEvents();
