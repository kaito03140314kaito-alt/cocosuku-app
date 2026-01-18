from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import firebase_admin
from firebase_admin import credentials, auth, firestore, storage
import os
from datetime import datetime, timezone, timedelta
import uuid
import json
import base64
import google.generativeai as genai
import cloudinary
import cloudinary.uploader
import cloudinary.api

# ---------------------------
# JST設定
# ---------------------------
JST = timezone(timedelta(hours=9))

# ---------------------------
# Gemini API 設定
# ---------------------------
if os.environ.get("GOOGLE_API_KEY"):
    genai.configure(api_key=os.environ.get("GOOGLE_API_KEY"))


# ---------------------------
# Firebase 初期化
# ---------------------------
# ---------------------------
# Firebase 初期化
# ---------------------------
# 環境変数から「生のJSON文字列」を取得、なければローカルファイルを探す
firebase_config_raw = os.environ.get("FIREBASE_CONFIG")
cred = None

if firebase_config_raw:
    try:
        # 文字列を辞書型に変換
        cred_json = json.loads(firebase_config_raw)
        cred = credentials.Certificate(cred_json)
    except Exception as e:
        print(f"Firebase設定読み込みエラー(Env): {e}")

elif os.path.exists("serviceAccountKey.json"):
    try:
        print("serviceAccountKey.json を読み込んでいます...")
        cred = credentials.Certificate("serviceAccountKey.json")
    except Exception as e:
        print(f"Firebase設定読み込みエラー(File): {e}")

if cred:
    try:
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        print("Firebaseの初期化に成功しました！(Credential)")
    except Exception as e:
        print(f"Firebase初期化エラー: {e}")
else:
    # クレデンシャルが見つからない場合は、Application Default Credentials (ADC) を試みる
    # Cloud Functions / Cloud Run 環境ではこちらが動く
    try:
        if not firebase_admin._apps:
            firebase_admin.initialize_app()
        print("Firebaseの初期化に成功しました！(ADC)")
    except Exception as e:
        print(f"Firebase初期化エラー(ADC): {e}")

# dbの作成（初期化が成功していれば動きます）
# dbの作成（初期化が成功していれば動きます）
db = firestore.client()

# ---------------------------
# Cloudinary 設定
# ---------------------------
cloudinary.config(
    cloud_name=os.environ.get("CLOUDINARY_CLOUD_NAME"),
    api_key=os.environ.get("CLOUDINARY_API_KEY"),
    api_secret=os.environ.get("CLOUDINARY_API_SECRET"),
    secure=True
)


# ---------------------------
# Flask アプリ設定
# ---------------------------
app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-this")

# ---------------------------
# トップページ
# ---------------------------
@app.route("/")
def index():
    return redirect(url_for("login"))


# ---------------------------
# ログイン画面
# ---------------------------
@app.route("/login")
def login():
    return render_template("cocologin.html")


# ---------------------------
# ログイン処理
# ---------------------------
@app.route("/login", methods=["POST"])
def login_post():
    email = request.form["email"]
    password = request.form["password"]

    try:
        user = auth.get_user_by_email(email)
        user_ref = db.collection("users").document(user.uid)
        user_doc = user_ref.get()

        if not user_doc.exists:
            flash("ユーザー情報が見つかりません。")
            return redirect(url_for("login"))

        user_data = user_doc.to_dict()

        if user_data.get("password") == password:
            session["user"] = {
                "uid": user.uid,
                "name": user_data.get("name"),
                "email": email
            }
            return redirect(url_for("timeline"))
        else:
            flash("パスワードが間違っています。")
            return redirect(url_for("login"))

    except Exception as e:
        print("ログインエラー:", e)
        flash("メールアドレスが見つかりません。")
        return redirect(url_for("login"))


# ---------------------------
# 新規登録画面
# ---------------------------
@app.route("/register")
def register():
    return render_template("cocoregister.html")


# ---------------------------
# 新規登録処理
# ---------------------------
@app.route("/register", methods=["POST"])
def register_post():
    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]

    try:


        user = auth.create_user(email=email, password=password)

        db.collection("users").document(user.uid).set({
            "name": name,
            "email": email,
            "password": password
        })

        flash("登録が完了しました！ログインしてください。")
        return redirect(url_for("login"))

    except Exception as e:
        print("登録エラー:", e)
        # エラー詳細を表示するように変更（デバッグ用）
        flash(f"登録に失敗しました: {e}")
        return redirect(url_for("register"))


# ---------------------------
# ログアウト
# ---------------------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    flash("ログアウトしました。")
    return redirect(url_for("login"))


