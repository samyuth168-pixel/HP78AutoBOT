import os
import logging
import requests
from io import BytesIO
from PIL import Image
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =========================
# CONFIG
# =========================
BOT_TOKEN = os.getenv("BOT_TOKEN")
MANUS_API_KEY = os.getenv("MANUS_API_KEY")

MANUS_API_URL = "https://api.manus.ai/v1/enhance"  # placeholder endpoint

logging.basicConfig(level=logging.INFO)

user_state = {}  # simple memory per user


# =========================
# MANUS AI FUNCTION
# =========================
def enhance_with_manus(image_bytes: bytes, style: bool = False):
    """
    Send image to Manus AI for enhancement.
    Replace endpoint if your Manus docs differ.
    """

    headers = {
        "Authorization": f"Bearer {MANUS_API_KEY}",
    }

    files = {
        "image": ("image.jpg", image_bytes, "image/jpeg"),
    }

    data = {
        "mode": "style" if style else "enhance"
    }

    try:
        res = requests.post(MANUS_API_URL, headers=headers, files=files, data=data)
        res.raise_for_status()

        # assume API returns image bytes
        return res.content

    except Exception as e:
        print("Manus API error:", e)
        return None


# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    user_state[user_id] = {
        "step": "waiting_style"
    }

    await update.message.reply_text(
        "📤 Send 1 STYLE photo first (this will define enhancement style)"
    )


# =========================
# PHOTO HANDLER
# =========================
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in user_state:
        user_state[user_id] = {"step": "waiting_style"}

    step = user_state[user_id]["step"]

    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    image_bytes = await file.download_as_bytearray()

    # =========================
    # STEP 1: STYLE IMAGE
    # =========================
    if step == "waiting_style":
        user_state[user_id]["style_image"] = image_bytes
        user_state[user_id]["step"] = "waiting_target"

        await update.message.reply_text(
            "✅ Style saved!\nNow send target photo(s) to apply this style."
        )
        return

    # =========================
    # STEP 2: TARGET IMAGE
    # =========================
    style_img = user_state[user_id].get("style_image")

    if not style_img:
        await update.message.reply_text("❌ Please send style photo first.")
        return

    await update.message.reply_text("🎨 Processing with Manus AI...")

    # CALL MANUS AI
    result = enhance_with_manus(image_bytes, style=True)

    if not result:
        await update.message.reply_text("❌ AI processing failed. Try again.")
        return

    await update.message.reply_photo(photo=BytesIO(result))


# =========================
# TEXT HANDLER (BLOCK WRONG INPUTS)
# =========================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📸 Please send a PHOTO only.")


# =========================
# ERROR HANDLER
# =========================
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error("Error: %s", context.error)


# =========================
# MAIN
# =========================
def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN missing in environment variables")

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT, handle_text))

    app.add_error_handler(error_handler)

    # IMPORTANT FIX FOR RENDER
    app.run_polling(
        drop_pending_updates=True,  # fixes conflict issues
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()
