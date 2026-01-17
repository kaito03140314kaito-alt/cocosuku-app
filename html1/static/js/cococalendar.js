// =============================
// ユーザーロール選択モーダル
// =============================
let userRole = null;

window.addEventListener("load", () => {
  showRoleModal();
});

function showRoleModal() {
  const modalBg = document.createElement("div");
  modalBg.id = "roleModalBg";
  modalBg.className = "role-modal-bg";
  modalBg.innerHTML = `
    <div class="role-modal">
      <h2>あなたの区分を選んでください</h2>
      <div class="role-buttons">
        <button class="role-btn student">学生</button>
        <button class="role-btn teacher">教師</button>
      </div>
      <div id="teacherPassArea" style="display:none;margin-top:12px;opacity:0;transform:translateY(-20px);transition:0.3s;">
        <input type="password" id="teacherPass" placeholder="暗証番号">
        <button class="role-btn confirm" style="margin-top:8px;">確認</button>
        <button class="role-btn cancel" style="margin-top:4px;">キャンセル</button>
      </div>
    </div>
  `;
  document.body.appendChild(modalBg);

  const passArea = modalBg.querySelector("#teacherPassArea");
  const passInput = passArea.querySelector("#teacherPass");
  const confirmBtn = passArea.querySelector(".confirm");
  const cancelBtn = passArea.querySelector(".cancel");

  // 学生ボタン
  modalBg.querySelector(".student").addEventListener("click", () => {
    userRole = "学生";
    closeRoleModal();
    setTimeout(() => alert("学生モードで開きます。"), 10);
  });

  // 教師ボタン
  modalBg.querySelector(".teacher").addEventListener("click", () => {
    if (passArea.style.display === "none") {
      passArea.style.display = "block";
      setTimeout(() => {
        passArea.style.opacity = 1;
        passArea.style.transform = "translateY(0)";
      }, 10);
      passInput.focus();
    }
  });

  passInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") checkTeacherPass(passInput.value);
  });

  confirmBtn.addEventListener("click", () => checkTeacherPass(passInput.value));

  cancelBtn.addEventListener("click", () => {
    passArea.style.opacity = 0;
    passArea.style.transform = "translateY(-20px)";
    setTimeout(() => { passArea.style.display = "none"; }, 300);
  });
}

function checkTeacherPass(pass) {
  if (pass === "1234") {
    userRole = "教師";
    closeRoleModal();
    setTimeout(() => alert("認証成功。教師モードで開きます。"), 10);
  } else {
    alert("暗証番号が間違っています。");
  }
}

function closeRoleModal() {
  const modalBg = document.getElementById("roleModalBg");
  if (modalBg) modalBg.remove();
  renderCalendar(currentMonth, currentYear);
}

// =============================
// カレンダー機能
// =============================
let today = new Date();
let currentMonth = today.getMonth();
let currentYear = today.getFullYear();
let events = JSON.parse(localStorage.getItem("events") || "[]");

const calendarGrid = document.getElementById("calendarGrid");
const monthLabel = document.getElementById("monthLabel");
const modalBgCalendar = document.getElementById("modalBg");
const modalDate = document.getElementById("modalDate");
const eventList = document.getElementById("eventList");
const eventTime = document.getElementById("eventTime");
const eventTitle = document.getElementById("eventTitle");
const eventMemo = document.getElementById("eventMemo");