# ---------------------------
# 投稿処理（Cloudinary版）
# ---------------------------
@app.route("/post", methods=["POST"])
def post():
    if "user" not in session:
        flash("ログインが必要です")
        return redirect(url_for("login"))

    user = session["user"]
    content = request.form.get("content")
    image = request.files.get("image")

    if not content and not image:
        flash("投稿内容が空です")
        return redirect(url_for("timeline"))

    image_url = None

    # Cloudinary にアップロード
    if image and image.filename != "":
        try:
            # Cloudinaryへアップロード
            upload_result = cloudinary.uploader.upload(image)
            image_url = upload_result["secure_url"]

        except Exception as e:
            print("Cloudinary 画像アップロードエラー:", e)
            flash("画像のアップロードに失敗しました")
            return redirect(url_for("timeline"))

    # Firestore に投稿保存
    post_data = {
        "user_id": user["uid"],
        "user_name": user["name"],
        "content": content,
        "image_url": image_url,
        "created_at": datetime.now(JST),
        "likes": []
    }

    post_ref = db.collection("posts").add(post_data)
    post_id = post_ref[1].id

    # ---------------------------
    # 通知作成 (フォロワー全員に)
    # ---------------------------
    # 自分のフォロワーを取得
    user_ref = db.collection("users").document(user["uid"])
    user_doc = user_ref.get()
    if user_doc.exists:
        followers = user_doc.to_dict().get("followers", [])
        
        # バッチ書き込みで効率化（人数が多い場合は分割が必要だが今回は簡易実装）
        batch = db.batch()
        count = 0
        
        for follower_uid in followers:
            # 自分自身には通知しない（通常含まれないはずだが念のため）
            if follower_uid == user["uid"]:
                continue
                
            notif_ref = db.collection("users").document(follower_uid)\
                          .collection("notifications").document()
            
            notif_data = {
                "type": "new_post",
                "from_uid": user["uid"],
                "from_name": user["name"],
                "from_avatar_url": user_doc.to_dict().get("avatar_url"), # アバターも入れておくと表示が楽
                "post_id": post_id,
                "is_read": False,
                "created_at": datetime.now(JST)
            }
            batch.set(notif_ref, notif_data)
            count += 1
            
            # Firestoreバッチは最大500件まで
            if count >= 400:
                batch.commit()
                batch = db.batch()
                count = 0
        
        if count > 0:
            batch.commit()



    flash("投稿しました！")
    return redirect(url_for("timeline"))


# ---------------------------
# AI炎上チェックAPI
# ---------------------------
@app.route("/api/ai_check", methods=["POST"])
def api_ai_check():
    if "user" not in session:
        return jsonify({"error": "Login required"}), 403

    content = request.form.get("content", "")
    image = request.files.get("image")

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt_parts = []
        prompt_parts.append("""
        あなたはSNSの炎上リスク判定AIです。
        ユーザーが投稿しようとしている内容（テキストおよび画像）を分析し、
        炎上確率（0〜100%）と、その理由を簡潔に答えてください。
        
        出力フォーマットは必ず以下の純粋なJSONのみにしてください。Markdownのコードブロックは不要です。
        {
            "percentage": 30,
            "reason": "攻撃的な表現が含まれています。"
        }
        """)
        
        prompt_parts.append(f"投稿テキスト: {content}")
        
        if image and image.filename != "":
            # 画像データを読み込んでGeminiに渡す
            image_data = image.read()
            image_part = {
                "mime_type": image.content_type,
                "data": image_data
            }
            prompt_parts.append(image_part)
            # 読み込み位置を戻す（後で投稿する場合に備えて...今回はAPIのみ利用なので不要だが念のため）
            image.seek(0)

        response = model.generate_content(prompt_parts)
        text_resp = response.text.replace('```json', '').replace('```', '').strip()
        
        result = json.loads(text_resp)
        return jsonify(result)

    except Exception as e:
        print("AI Check Error:", e)
        return jsonify({"percentage": -1, "reason": "AIチェックに失敗しました"}), 500



# ---------------------------


# -----------------------------------------------------
# ヘルパー: 投稿リスト取得・加工
# -----------------------------------------------------
def fetch_rich_posts(limit=10, start_after=None):
    query = db.collection("posts").order_by(
        "created_at", direction=firestore.Query.DESCENDING
    )
    
    if start_after:
        query = query.start_after(start_after)
        
    query = query.limit(limit)
    
    posts = []
    docs = list(query.stream())
    
    for doc in docs:
        post = doc.to_dict()
        post["id"] = doc.id

        user_id = post.get("user_id")

        # ⭐ 投稿主ユーザー情報を取得（特に avatar_url）
        if user_id:
            user_doc = db.collection("users").document(user_id).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                post["user_avatar_url"] = user_data.get("avatar_url", None)
                post["user_name"] = user_data.get("name", "無名ユーザー")
            else:
                post["user_avatar_url"] = None
                post["user_name"] = "無名ユーザー"
        else:
            post["user_avatar_url"] = None
            post["user_name"] = "無名ユーザー"

        # ⭐ リプライ取得
        # ※ N+1問題になるが、仕様維持のためそのまま
        # 無限スクロールで件数が絞られるので負荷はマシになる
        replies_ref = db.collection("posts").document(doc.id) \
            .collection("replies") \
            .order_by("created_at", direction=firestore.Query.ASCENDING)

        replies = []
        for r in replies_ref.stream():
            rep = r.to_dict()
            rep["id"] = r.id
            replies.append(rep)

        post["replies"] = replies
        post["replies_count"] = len(replies)

        posts.append(post)
        
    return posts


