import { initializeApp } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-app.js";
import { getAuth, signInAnonymously, signInWithCustomToken } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-auth.js";
import { getFirestore, setLogLevel } from "https://www.gstatic.com/firebasejs/11.6.1/firebase-firestore.js";

setLogLevel('Debug');
const appId = typeof __app_id !== 'undefined' ? __app_id : 'default-app-id';
const firebaseConfig = JSON.parse(typeof __firebase_config !== 'undefined' ? __firebase_config : '{}');

let app, db, auth;

(async () => {
  try {
    if (Object.keys(firebaseConfig).length > 0) {
      app = initializeApp(firebaseConfig);
      db = getFirestore(app);
      auth = getAuth(app);

      if (typeof __initial_auth_token !== 'undefined') {
        await signInWithCustomToken(auth, __initial_auth_token);
      } else {
        await signInAnonymously(auth);
      }
      console.log("Firebase/Auth setup complete. User ID:", auth.currentUser?.uid || 'N/A');
    } else {
      console.warn("Firebase config not available. Running in simulation mode.");
    }
  } catch (e) {
    console.error("Firebase setup failed:", e);
  }
})();

// --- ページ操作関数 ---
window.goTimeline = function () {
  window.location.href = "cocotimeline.html";
};

window.handleNavigation = function (destination) {
  console.log(`${destination} への遷移をシミュレートします。`);
};

// --- ログアウトモーダル ---
window.openLogoutModal = function () {
  document.getElementById("logoutModal").style.display = "flex";
};

window.closeLogoutModal = function () {
  document.getElementById("logoutModal").style.display = "none";
};

window.performLogout = function () {
  console.log("ログアウト処理を実行しました。");
  window.location.href = "cocologin.html";
  window.closeLogoutModal();
};