function renderCalendar(month, year) {
  if (!userRole) return;

  calendarGrid.innerHTML = "";
  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  monthLabel.textContent = `${year}年 ${month + 1}月`;

  // 空白セル
  for (let i = 0; i < firstDay; i++) calendarGrid.appendChild(document.createElement("div"));

  // 日付セル
  for (let d = 1; d <= daysInMonth; d++) {
    const dayDiv = document.createElement("div");
    dayDiv.className = "day";
    const dateStr = `${year}-${month + 1}-${d}`;
    dayDiv.textContent = d;

    if (d === today.getDate() && month === today.getMonth() && year === today.getFullYear())
      dayDiv.classList.add("today");

    // 表示対象イベント
    const visibleEvents = events.filter(e => {
      if (userRole === "学生") return e.role === "学生" || e.role === "教師";
      else return e.role === "教師";
    }).filter(e => e.date === dateStr);

    if (visibleEvents.length > 0) {
      dayDiv.classList.add("has-event");
      visibleEvents.slice(0, 2).forEach(e => {
        const preview = document.createElement("div");
        preview.className = "event-preview";
        preview.textContent = (e.time ? e.time + " " : "") + e.title;
        preview.style.backgroundColor = e.role === "学生" ? "#ffd1dc" : "#ffeeba";
        preview.style.borderRadius = "8px";
        preview.style.padding = "2px 4px";
        dayDiv.appendChild(preview);
      });
      if (visibleEvents.length > 2) {
        const more = document.createElement("div");
        more.className = "event-preview";
        more.textContent = "…その他";
        dayDiv.appendChild(more);
      }
    }

    dayDiv.addEventListener("click", () => openModalCalendar(dateStr));
    calendarGrid.appendChild(dayDiv);
  }
}

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

// =============================
// モーダル操作
// =============================
function openModalCalendar(date) {
  modalDate.textContent = date;
  modalBgCalendar.style.display = "flex";
  showEvents(date);
}

function closeModal() {
  modalBgCalendar.style.display = "none";
  eventTime.value = "";
  eventTitle.value = "";
  eventMemo.value = "";
}

// =============================
// イベント処理（凡例付き）
// =============================
function showEvents(date) {
  eventList.innerHTML = "";

  // 凡例
  const legend = document.createElement("div");
  legend.style.display = "flex";
  legend.style.gap = "8px";
  legend.style.marginBottom = "8px";
  const studentLegend = document.createElement("div");
  studentLegend.style.backgroundColor = "#ffd1dc";
  studentLegend.style.width = "16px";
  studentLegend.style.height = "16px";
  studentLegend.style.borderRadius = "4px";
  studentLegend.title = "学生の予定";
  const teacherLegend = document.createElement("div");
  teacherLegend.style.backgroundColor = "#ffeeba";
  teacherLegend.style.width = "16px";
  teacherLegend.style.height = "16px";
  teacherLegend.style.borderRadius = "4px";
  teacherLegend.title = "教師の予定";
  legend.appendChild(studentLegend);
  legend.appendChild(document.createTextNode(" 学生"));
  legend.appendChild(teacherLegend);
  legend.appendChild(document.createTextNode(" 教師"));
  eventList.appendChild(legend);

  const dayEvents = events.filter(e => e.date === date && (
    (userRole === "教師" && e.role === "教師") ||
    (userRole === "学生" && (e.role === "教師" || e.role === "学生"))
  ));

  if (dayEvents.length === 0) eventList.innerHTML += "<div>予定なし</div>";
  else {
    dayEvents.forEach((e, index) => {
      const div = document.createElement("div");
      div.className = "event-card";
      div.style.backgroundColor = e.role === "学生" ? "#ffd1dc" : "#ffeeba";
      div.innerHTML = `
        <div class="event-time">${e.time || "時間指定なし"}</div>
        <div class="event-title">${e.title}</div>
        ${e.memo ? `<div class="event-memo">${e.memo}</div>` : ""}
        ${
          (userRole === "教師" && e.role === "教師") ||
          (userRole === "学生" && e.role === "学生")
            ? `<button class="delete-btn" onclick="deleteEvent('${date}',${index})">×</button>`
            : ""
        }
      `;
      eventList.appendChild(div);
    });
  }
}

function addEvent() {
  const date = modalDate.textContent;
  const time = eventTime.value;
  const title = eventTitle.value.trim();
  const memo = eventMemo.value.trim();
  if (!title) return alert("予定を入力してください！");

  const newEvent = { date, time, title, memo, role: userRole };
  events.push(newEvent);
  localStorage.setItem("events", JSON.stringify(events));
  showEvents(date);
  renderCalendar(currentMonth, currentYear);

  eventTime.value = "";
  eventTitle.value = "";
  eventMemo.value = "";
}

function deleteEvent(date, index) {
  events = events.filter((e, i) => !(e.date === date && i === index));
  localStorage.setItem("events", JSON.stringify(events));
  showEvents(date);
  renderCalendar(currentMonth, currentYear);
}
