// ==========================
// cocoprofile.js（Flask版：必要部分のみ）
// ==========================

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