# ---------------------------
# タイムライン表示
# ---------------------------
@app.route("/timeline")
def timeline():
    if "user" not in session:
        flash("ログインが必要です。")
        return redirect(url_for("login"))

    user = session["user"]

    # 初回10件取得
    posts = fetch_rich_posts(limit=10)

    return render_template("cocotimeline.html", user=user, posts=posts)


@app.route("/api/timeline")
def api_timeline():
    if "user" not in session:
        return jsonify({"html": "", "has_next": False}), 403

    user = session["user"]
    last_created_at_str = request.args.get("last_created_at")
    
    start_time = None
    if last_created_at_str:
        try:
            # 文字列からdatetimeオブジェクトへ復元 (フォーマット依存があるため注意)
            # Pythonのstr()形式 'YYYY-MM-DD HH:MM:SS.ffffff+HH:MM' をパース
            # dateutilがない場合、簡易パース
            # ここでは一番確実な「前の最後の投稿ID」を受け取る方式ではなく
            # クライアントから送られた文字列を頑張ってパースする
            # fromisoformatはPython 3.7+で対応だが、タイムゾーン表記によってはコケる
            start_time = datetime.fromisoformat(last_created_at_str)
        except Exception as e:
            print("Date parse error:", e)
            # パース失敗したら続きが取れないので終了
            return jsonify({"html": "", "has_next": False})

    # 次の10件
    new_posts = fetch_rich_posts(limit=10, start_after={"created_at": start_time} if start_time else None)
    
    if not new_posts:
        return jsonify({"html": "", "has_next": False})

    # レンダリングして返す
    # userオブジェクトを渡しておかないと、削除ボタン判定などでエラーになる
    html = render_template("post_items.html", posts=new_posts, user=user)
    
    return jsonify({
        "html": html,
        "has_next": len(new_posts) == 10  # 10件取れたらまだあるかも
    })




# ---------------------------
# いいね
# ---------------------------
@app.route("/like/<post_id>", methods=["POST"])
def like_post(post_id):
    if "user" not in session:
        return "unauthorized", 403

    uid = session["user"]["uid"]
    user_name = session["user"]["name"]

    post_ref = db.collection("posts").document(post_id)
    like_ref = post_ref.collection("likes").document(uid)

    if like_ref.get().exists:
        # いいね解除
        like_ref.delete()
        post_ref.update({"likes_count": firestore.Increment(-1)})
        return {"liked": False}

    else:
        # いいね追加（通知向けの情報を保存）
        like_ref.set({
            "user_id": uid,
            "user_name": user_name,
            "created_at": datetime.now(JST)
        })
        post_ref.update({"likes_count": firestore.Increment(1)})

        return {"liked": True}



# ---------------------------
# リプライ
# ---------------------------
@app.route("/reply/<post_id>", methods=["POST"])
def reply_post(post_id):
    if "user" not in session:
        return redirect("/login")

    content = request.form.get("reply")
    user = session["user"]

    if not content:
        flash("返信内容が空です。")
        return redirect("/timeline")

    post_ref = db.collection("posts").document(post_id)

    # replyを追加
    post_ref.collection("replies").add({
        "user_id": user["uid"],
        "user_name": user["name"],
        "content": content,
        "created_at": datetime.now(JST),
    })

    # reply数を更新
    post_ref.update({
        "replies_count": firestore.Increment(1)
    })

    flash("返信しました！")
    return redirect("/timeline")



# ---------------------------
# 投稿削除
# ---------------------------
@app.route("/post/delete/<post_id>", methods=["POST"])
def delete_post(post_id):
    if "user" not in session:
        return redirect("/login")

    post_ref = db.collection("posts").document(post_id)
    post_doc = post_ref.get()

    if not post_doc.exists:
        flash("投稿が見つかりません")
        return redirect("/timeline")

    post = post_doc.to_dict()

    # 投稿主チェック
    if post.get("user_id") != session["user"]["uid"]:
        flash("削除権限がありません")
        return redirect("/timeline")

    # Cloudinary の画像削除
    if post.get("image_url"):
        try:
            # 画像URLからpublic_idを抽出して削除を試みる
            # URL例: https://res.cloudinary.com/demo/image/upload/v1570979139/sample.jpg
            # 後ろの filename (拡張子除く) が public_id のケースが多いが、
            # フォルダ構成などにより異なるため、簡易実装として
            # URLの最後のパーツの拡張子を除いたものを public_id と仮定する。
            # 正確に行うにはアップロード時に public_id をDBに保存すべき。
            
            image_url = post.get("image_url")
            # / で分割した最後を取得
            filename = image_url.split("/")[-1]
            # . で分割した最初（拡張子削除）を取得
            public_id = filename.rsplit(".", 1)[0]
            
            cloudinary.uploader.destroy(public_id)
            print(f"Cloudinary image deleted: {public_id}")
            
        except Exception as e:
            print("Cloudinary削除エラー:", e)

    # リプライ削除
    for reply in post_ref.collection("replies").stream():
        reply.reference.delete()

    # いいね削除
    for like in post_ref.collection("likes").stream():
        like.reference.delete()

    # 投稿削除
    post_ref.delete()

    flash("投稿を削除しました")
    return redirect("/timeline")


