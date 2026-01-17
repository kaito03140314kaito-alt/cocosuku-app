// ログインチェック
if (!localStorage.getItem("isLoggedIn")) {
    window.location.href = "cocologin.html";
}

// 通知データ（仮）
const notifications = [
    { icon: "❤️", text: "たけっちょがあなたの投稿に「いいね」しました。", time: "1時間前", link: "cocootherprofile.html?user=たけっちょ" },
    { icon: "👤", text: "そらがあなたをフォローしました。", time: "3時間前", link: "cocootherprofile.html?user=そら" },
    { icon: "📝", text: "新しい話題の投稿がタイムラインにあります。", time: "昨日", link: "cocotimeline.html" }
];

const list = document.getElementById("notificationList");

notifications.forEach(n => {
    const item = document.createElement("div");
    item.className = "notification-item";
    item.onclick = () => window.location.href = n.link;

    item.innerHTML = `
        <div class="notif-icon">${n.icon}</div>
        <div class="notif-content">
            <div class="notif-text"><span style="font-weight:bold;">${n.text.split('が')[0]}</span>${n.text.slice(n.text.indexOf('が'))}</div>
            <div class="notif-time">${n.time}</div>
        </div>
    `;
    list.appendChild(item);
});

// 通知が0件の場合
if(notifications.length === 0){
    const noNotif = document.createElement("div");
    noNotif.style.textAlign = "center";
    noNotif.style.color = "var(--muted)";
    noNotif.style.marginTop = "30px";
    noNotif.textContent = "これ以上の通知はありません。";
    list.appendChild(noNotif);
}
