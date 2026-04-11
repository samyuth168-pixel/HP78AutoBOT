# Telegram Photo Enhance Bot (Render Ready)
# python-telegram-bot==20.7

import os
import cv2
import numpy as np
from io import BytesIO
from PIL import Image
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

# =====================
# CONFIG
# =====================
TOKEN = os.getenv("BOT_TOKEN")

# user sessions (simple in-memory)
user_data = {}

# structure:
# user_data[user_id] = {
#   "mode": "sample" | "new",
#   "style_img": np.array,
#   "target_imgs": [np.array]
# }

# =====================
# IMAGE UTILITIES
# =====================

def read_image(file_bytes):
    img = Image.open(BytesIO(file_bytes)).convert("RGB")
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def to_bytes(img):
    _, buffer = cv2.imencode('.jpg', img)
    return BytesIO(buffer.tobytes())


# SIMPLE STYLE EXTRACTION
# =====================
def extract_style(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    return {
        "brightness": float(np.mean(hsv[:, :, 2])),
        "contrast": float(np.std(hsv[:, :, 2]))
    }


def apply_style(img, style):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # brightness shift
    v = hsv[:, :, 2].astype(np.float32)
    v = v + (style["brightness"] - np.mean(v))
    v = np.clip(v, 0, 255)
    hsv[:, :, 2] = v.astype(np.uint8)

    out = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)

    # contrast boost
    alpha = max(0.8, min(1.5, style["contrast"] / 50))
    out = cv2.convertScaleAbs(out, alpha=alpha)

    return out


# NEW ENHANCE
# =====================

def enhance_hd(img):
    kernel = np.array([[0, -1, 0],
                       [-1, 5, -1],
                       [0, -1, 0]])
    return cv2.filter2D(img, -1, kernel)


def enhance_brightness(img):
    return cv2.convertScaleAbs(img, alpha=1.2, beta=20)


# =====================
# UI
# =====================

def main_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🖼 Sample Enhance", callback_data="sample")],
        [InlineKeyboardButton("🤖 New Enhance", callback_data="new")]
    ])


def new_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔆 Brightness", callback_data="bright")],
        [InlineKeyboardButton("📷 HD Enhance", callback_data="hd")],
        [InlineKeyboardButton("⚡ Auto Enhance", callback_data="auto")]
    ])


# =====================
# HANDLERS
# =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send me a photo to start enhancement ✨"
    )


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    file_bytes = await file.download_as_bytearray()
    img = read_image(file_bytes)

    user_data.setdefault(user_id, {})

    # first image → ask mode
    user_data[user_id]["temp_img"] = img

    await update.message.reply_text(
        "Choose enhancement type:",
        reply_markup=main_menu()
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data

    if user_id not in user_data:
        user_data[user_id] = {}

    # =====================
    # SAMPLE ENHANCE
    # =====================
    if data == "sample":
        user_data[user_id]["mode"] = "sample"
        user_data[user_id]["step"] = "style"
        user_data[user_id]["target_imgs"] = []

        await query.message.reply_text("Send 1 STYLE photo 🎨")

    # =====================
    # NEW ENHANCE
    # =====================
    elif data == "new":
        user_data[user_id]["mode"] = "new"
        await query.message.reply_text(
            "Choose tool:",
            reply_markup=new_menu()
        )

    # NEW ENHANCE OPTIONS
    elif data in ["bright", "hd", "auto"]:
        user_data[user_id]["enhance_type"] = data
        await query.message.reply_text("Now send your photo 📸")


# =====================
# SECOND PHOTO FLOW
# =====================

async def handle_second_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    if user_id not in user_data:
        return

    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    file_bytes = await file.download_as_bytearray()
    img = read_image(file_bytes)

    session = user_data[user_id]

    # =====================
    # SAMPLE ENHANCE FLOW
    # =====================
    if session.get("mode") == "sample":

        if session.get("step") == "style":
            session["style_img"] = img
            session["style"] = extract_style(img)
            session["step"] = "target"

            await update.message.reply_text("Now send target photos 📸")
            return

        if session.get("step") == "target":
            style = session.get("style")
            result = apply_style(img, style)

            bio = to_bytes(result)
            bio.seek(0)

            await update.message.reply_photo(photo=bio)
            return

    # =====================
    # NEW ENHANCE FLOW
    # =====================
    elif session.get("mode") == "new":
        etype = session.get("enhance_type")

        if etype == "bright":
            result = enhance_brightness(img)
        elif etype == "hd":
            result = enhance_hd(img)
        else:
            result = cv2.convertScaleAbs(img, alpha=1.1, beta=10)

        bio = to_bytes(result)
        bio.seek(0)

        await update.message.reply_photo(photo=bio)


# =====================
# APP START
# =====================

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
