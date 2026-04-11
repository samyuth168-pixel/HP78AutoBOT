# =============================
# PRO AI Telegram Photo Editor Bot (STABLE FINAL VERSION)
# FIXED FOR RENDER + REAL AI (Replicate)
# =============================

import os
import time
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")

# =============================
# UPLOAD IMAGE TO PUBLIC URL
# =============================

def upload_image(file_path):
    with open(file_path, "rb") as f:
        response = requests.post("https://0x0.st", files={"file": f})
    return response.text.strip()

# =============================
# REAL AI (Replicate)
# GFPGAN / Real-ESRGAN STYLE
# =============================

REPLICATE_URL = "https://api.replicate.com/v1/predictions"

headers = {
    "Authorization": f"Token {REPLICATE_API_TOKEN}",
    "Content-Type": "application/json"
}

async def run_ai_model(image_path):
    try:
        image_url = upload_image(image_path)

        headers = {
            "Authorization": f"Token {REPLICATE_API_TOKEN}",
            "Content-Type": "application/json"
        }

        payload = {
            "version": "tencentarc/gfpgan",
            "input": {
                "img": image_url,
                "version": "1.4",
                "scale": 2
            }
        }

        r = requests.post(
            "https://api.replicate.com/v1/predictions",
            json=payload,
            headers=headers
        )

        if r.status_code != 201:
            print("AI ERROR:", r.text)
            return image_path

        prediction = r.json()
        get_url = prediction["urls"]["get"]

        for _ in range(30):
            res = requests.get(get_url, headers=headers).json()

            if res["status"] == "succeeded":
                output = res["output"]
                if isinstance(output, list):
                    output = output[0]

                img = requests.get(output).content

                out_path = image_path.replace("input", "output")
                with open(out_path, "wb") as f:
                    f.write(img)

                return out_path

            if res["status"] == "failed":
                print("AI failed")
                return image_path

            time.sleep(2)

        return image_path

    except Exception as e:
        print("AI ERROR:", e)
        return image_path
        
# =============================
# TELEGRAM BOT UI
# =============================

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("✨ AI Beauty Enhance", callback_data="ai")],
        [InlineKeyboardButton("⚡ Enhance Quality", callback_data="ai")],
        [InlineKeyboardButton("🎭 Style AI", callback_data="ai")]
    ])

# =============================
# BOT HANDLERS
# =============================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me a photo 📸 / ផ្ញើរូបភាព")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = update.message.photo[-1]
    file = await photo.get_file()

    path = f"input_{update.message.chat_id}.jpg"
    await file.download_to_drive(path)

    context.user_data["photo"] = path

    await update.message.reply_text(
        "Choose AI enhancement:",
        reply_markup=menu()
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    photo_path = context.user_data.get("photo")

    if not photo_path:
        await query.message.reply_text("Please send photo first 📸")
        return

    await query.message.reply_text("Processing AI... ⏳")

    output = await run_ai_model(photo_path)

    await query.message.reply_photo(photo=open(output, "rb"))

# =============================
# MAIN
# =============================

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(button))

    print("🔥 AI Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()

# =============================
# REQUIREMENTS.txt
# =============================
# python-telegram-bot==20.7
# requests

# =============================
# ENV VARIABLES (RENDER)
# =============================
# BOT_TOKEN=your_token
# REPLICATE_API_TOKEN=your_replicate_key