# -------------------
# リプライ削除
# -------------------
@app.route("/reply/delete/<post_id>/<reply_id>", methods=["POST"])
def delete_reply(post_id, reply_id):
    if "user" not in session:
        return redirect("/login")

    uid = session["user"]["uid"]

    reply_ref = db.collection("posts").document(post_id).collection("replies").document(reply_id)
    reply_doc = reply_ref.get()

    if not reply_doc.exists:
        flash("返信が見つかりません")
        return redirect("/timeline")

    if reply_doc.to_dict().get("user_id") != uid:
        flash("削除権限がありません")
        return redirect("/timeline")

    # 削除
    reply_ref.delete()

    # 親投稿の件数を減らす
    db.collection("posts").document(post_id).update({
        "replies_count": firestore.Increment(-1)
    })

    flash("リプライを削除しました")
    return redirect("/timeline")


# ---------------------------
# プロフィール画面
# ---------------------------
@app.route("/profile")
def profile():
    if "user" not in session:
        flash("ログインが必要です")
        return redirect(url_for("login"))

    uid = session["user"]["uid"]

    # ユーザーデータ取得
    user_ref = db.collection("users").document(uid)
    doc = user_ref.get()

    if not doc.exists:
        flash("ユーザーデータがありません")
        return redirect(url_for("timeline"))

    user_data = doc.to_dict()

    # followers / following のデフォルト値
    following = user_data.get("following", [])
    followers = user_data.get("followers", [])

    # 空項目補完
    for key in ["bio", "hobby", "circle", "course", "grade",
                "qualification", "comment", "avatar_url"]:
        user_data.setdefault(key, "")

    # 投稿取得
    posts_ref = db.collection("posts")\
        .where("user_id", "==", uid)\
        .order_by("created_at", direction=firestore.Query.DESCENDING)

    posts_raw = list(posts_ref.stream())

    posts = []
    for p in posts_raw:
        item = p.to_dict()
        item["id"] = p.id

        # リプライ取得
        replies_ref = db.collection("posts").document(p.id).collection("replies")
        replies = []
        for r in replies_ref.stream():
            reply_data = r.to_dict()
            reply_data["id"] = r.id
            replies.append(reply_data)

        item["replies"] = replies
        item["replies_count"] = len(replies)

        posts.append(item)

    return render_template(
        "cocoprofile.html",
        user=user_data,
        posts=posts,
        post_count=len(posts),

        follower_count=len(followers),
        following_count=len(following)
    )



# ---------------------------
# プロフィール更新
# ---------------------------
@app.route("/profile/update", methods=["POST"])
def profile_update():
    if "user" not in session:
        flash("ログインが必要です")
        return redirect(url_for("login"))

    uid = session["user"]["uid"]
    user_ref = db.collection("users").document(uid)

    # フォーム入力データ
    data = {
        "name": request.form.get("name"),
        "bio": request.form.get("bio"),
        "hobby": request.form.get("hobby"),
        "circle": request.form.get("circle"),
        "course": request.form.get("course"),
        "grade": request.form.get("grade"),
        "qualification": request.form.get("qualification"),
        "comment": request.form.get("comment"),
    }

    file = request.files.get("avatar")
    if file and file.filename != "":
        try:
            # Cloudinary にアップロード
            upload_result = cloudinary.uploader.upload(file)
            data["avatar_url"] = upload_result["secure_url"]
        except Exception as e:
            print("Avatar upload error:", e)
            flash("アバターのアップロードに失敗しました")

    # Firestore 更新
    user_ref.update(data)

    flash("プロフィールを更新しました！")
    return redirect(url_for("profile"))

