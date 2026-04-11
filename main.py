import logging
import os
import cv2
import numpy as np
from PIL import Image, ImageEnhance
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(level=logging.INFO)

user_state = {}

# MENU
menu = ReplyKeyboardMarkup(
    [["Send photo 📸"]],
    resize_keyboard=True
)

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to BeautyAgent ✨\nSend photo to enhance",
        reply_markup=menu
    )

# SIMPLE AI ENHANCEMENT (REAL PROCESSING)
def enhance_image(input_path, output_path):
    img = cv2.imread(input_path)

    # upscale
    img = cv2.resize(img, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_CUBIC)

    # denoise
    img = cv2.fastNlMeansDenoisingColored(img, None, 10, 10, 7, 21)

    # convert to PIL for color boost
    pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

    enhancer = ImageEnhance.Sharpness(pil_img)
    pil_img = enhancer.enhance(2.0)

    enhancer = ImageEnhance.Contrast(pil_img)
    pil_img = enhancer.enhance(1.3)

    pil_img.save(output_path)

# PHOTO HANDLER
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Processing AI image... ⏳")

    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)

    input_path = "input.jpg"
    output_path = "output.jpg"

    await file.download_to_drive(input_path)

    try:
        enhance_image(input_path, output_path)

        await update.message.reply_photo(
            photo=open(output_path, "rb"),
            caption="✨ AI Enhanced Image"
        )

    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")

# TEXT HANDLER
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please send a photo 📸")

# MAIN
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.TEXT, text_handler))

    print("Bot running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
