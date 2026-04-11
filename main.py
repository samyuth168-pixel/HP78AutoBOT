# =============================
# PRO Telegram AI Photo Editor Bot
# Features:
# - Multi-effect selection
# - Style transfer (sample photo)
# - Queue processing
# - English / Khmer UI
# =============================

import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from PIL import Image, ImageEnhance
import cv2

BOT_TOKEN = os.getenv("BOT_TOKEN")

# -------- USER STATE --------
user_sessions = {}
queue = asyncio.Queue()

# -------- IMAGE FUNCTIONS --------

def adjust_brightness(img):
    return ImageEnhance.Brightness(img).enhance(1.5)

def adjust_contrast(img):
    return ImageEnhance.Contrast(img).enhance(1.5)

def beauty_filter_cv(img_path):
    img = cv2.imread(img_path)
    smooth = cv2.bilateralFilter(img, 15, 75, 75)
    cv2.imwrite(img_path, smooth)

# -------- STYLE TRANSFER (Simple color match) --------

def apply_style(source_path, style_path, output_path):
    src = cv2.imread(source_path)
    style = cv2.imread(style_path)

    src = cv2.resize(src, (style.shape[1], style.shape[0]))
    blended = cv2.addWeighted(src, 0.7, style, 0.3, 0)
    cv2.imwrite(output_path, blended)

# -------- UI --------

def get_menu(lang="en"):
    if lang == "kh":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("✨ ស្អាត", callback_data="beauty")],
            [InlineKeyboardButton("☀️ ពន្លឺ", callback_data="brightness")],
            [InlineKeyboardButton("🎨 កម្រាស់ពណ៌", callback_data="contrast")],
            [InlineKeyboardButton("🎭 Style", callback_data="style")],
            [InlineKeyboardButton("✅ អនុវត្ត", callback_data="apply")]
        ])
    else:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("✨ Beauty", callback_data="beauty")],
            [InlineKeyboardButton("☀️ Brightness", callback_data="brightness")],
            [InlineKeyboardButton("🎨 Contrast", callback_data="contrast")],
            [InlineKeyboardButton("🎭 Style", callback_data="style")],
            [InlineKeyboardButton("✅ Apply", callback_data="apply")]
        ])

# -------- COMMANDS --------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_sessions[update.effective_chat.id] = {
        "effects": [],
        "lang": "en",
        "style": None
    }
    await update.message.reply_text("Send photo 📸 / ផ្ញើរូបភាព")

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    photo = update.message.photo[-1]
    file = await photo.get_file()

    path = f"input_{chat_id}.jpg"
    await file.download_to_drive(path)

    if user_sessions[chat_id].get("waiting_style"):
        user_sessions[chat_id]["style"] = path
        user_sessions[chat_id]["waiting_style"] = False
        await update.message.reply_text("Style saved ✅")
        return

    user_sessions[chat_id]["photo"] = path
    await update.message.reply_text("Choose options:", reply_markup=get_menu(user_sessions[chat_id]["lang"]))

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id

    session = user_sessions.get(chat_id)
    action = query.data

    if action == "style":
        session["waiting_style"] = True
        await query.message.reply_text("Upload style photo 🎭")
        return

    if action == "apply":
        await queue.put(chat_id)
        await query.message.reply_text("Processing... ⏳")
        return

    if action not in session["effects"]:
        session["effects"].append(action)

    await query.message.reply_text(f"Added: {action}")

# -------- PROCESSOR --------

async def worker(app):
    while True:
        chat_id = await queue.get()
        session = user_sessions.get(chat_id)

        input_path = session.get("photo")
        style_path = session.get("style")
        effects = session.get("effects", [])

        img = Image.open(input_path)

        if "brightness" in effects:
            img = adjust_brightness(img)
        if "contrast" in effects:
            img = adjust_contrast(img)

        temp_path = f"temp_{chat_id}.jpg"
        img.save(temp_path)

        if "beauty" in effects:
            beauty_filter_cv(temp_path)

        output_path = f"output_{chat_id}.jpg"

        if style_path:
            apply_style(temp_path, style_path, output_path)
        else:
            os.rename(temp_path, output_path)

        await app.bot.send_photo(chat_id=chat_id, photo=open(output_path, "rb"))

        session["effects"] = []
        queue.task_done()

# -------- MAIN --------

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(CallbackQueryHandler(button))

    app.create_task(worker(app))

    print("Pro Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()

# =============================
# requirements.txt
# =============================
# python-telegram-bot==20.7
# pillow
# opencv-python