# ---------------------------
# 他ユーザープロフィール画面
# ---------------------------
@app.route("/user/<uid>")
def other_profile(uid):
    if "user" not in session:
        flash("ログインが必要です。")
        return redirect(url_for("login"))

    current_user = session["user"]

    # ▼ 対象ユーザー情報を取得
    user_ref = db.collection("users").document(uid).get()
    if not user_ref.exists:
        flash("ユーザーが見つかりません。")
        return redirect(url_for("timeline"))

    user_data = user_ref.to_dict()
    user_data["uid"] = uid

    # ▼ 対象ユーザーの投稿一覧を取得（新しい順）
    posts_ref = db.collection("posts") \
        .where("user_id", "==", uid) \
        .order_by("created_at", direction=firestore.Query.DESCENDING)

    posts = []
    for doc in posts_ref.stream():
        post = doc.to_dict()
        post["id"] = doc.id

        # 投稿者情報（念のため）
        post["user_avatar_url"] = user_data.get("avatar_url")
        post["user_name"] = user_data.get("name", "無名ユーザー")

        # ▼ リプライ取得
        replies_ref = db.collection("posts").document(doc.id) \
            .collection("replies") \
            .order_by("created_at", direction=firestore.Query.ASCENDING)

        replies = []
        for r in replies_ref.stream():
            rep = r.to_dict()
            rep["id"] = r.id
            replies.append(rep)

        post["replies"] = replies
        post["replies_count"] = len(replies)

    # ▼ フォロー・フォロワー（存在しない場合は 0 に）
    following = user_data.get("following", [])
    followers = user_data.get("followers", [])
    
    is_following = current_user["uid"] in followers

    return render_template(
        "cocootherprofile.html",
        profile=user_data,
        posts=posts,
        following_count=len(following),
        follower_count=len(followers),
        post_count=len(posts),
        current_user=current_user,
        is_following=is_following
    )


# ---------------------------
# 設定ページ
# ---------------------------
@app.route("/settings")
def settings_page():
    if "user" not in session:
        return redirect(url_for("login"))
    user = session["user"]
    return render_template("cocosettings.html", user=user)


@app.route("/user/<uid>/following")
def following_list(uid):
    if "user" not in session:
        return redirect(url_for("login"))

    user_ref = db.collection("users").document(uid).get()
    if not user_ref.exists:
        flash("ユーザーが見つかりません")
        return redirect(url_for("timeline"))

    following_uids = user_ref.to_dict().get("following", [])
    
    users_data = []
    if following_uids:
        # db.get_all を使用して一括取得
        refs = [db.collection("users").document(u) for u in following_uids]
        docs = db.get_all(refs)
        
        for doc in docs:
            if doc.exists:
                d = doc.to_dict()
                d["uid"] = doc.id
                users_data.append(d)

    return render_template("cocofollow_list.html", title="フォロー中", users=users_data)


@app.route("/user/<uid>/followers")
def followers_list(uid):
    if "user" not in session:
        return redirect(url_for("login"))

    user_ref = db.collection("users").document(uid).get()
    if not user_ref.exists:
        flash("ユーザーが見つかりません")
        return redirect(url_for("timeline"))

    follower_uids = user_ref.to_dict().get("followers", [])
    
    users_data = []
    if follower_uids:
        refs = [db.collection("users").document(u) for u in follower_uids]
        docs = db.get_all(refs)
        
        for doc in docs:
            if doc.exists:
                d = doc.to_dict()
                d["uid"] = doc.id
                users_data.append(d)

    return render_template("cocofollow_list.html", title="フォロワー", users=users_data)


# ---------------------------
# 規約・ヘルプなど (Static Pages)
# ---------------------------
@app.route("/kiyaku")
def kiyaku():
    if "user" not in session: return redirect(url_for("login"))
    user = session["user"]
    return render_template("cocokiyaku.html", user=user)

@app.route("/privacy")
def privacy():
    if "user" not in session: return redirect(url_for("login"))
    user = session["user"]
    return render_template("cocoprivate.html", user=user)

@app.route("/help")
def help_page():
    if "user" not in session: return redirect(url_for("login"))
    user = session["user"]
    return render_template("cocohelp.html", user=user)


