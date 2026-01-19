# 次回（明日）やることメモ

Firebase Firestoreが有料プラン必須のリージョンだったため、無料で使える「Realtime Database」へ移行します。

## 1. Firebaseコンソールでの作業
- [ ] **Realtime Databaseの作成**
    - 左メニュー「Build」→「Realtime Database」を選択
    - 「データベースを作成」をクリック
    - ロケーション: 米国 (us-central1) など、デフォルトでOK
    - セキュリティルール: 「本番環境モードで開始」または「テストモード」を選択して有効化

## 2. コードの修正作業 (AI担当)
- [ ] **app.py の書き換え**
    - `firestore` ライブラリの使用をやめる
    - `firebase_admin.db` を使って Realtime Database に読み書きするように変更する
    - 対象: ユーザー保存、投稿保存、タイムライン取得、通知などすべて

## 3. 環境変数の設定
- [ ] **DATABASE_URL の追加**
    - Realtime Databaseを作成するとURL (例: `https://cocosuku-machan-default-rtdb.firebaseio.com/`) が発行されます。
    - これを環境変数 `FIREBASE_DATABASE_URL` （またはコード内に直接）設定する必要があります。
