let timer = null;

function liveSearch(keyword) {
  clearTimeout(timer);

  timer = setTimeout(() => {
    if (!keyword.trim()) {
      document.getElementById("results").innerHTML =
        `<div class="no-results">検索ワードを入力してください</div>`;
      return;
    }

    fetch(`/search/api?q=${encodeURIComponent(keyword)}`)
      .then(res => res.json())
      .then(data => renderResults(data));
  }, 250); // ← 入力が止まって250ms後に検索（負荷軽減）
}

function renderResults(data) {
  const results = document.getElementById("results");
  results.innerHTML = "";

  // ===== ユーザー =====
  results.innerHTML += `<div class="results-header">ユーザー</div>`;
  if (data.users.length === 0) {
    results.innerHTML += `<div class="no-results">ユーザーなし</div>`;
  } else {
    data.users.forEach(u => {
      results.innerHTML += `
        <div class="search-result" onclick="location.href='/user/${u.uid}'">
          <div class="result-avatar">
            <img src="${u.avatar_url || '/static/image/default.png'}">
          </div>
          <div class="result-body">
            <div class="result-name">${u.name}</div>
            <div class="result-meta">${u.bio || ""}</div>
          </div>
        </div>
      `;
    });
  }

  // ===== 投稿 =====
  results.innerHTML += `<div class="results-header">投稿</div>`;
  if (data.posts.length === 0) {
    results.innerHTML += `<div class="no-results">投稿なし</div>`;
  } else {
    data.posts.forEach(p => {
      results.innerHTML += `
        <div class="search-result">
          <div class="result-avatar">
            <img src="${p.user_avatar_url || '/static/image/default.png'}">
          </div>
          <div class="result-body">
            <div class="result-name">${p.user_name}</div>
            <div class="result-content">${p.content}</div>
          </div>
        </div>
      `;
    });
  }
}