# ---------------------------
# パスワードリセット (メール送信)
# ---------------------------
@app.route("/api/reset_password_request", methods=["POST"])
def reset_password_request():
    if "user" not in session:
        return jsonify({"error": "Login required"}), 403
    
    user = session["user"]
    email = user["email"]
    
    try:
        # Firebase Authでパスワードリセットメールを送信
        # generate_password_reset_link はリンク生成のみでメール送信しない場合が多いが
        # Admin SDKのバージョンによってはLink生成のみ。
        # クライアントSDKなら sendPasswordResetEmail だが、Admin SDKには直接メール送る機能が弱い場合がある。
        # ここでは「リンクを生成して、本来はSendGrid等で送る」のが定石だが、
        # 簡易的に「リンクを生成してブラウザ（コンソール）に表示」もしくはお茶を濁す実装になりがち。
        # しかしFirebase Authenticationには "generate_password_reset_link" がある。
        
        link = auth.generate_password_reset_link(email)
        
        # 本来はメール送信サービス(SendGrid等)で送るべきだが、
        # ここでは開発用として「成功」だけ返し、実際には送られない（リンク生成のみ）という罠がある。
        # ★重要: Admin SDKで「メールを送る」直接的なメソッドはない。リンクを作るだけ。
        # ユーザー要望は「機能を追加してほしい」なので、
        # 厳密には「メールサーバー(SMTP)の実装」が必要になる。レンダーだと面倒。
        # 
        # 代替案: フロントエンド(JS)のFirebase Client SDKを使えば sendPasswordResetEmail() が一発で使える。
        # しかし今はバックエンド主体の実装になっている。
        # 
        # 今回は妥協案として、「本来はメール送信処理が必要ですが、簡易実装としてリンク発行成功＝OK」とするか、
        # ちゃんと Client SDK を導入するか。
        # ユーザーは「Renderで無料」を求めているので、SMTP設定などはハードルが高い。
        # 
        # → ここでは「リンク生成」まで行い、
        # 「（開発環境用）コンソールにリンクを表示しました。本来はメール送信APIが必要です」とするのが誠実。
        # あるいは、一番簡単なのはフロントエンドで firebase.auth().sendPasswordResetEmail() を呼ぶこと。
        # だがフロントにFirebase configが露出していない...
        # 
        # いや、待てよ。generate_password_reset_link で生成したリンクを、
        # アプリ側でメール送信しなくても、ユーザーに「このリンクからリセットして」と表示するのはセキュリティ的に微妙（他人がリクエストしたら見えちゃう）。
        # 
        # ★一番いいのは「Client SDKの導入」だが、今回は大掛かりになる。
        # ここでは、「サーバーログにリンクを出すので、自分でクリックしてね」という
        # "開発者モード" として実装し、ユーザーにはその旨伝えるのが現実的。
        
        print(f"PASSWORD RESET LINK for {email}: {link}")
        return jsonify({"message": "本来はメール送信されますが、現在はサーバーログにリンクを表示しています。"})

    except Exception as e:
        print(f"Password Reset Error: {e}")
        return jsonify({"error": str(e)}), 500
    
@app.route("/follow/<uid>")
def toggle_follow(uid):
    if "user" not in session:
        return redirect(url_for("login"))

    current_uid = session["user"]["uid"]

    # 自分フォロー禁止
    if current_uid == uid:
        return redirect(url_for("other_profile", uid=uid))

    current_ref = db.collection("users").document(current_uid)
    target_ref = db.collection("users").document(uid)

    current_user = current_ref.get().to_dict()
    target_user = target_ref.get().to_dict()

    # 配列が無い場合の初期化
    current_user.setdefault("following", [])
    target_user.setdefault("followers", [])

    following = current_user["following"]
    followers = target_user["followers"]

    if uid in following:
        # 解除
        following.remove(uid)
        followers.remove(current_uid)
    else:
        # フォロー
        following.append(uid)
        followers.append(current_uid)

    # Firestore 更新
    current_ref.update({"following": following})
    target_ref.update({"followers": followers})

    return redirect(url_for("other_profile", uid=uid))



@app.route("/search")
def search_page():
    if "user" not in session:
        return redirect(url_for("login"))

    query = request.args.get("q", "").strip()

    user_results = []
    post_results = []

    if query:
        # ===== ユーザー検索 =====
        for doc in db.collection("users").stream():
            data = doc.to_dict()
            if query.lower() in data.get("name", "").lower():
                user_results.append({
                    "uid": doc.id,
                    "name": data.get("name"),
                    "bio": data.get("bio", ""),
                    "avatar_url": data.get("avatar_url")
                })

        # ===== 投稿検索 =====
        for doc in db.collection("posts").stream():
            post = doc.to_dict()
            content = post.get("content", "")

            if query.lower() in content.lower():
                user_id = post.get("user_id")

                avatar_url = None
                user_name = post.get("user_name", "不明")

                if user_id:
                    user_doc = db.collection("users").document(user_id).get()
                    if user_doc.exists:
                        u = user_doc.to_dict()
                        avatar_url = u.get("avatar_url")
                        user_name = u.get("name", user_name)

                post_results.append({
                    "post_id": doc.id,
                    "content": content,
                    "user_name": user_name,
                    "user_avatar_url": avatar_url
                })

    return render_template(
        "cocosearch.html",
        query=query,
        user_results=user_results,
        post_results=post_results
    )

