function previewImage(event) {
    const img = document.getElementById("postImagePreview");
    img.src = URL.createObjectURL(event.target.files[0]);
    img.style.display = "block";
}

function openModal() {
    document.getElementById("modalBg").style.display = "flex";
}

function closeModal() {
    document.getElementById("modalBg").style.display = "none";
}

function openReplyModal(postId) {
    const modal = document.getElementById("replyModal");
    modal.style.display = "flex";

    // replyForm の action を更新
    const replyForm = document.getElementById("replyForm");
    replyForm.action = `/reply/${postId}`;
}

function closeReplyModal() {
    document.getElementById("replyModal").style.display = "none";
}

function toggleReplies(postId) {
    const hiddenBlock = document.getElementById(`hidden-replies-${postId}`);
    const toggleBtn = document.getElementById(`toggle-btn-${postId}`);

    if (hiddenBlock.style.display === "none") {
        hiddenBlock.style.display = "block";
        toggleBtn.style.display = "none";
    } else {
        hiddenBlock.style.display = "none";
        toggleBtn.style.display = "block";
    }
}

function confirmDeletePost(postId) {
    if (confirm("本当に削除しますか？")) {
        // OK → 削除用フォームを動的に作成して送信
        const form = document.createElement("form");
        form.method = "POST";
        form.action = `/post/delete/${postId}`;
        document.body.appendChild(form);
        form.submit();
    }
}



