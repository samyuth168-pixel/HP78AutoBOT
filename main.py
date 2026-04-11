import os
import logging
import requests

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ======================
# CONFIG
# ======================
BOT_TOKEN = os.getenv("BOT_TOKEN")
MANUS_API_KEY = os.getenv("MANUS_API_KEY")

logging.basicConfig(level=logging.INFO)

# ======================
# STATE STORAGE
# ======================
user_state = {}
user_style = {}

STATE_MENU = "menu"
STATE_WAIT_STYLE = "wait_style"
STATE_WAIT_TARGET = "wait_target"

# ======================
# UI MENU
# ======================
menu_kb = ReplyKeyboardMarkup(
    [["🖼 Sample Enhance", "✨ New Enhance"]],
    resize_keyboard=True
)

# ======================
# START
# ======================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text if update.message else None
    photo = update.message.photo if update.message else None

    if user_id not in user_state:
        user_state[user_id] = STATE_MENU

    state = user_state[user_id]

    # MENU
    if text == "🖼 Sample Enhance":
        user_state[user_id] = STATE_WAIT_STYLE
        await update.message.reply_text("📤 Send 1 STYLE photo")
        return

    if text == "✨ New Enhance":
        user_state[user_id] = STATE_WAIT_TARGET
        user_style[user_id] = None
        await update.message.reply_text("📤 Send photo(s) to enhance")
        return

    # STYLE PHOTO
    if state == STATE_WAIT_STYLE:
        if photo:
            user_style[user_id] = photo[-1].file_id
            user_state[user_id] = STATE_WAIT_TARGET
            await update.message.reply_text("✅ Style saved! Now send target photos.")
        else:
            await update.message.reply_text("❌ Send a photo only.")
        return

    # TARGET PHOTO
    if state == STATE_WAIT_TARGET:
        if photo:
            await update.message.reply_text("🎨 Processing with AI...")

            result = await manus_enhance(photo[-1].file_id, user_style.get(user_id))

            if result:
                await update.message.reply_photo(result)
            else:
                await update.message.reply_text("❌ AI failed.")
        else:
            await update.message.reply_text("❌ Send a photo.")
        return

    if text == "✨ New Enhance":
        user_state[user_id] = STATE_WAIT_TARGET
        user_style[user_id] = None
        await update.message.reply_text(
            "📤 Send photo(s) to enhance with AI"
        )
        return

    # ----------------------
    # STYLE IMAGE
    # ----------------------
    if state == STATE_WAIT_STYLE:
        if update.message.photo:
            style_photo = update.message.photo[-1].file_id
            user_style[user_id] = style_photo

            user_state[user_id] = STATE_WAIT_TARGET

            await update.message.reply_text(
                "✅ Style saved!\nNow send target photos to apply this style."
            )
        else:
            await update.message.reply_text("❌ Please send a photo.")
        return

    # ----------------------
    # TARGET IMAGE PROCESS
    # ----------------------
    if state == STATE_WAIT_TARGET:
        if update.message.photo:
            photo = update.message.photo[-1].file_id
            style = user_style.get(user_id)

            await update.message.reply_text("🎨 Enhancing image with AI...")

            result_url = await manus_enhance(photo, style)

            if result_url:
                await update.message.reply_photo(result_url)
            else:
                await update.message.reply_text("❌ AI failed. Try again.")
        else:
            await update.message.reply_text("❌ Please send a photo.")
        return


# ======================
# MANUS AI INTEGRATION
# ======================
async def manus_enhance(photo_file_id: str, style_file_id: str = None):
    """
    REAL MANUS API CONNECTOR
    Replace endpoint if your Manus docs differ.
    """

    if not MANUS_API_KEY:
        logging.error("Missing MANUS_API_KEY")
        return None

    try:
        url = "https://api.manus.ai/v1/image/enhance"

        headers = {
            "Authorization": f"Bearer {MANUS_API_KEY}"
        }

        payload = {
            "image": photo_file_id,
            "style_image": style_file_id,
            "mode": "enhance"
        }

        response = requests.post(url, json=payload, headers=headers, timeout=120)

        if response.status_code == 200:
            data = response.json()

            # expected: {"result_url": "..."}
            return data.get("result_url")

        logging.error(f"Manus API error: {response.text}")
        return None

    except Exception as e:
        logging.error(f"Manus exception: {e}")
        return None


# ======================
# MAIN APP
# ======================
def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN missing in environment variables")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ALL, handle))

    print("🚀 Bot is running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
