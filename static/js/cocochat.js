// ==========================
// 必須：HTMLの <script> で
// ROOM_ID と CURRENT_UID が定義されている前提
// ==========================

// DMメッセージ取得
async function loadMessages() {
    if (!window.ROOM_ID) return;

    const res = await fetch(`/dm/messages/${ROOM_ID}`);
    const data = await res.json();

    const chatContainer = document.getElementById("chatContainer");
    chatContainer.innerHTML = "";

    data.messages.forEach(msg => {
        const wrapper = document.createElement("div");
        wrapper.className = "message-wrapper";

        const div = document.createElement("div");
        const isMe = msg.from_uid === CURRENT_UID;

        div.className = "message " + (isMe ? "you" : "them");
        div.textContent = msg.text;

        wrapper.appendChild(div);
        chatContainer.appendChild(wrapper);
    });

    chatContainer.scrollTop = chatContainer.scrollHeight;
}




// ==========================
// メッセージ送信
// ==========================
async function sendMessage() {
    const input = document.getElementById("chatInput");
    const text = input.value.trim();
    if (!text) return;

    const res = await fetch(`/dm/send/${ROOM_ID}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
    });

    const data = await res.json();
    if (data.success) {
        input.value = "";
        loadMessages();
    }
}


// ==========================
// エンターキー送信
// ==========================
document.addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
        sendMessage();
    }
});


// ==========================
// 初回ロード
// ==========================
window.addEventListener("load", () => {
    if (window.ROOM_ID) {
        loadMessages();
    }
});


// ==========================
// DM一覧ロード
// ==========================
async function loadDmList() {
    const container = document.getElementById("dmListContainer");
    if (!container) return;

    container.innerHTML = "";

    // Flask から埋め込まれた rooms を取得
    const rooms = window.DM_ROOMS || [];

    if (rooms.length === 0) {
        container.innerHTML = "<p style='color:#888; text-align:center;'>まだDMはありません</p>";
        return;
    }

    rooms.forEach(room => {
        const item = document.createElement("div");
        item.className = "dm-item";

        item.onclick = () => {
            location.href = `/dm/chat/${room.other_user.uid}`;
        };

        // アバター
        const avatar = document.createElement("div");
        avatar.className = "dm-avatar";
        if (room.other_user.avatar_url) {
            avatar.style.backgroundImage = `url(${room.other_user.avatar_url})`;
            avatar.style.backgroundSize = "cover";
        } else {
            avatar.textContent = room.other_user.name[0] || "？";
        }

        // ユーザー名 + 最終メッセージ
        const info = document.createElement("div");
        info.className = "dm-info";

        const name = document.createElement("div");
        name.className = "dm-name";
        name.textContent = room.other_user.name;

        const preview = document.createElement("div");
        preview.className = "dm-preview";
        preview.textContent = room.last_message || "";

        info.appendChild(name);
        info.appendChild(preview);

        item.appendChild(avatar);
        item.appendChild(info);

        container.appendChild(item);
    });
}