@app.route("/search/api")
def search_api():
    if "user" not in session:
        return {"users": [], "posts": []}

    query = request.args.get("q", "").strip().lower()
    user_results = []
    post_results = []

    if not query:
        return {"users": [], "posts": []}

    # ===== ユーザー検索 =====
    for doc in db.collection("users").stream():
        data = doc.to_dict()
        if query in data.get("name", "").lower() or query in data.get("bio", "").lower():
            user_results.append({
                "uid": doc.id,
                "name": data.get("name"),
                "bio": data.get("bio", ""),
                "avatar_url": data.get("avatar_url")
            })

    # ===== 投稿検索 =====
    for doc in db.collection("posts").stream():
        post = doc.to_dict()
        if query in post.get("content", "").lower():
            post_results.append({
                "id": doc.id,
                "content": post.get("content"),
                "user_name": post.get("user_name"),
                "user_avatar_url": post.get("user_avatar_url")
            })

    return {
        "users": user_results,
        "posts": post_results
    }
    

@app.route("/dm")
def dm_list():
    if "user" not in session:
        return redirect(url_for("login"))

    uid = session["user"]["uid"]

    rooms_ref = db.collection("dm_rooms").where("users", "array_contains", uid)
    rooms = []

    for r in rooms_ref.stream():
        room = r.to_dict()
        room["room_id"] = r.id

        other_uid = [u for u in room["users"] if u != uid][0]
        other_doc = db.collection("users").document(other_uid).get()
        other_data = other_doc.to_dict() if other_doc.exists else {"name": "不明"}
        other_data["uid"] = other_uid

        room["other_user"] = other_data

        # ▼ 最後のメッセージを取得
        last_msg_ref = (
            db.collection("dm_rooms")
              .document(r.id)
              .collection("messages")
              .order_by("created_at", direction=firestore.Query.DESCENDING)
              .limit(1)
        )

        last_msgs = list(last_msg_ref.stream())
        if last_msgs:
            room["last_message"] = last_msgs[0].to_dict().get("text")
        else:
            room["last_message"] = ""

        rooms.append(room)

    return render_template(
        "cocochat.html",
        rooms=rooms,
        enter_chat=False
    )



@app.route("/dm_redirect")
def dm():
    return redirect(url_for("dm_list"))

@app.route("/dm/start/<other_uid>")
def dm_start(other_uid):
    if "user" not in session:
        return redirect(url_for("login"))

    current_uid = session["user"]["uid"]

    if current_uid == other_uid:
        return redirect(url_for("other_profile", uid=other_uid))

    room_id = "_".join(sorted([current_uid, other_uid]))

    room_ref = db.collection("dm_rooms").document(room_id)
    if not room_ref.get().exists:
        room_ref.set({
            "users": [current_uid, other_uid],
            "updated_at": datetime.now(JST)
        })

    return redirect(url_for("dm_chat", other_uid=other_uid))


@app.route("/dm/chat/<other_uid>")
def dm_chat(other_uid):
    if "user" not in session:
        return redirect(url_for("login"))

    current_uid = session["user"]["uid"]

    room_id = "_".join(sorted([current_uid, other_uid]))

    # ルーム作成
    room_ref = db.collection("dm_rooms").document(room_id)
    if not room_ref.get().exists:
        room_ref.set({
            "users": [current_uid, other_uid],
            "updated_at": datetime.now(JST)
        })

    # 相手情報
    other_doc = db.collection("users").document(other_uid).get()
    if not other_doc.exists:
        flash("相手ユーザーが見つかりません。")
        return redirect(url_for("timeline"))

    other_data = other_doc.to_dict()
    other_data["uid"] = other_uid

    # チャット画面へ遷移（JS に情報を渡す）
    return render_template(
        "cocochat.html",
        room_id=room_id,
        other=other_data,
        current_uid=current_uid,
        enter_chat=True     # ← これが超重要
    )

    
@app.route("/dm/messages/<room_id>")
def dm_messages(room_id):

    try:
        # Firestore パス修正（dm_room）
        messages_ref = (
            db.collection("dm_rooms")
              .document(room_id)
              .collection("messages")
              .order_by("created_at")
        )

        docs = messages_ref.stream()

        messages = []
        for doc in docs:
            d = doc.to_dict()
            messages.append({
                "text": d.get("text"),
                "from_uid": d.get("from_uid"),
                "timestamp": d.get("created_at")  # Timestamp
            })

        return jsonify({"messages": messages})

    except Exception as e:
        print("DM FETCH ERROR:", e)
        return jsonify({"error": str(e)}), 500



@app.route("/dm/send/<room_id>", methods=["POST"])
def dm_send(room_id):
    if "user" not in session:
        return {"success": False}

    text = request.json.get("text", "").strip()
    if not text:
        return {"success": False}

    uid = session["user"]["uid"]

    msg_ref = db.collection("dm_rooms").document(room_id)\
        .collection("messages")

    msg_ref.add({
        "from_uid": uid,
        "text": text,
        "created_at": datetime.now(JST)
    })

    # ルーム更新
    db.collection("dm_rooms").document(room_id).update({
        "updated_at": datetime.now(JST)
    })

    return {"success": True}


