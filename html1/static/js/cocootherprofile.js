// データ取得
let posts = JSON.parse(localStorage.getItem("posts") || "[]");
let follows = JSON.parse(localStorage.getItem("follows") || "{}");
let myProfile = JSON.parse(localStorage.getItem("profile") || '{"name":"ゲスト","avatar":"ゲ"}');

// URLパラメータ
const urlParams = new URLSearchParams(window.location.search);
const userName = urlParams.get("user");

// モックプロフィール
const mockProfiles = {
  "そら": {
    name:"そら",
    bio:"趣味は写真、サークルはテニスです。",
    avatar:"そ",
    details:{
      hobby: "読書、写真",
      circle: "テニスサークル",
      dept: "情報システム学科",
      year: "1年",
      license: "基本情報技術者試験 合格",
      comment: "よろしくお願いします！"
    },
    posts: [
      { text:"HTMLとCSSの勉強を頑張っています！", time:"2025-11-03T10:00:00" },
      { text:"文化祭でポスター制作を担当しました！", time:"2025-10-21T15:30:00" },
      { text:"最近はPythonでWebアプリを作ってみました！", time:"2025-09-18T20:45:00" }
    ]
  },
  "たけっちょ": {
    name:"たけっちょ",
    bio:"勉強頑張ってます！",
    avatar:"た",
    details:{
      hobby: "プログラミング、ゲーム",
      circle: "勉強サークル",
      dept: "情報デザイン学科",
      year: "2年",
      license: "未取得",
      comment: "日々成長中！"
    },
    posts: [
      { text:"サークルで新しいプロジェクト始めました！", time:"2025-11-01T14:20:00" },
      { text:"Gitとチーム開発を体験してみたいです。", time:"2025-10-15T18:00:00" }
    ]
  }
};

// プロフィール確定
const userProfile = mockProfiles[userName] || {
  name: userName || "不明なユーザー",
  bio: "",
  avatar: "?",
  details: {
    hobby: "未設定",
    circle: "未設定",
    dept: "未設定",
    year: "未設定",
    license: "未設定",
    comment: ""
  },
  posts: []
};

// 初期化
function initProfile(){
  const icon = document.getElementById("profileIcon");
  const nameEl = document.getElementById("profileName");
  const header = document.getElementById("userNameHeader");
  const bioEl = document.getElementById("profileBio");
  if(icon) { icon.textContent = userProfile.avatar; }
  if(nameEl) { nameEl.textContent = userProfile.name; }
  if(header) { header.textContent = userProfile.name; }
  if(bioEl) { bioEl.textContent = userProfile.bio; }

  renderDetails(userProfile.details);
  updateFollowBtn();
  updateStats();
  renderUserPosts();
}

// 詳細情報レンダリング
function renderDetails(details){
  const area = document.getElementById("detailsArea");
  if(!area) return;
  area.innerHTML = "";
  const items = [
    { key:"趣味", val: details.hobby },
    { key:"サークル/部活", val: details.circle },
    { key:"学部/学科/専攻", val: details.dept },
    { key:"学年", val: details.year },
    { key:"資格", val: details.license },
    { key:"一言コメント", val: details.comment }
  ];
  items.forEach(it => {
    const row = document.createElement("div");
    row.className = "detail-row";
    const keyDiv = document.createElement("div");
    keyDiv.className = "detail-key";
    keyDiv.textContent = it.key;
    const valDiv = document.createElement("div");
    valDiv.className = "detail-value";
    valDiv.textContent = it.val || "未設定";
    row.appendChild(keyDiv);
    row.appendChild(valDiv);
    area.appendChild(row);
  });
}

// フォロー・投稿関数（略）
// updateFollowBtn, toggleFollow, startChat, updateStats などは従来通り

function updateFollowBtn(){
  const btn = document.getElementById("followBtn");
  const isFollowing = (follows[myProfile.name]||[]).includes(userProfile.name);
  if(btn) {
    if(isFollowing) {
      btn.textContent = "フォロー中";
      btn.classList.add("following");
    } else {
      btn.textContent = "フォロー";
      btn.classList.remove("following");
    }
  }
}

function toggleFollow(){
  if(!follows[myProfile.name]) follows[myProfile.name] = [];
  const idx = follows[myProfile.name].indexOf(userProfile.name);
  if(idx >= 0) {
    follows[myProfile.name].splice(idx,1);
  } else {
    follows[myProfile.name].push(userProfile.name);
  }
  localStorage.setItem("follows", JSON.stringify(follows));
  updateFollowBtn();
  updateStats();
}

function startChat(){
  window.location.href = `cocochat.html?target=${encodeURIComponent(userProfile.name)}`;
}

function updateStats(){
  const fc = document.getElementById("followingCount");
  const frc = document.getElementById("followerCount");
  const pc = document.getElementById("postCount");
  if(fc) fc.textContent = (follows[userProfile.name]||[]).length;
  let cnt = 0;
  for(let k in follows) {
    if((follows[k]||[]).includes(userProfile.name)) cnt++;
  }
  if(frc) frc.textContent = cnt;
  if(pc) pc.textContent = (userProfile.posts||[]).length;
}

function renderUserPosts(){
  const div = document.getElementById("userPostsDiv");
  if(!div) return;
  div.innerHTML = "";
  const userPosts = userProfile.posts || [];
  if(userPosts.length === 0) {
    div.innerHTML = "<div style='text-align:center; color:var(--muted); margin-top:20px;'>まだ投稿がありません。</div>";
    return;
  }
  userPosts.slice().reverse().forEach(p => {
    const card = document.createElement("div");
    card.className = "post-card";
    const time = new Date(p.time).toLocaleString("ja-JP",{hour12:false});
    card.innerHTML = `
      <div class='post-header'>
        <div class='icon'>${userProfile.avatar}</div>
        <div><div class='user-name'>${userProfile.name}</div><div class='time'>${time}</div></div>
      </div>
      <div class='post-content'>${p.text.replace(/\n/g,"<br>")}</div>
    `;
    div.appendChild(card);
  });
}

// 初期化呼び出し
initProfile();
