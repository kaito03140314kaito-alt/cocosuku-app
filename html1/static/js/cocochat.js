// ダミーデータ
const mockProfiles = {
    "たけっちょ": { avatar: "た", color: "#ffd1dc", lastMessage: "ねえ、今度のイベントって...", time: "10:30" },
    "そら": { avatar: "そ", color: "#a0d1ff", lastMessage: "自動返信: すうはそ...ん。", time: "昨日" },
    "みかん": { avatar: "み", color: "#ffaa7f", lastMessage: "元気にしてる？", time: "2日前" }
};

let chatHistory = JSON.parse(localStorage.getItem("chatHistory")) || {
    "たけっちょ": [{from:"them", text:"今日の授業どうだった？"}],
    "そら": [{from:"them", text:"今日の教室どこ？"}, {from:"you", text:"しらん"}],
    "みかん": []
};

// ロゴクリックでタイムラインに遷移
function goTimeline() {
  window.location.href = "cocotimeline.html";
}


let currentUser = null;

const dmListScreen = document.getElementById("dmListScreen");
const dmListContainer = document.getElementById("dmListContainer");
const chatScreen = document.getElementById("chatScreen");
const chatTitle = document.getElementById("chatTitle");
const chatContainer = document.getElementById("chatContainer");
const chatInput = document.getElementById("chatInput");

function renderDmList() {
    dmListContainer.innerHTML = "";
    const users = Object.keys(mockProfiles);
    users.forEach(name => {
        const profile = mockProfiles[name];
        const history = chatHistory[name] || [];
        const lastMsg = history.length > 0 ? history[history.length - 1].text : "まだメッセージはありません";
        const lastTime = profile.time;

        const item = document.createElement("div");
        item.className = "dm-item";
        item.onclick = () => selectUser(name);

        item.innerHTML = `
            <div class="dm-avatar" style="background-color:${profile.color};">${profile.avatar}</div>
            <div class="dm-info">
                <div class="dm-name">${name}</div>
                <div class="dm-preview">${lastMsg}</div>
            </div>
            <div class="dm-time">${lastTime}</div>
        `;
        dmListContainer.appendChild(item);
    });
}

function selectUser(name) {
    currentUser = name;
    chatTitle.textContent = name;
    dmListScreen.style.display = "none";
    chatScreen.style.display = "flex";
    renderChat();
    chatInput.focus();
}

function showDmList() {
    currentUser = null;
    chatScreen.style.display = "none";
    dmListScreen.style.display = "block";
    renderDmList();
}

function renderChat() {
    chatContainer.innerHTML = "";
    if (!currentUser) return;

    const profile = mockProfiles[currentUser];
    const history = chatHistory[currentUser] || [];

    history.forEach(msg => {
        const wrapper = document.createElement("div");
        wrapper.className = "message-wrapper " + msg.from;
        const messageDiv = document.createElement("div");
        messageDiv.className = "message " + msg.from;
        messageDiv.textContent = msg.text;

        if (msg.from === "them") {
            const img = document.createElement("div");
            img.className = "chat-avatar";
            img.style.backgroundColor = profile.color;
            img.textContent = profile.avatar;
            wrapper.appendChild(img);
            wrapper.appendChild(messageDiv);
        } else {
            wrapper.appendChild(messageDiv);
        }
        chatContainer.appendChild(wrapper);
    });

    setTimeout(() => { chatContainer.scrollTop = chatContainer.scrollHeight; }, 10);
}

function sendMessage() {
    const text = chatInput.value.trim();
    if (!text) return;
    if (!currentUser) return alert("チャット相手が選択されていません。");

    const msg = {from:"you", text};
    if (!chatHistory[currentUser]) chatHistory[currentUser] = [];
    chatHistory[currentUser].push(msg);
    localStorage.setItem("chatHistory", JSON.stringify(chatHistory));

    chatInput.value = "";
    chatInput.focus();
    renderChat();

    setTimeout(() => {
        const reply = {from:"them", text: "自動返信: " + text.split("").reverse().join("")};
        chatHistory[currentUser].push(reply);
        localStorage.setItem("chatHistory", JSON.stringify(chatHistory));
        renderChat();
    }, 1000);
}

chatInput.addEventListener('keypress', e => {
    if (e.key === 'Enter') {
        e.preventDefault();
        sendMessage();
    }
});

window.addEventListener('load', renderDmList);