@app.route("/dm/to/<uid>")
def dm_to(uid):
    if "user" not in session:
        return redirect(url_for("login"))

    # 今はとりあえずDMページに遷移するだけ
    # 将来 Firestore の DM ID でスレッド管理できる
    session["dm_target"] = uid
    return redirect(url_for("dm"))


@app.post("/api/check-id")
def api_check_id():
    data = request.get_json()
    entered_id = data.get("id", "").strip()

    current_uid = session.get("user", {}).get("uid")

    classes_ref = db.collection("classes").stream()

    for doc in classes_ref:
        class_data = doc.to_dict()
        class_id = doc.id

        if class_data.get("teacher_id") == entered_id:
            return jsonify({
                "ok": True,
                "role": "teacher",
                "class_id": class_id,
                "uid": current_uid
            })

        if class_data.get("student_id") == entered_id:
            return jsonify({
                "ok": True,
                "role": "student",
                "class_id": class_id,
                "uid": current_uid
            })

    return jsonify({"ok": False})



@app.get("/calendar/<class_id>")
def calendar_page(class_id):
    role = request.args.get("role", "student")
    uid = session.get("user", {}).get("uid", "")

    return render_template(
        "cococalendar.html",
        class_id=class_id,
        role=role,
        uid=uid
    )




# --------------------------------------
# GET /api/events?class_id=xxx&role=student&uid=123
# --------------------------------------
@app.get("/api/events")
def get_events():
    class_id = request.args.get("class_id")
    role = request.args.get("role")     
    uid = request.args.get("uid")       

    events_ref = db.collection("calendar_events")\
                    .document(class_id)\
                    .collection("events")

    docs = events_ref.stream()
    events = []

    for d in docs:
        ev = d.to_dict()
        ev["id"] = d.id

        # 教師
        if role == "teacher":
            if ev["role"] == "teacher":
                events.append(ev)

        # 学生
        elif role == "student":
            if ev["role"] == "teacher":
                events.append(ev)
            elif ev["role"] == "student" and ev.get("uid") == uid:
                events.append(ev)

    return jsonify(events)



# --------------------------------------
# POST /api/events
# --------------------------------------
@app.post("/api/events")
def add_event():
    data = request.get_json()

    class_id = data.get("class_id")
    role = data.get("role")
    uid = data.get("uid")
    date = data.get("date")
    time = data.get("time")
    title = data.get("title")
    memo = data.get("memo")

    new_event = {
        "date": date,
        "time": time,
        "title": title,
        "memo": memo,
        "role": role
    }

    if role == "student":
        new_event["uid"] = uid

    events_ref = db.collection("calendar_events")\
                    .document(class_id)\
                    .collection("events")

    doc_ref = events_ref.document()
    doc_ref.set(new_event)

    return jsonify({"ok": True, "id": doc_ref.id})



# --------------------------------------
# DELETE /api/events
# --------------------------------------
@app.delete("/api/events")
def delete_event():
    data = request.get_json()
    class_id = data.get("class_id")
    event_id = data.get("id")
    role = data.get("role")
    uid = data.get("uid")

    event_ref = db.collection("calendar_events")\
                   .document(class_id)\
                   .collection("events")\
                   .document(event_id)

    doc = event_ref.get()
    if not doc.exists:
        return jsonify({"ok": False})

    ev = doc.to_dict()

    # 教師の削除権限
    if role == "teacher":
        if ev["role"] != "teacher":
            return jsonify({"ok": False, "msg": "教師イベント以外は削除不可"})

    # 学生の削除権限
    elif role == "student":
        if ev["role"] != "student" or ev.get("uid") != uid:
            return jsonify({"ok": False, "msg": "自分の予定以外は削除不可"})

    event_ref.delete()
    return jsonify({"ok": True})



@app.route("/calendar/password")
def calendar_password():
    return render_template("password.html")

@app.route("/calendar/password", methods=["POST"])
def calendar_password_post():
    entered_id = request.form.get("calendar_id")

    # ここでバリデーションするなら処理を書く

    return redirect(url_for("calendar_page"))


# 後で実装
@app.route("/settings")
def settings():
    return render_template("cocosettings.html")


@app.route("/notifications")
def notifications():
    if "user" not in session:
        return redirect(url_for("login"))

    uid = session["user"]["uid"]

    # 通知を取得（新しい順）
    notif_ref = db.collection("users").document(uid)\
                  .collection("notifications")\
                  .order_by("created_at", direction=firestore.Query.DESCENDING)\
                  .limit(50)

    docs = notif_ref.stream()
    
    notifications = []
    for doc in docs:
        n = doc.to_dict()
        n["id"] = doc.id
        notifications.append(n)

    return render_template("coconotifications.html", notifications=notifications)


# ---------------------------
# Flask実行
# ---------------------------
if __name__ == "__main__":
    # Renderで動かすために port を 10000、host を 0.0.0.0 に固定します
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)




