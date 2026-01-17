
// プロフィール編集フォームを開く
function showEditForm() {
    document.getElementById("profileDisplay").style.display = "none";
    document.getElementById("profileEdit").style.display = "block";
}

// 編集をキャンセル
function cancelEdit() {
    document.getElementById("profileEdit").style.display = "none";
    document.getElementById("profileDisplay").style.display = "block";
}

// リプライの開閉
function toggleReplies(postId) {
    const hidden = document.getElementById(`hidden-replies-${postId}`);
    const toggleBtn = document.getElementById(`toggle-btn-${postId}`);

    if (!hidden) return;

    if (hidden.style.display === "none") {
        hidden.style.display = "block";
        if (toggleBtn) toggleBtn.style.display = "none";
    } else {
        hidden.style.display = "none";
        if (toggleBtn) toggleBtn.style.display = "block";
    }
}



