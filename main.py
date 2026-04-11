import os
import logging
from collections import defaultdict

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ---------------- LOGGING ----------------
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")

# ---------------- STATE STORAGE ----------------
USER_STATE = defaultdict(lambda: "MENU")
USER_DATA = {}

# ---------------- KEYBOARDS ----------------
main_menu = ReplyKeyboardMarkup(
    [["🖼 Sample Enhance", "✨ New Enhance"]],
    resize_keyboard=True
)

enhance_menu = ReplyKeyboardMarkup(
    [["⚡ Brightness", "📸 HD Quality"], ["🎯 Auto Enhance"], ["🔙 Back"]],
    resize_keyboard=True
)

# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    USER_STATE[uid] = "MENU"

    await update.message.reply_text(
        "👋 Welcome!\nChoose enhancement type:",
        reply_markup=main_menu
    )

# ---------------- TEXT HANDLER ----------------
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text
    state = USER_STATE[uid]

    # BACK BUTTON
    if text == "🔙 Back":
        USER_STATE[uid] = "MENU"
        await update.message.reply_text("Back to menu:", reply_markup=main_menu)
        return

    # ---------------- MAIN MENU ----------------
    if state == "MENU":

        if text == "🖼 Sample Enhance":
            USER_STATE[uid] = "WAIT_STYLE"
            await update.message.reply_text(
                "📤 Send 1 STYLE photo (this will be copied to others)"
            )
            return

        if text == "✨ New Enhance":
            USER_STATE[uid] = "NEW_MENU"
            await update.message.reply_text(
                "Choose enhancement tool:",
                reply_markup=enhance_menu
            )
            return

    # ---------------- NEW ENHANCE MENU ----------------
    if state == "NEW_MENU":
        USER_DATA[uid] = {"tool": text}
        USER_STATE[uid] = "WAIT_NEW_PHOTO"

        await update.message.reply_text(
            f"✅ Selected: {text}\nNow send your photo 📸"
        )
        return

    await update.message.reply_text("⚠️ Please use buttons only.")

# ---------------- PHOTO HANDLER ----------------
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = USER_STATE[uid]
    photo = update.message.photo[-1].file_id

    # ---------------- SAMPLE STYLE ----------------
    if state == "WAIT_STYLE":
        USER_DATA[uid] = {"style": photo}
        USER_STATE[uid] = "WAIT_TARGET_SAMPLE"

        await update.message.reply_text(
            "✅ Style saved!\nNow send target photo(s)."
        )
        return

    # ---------------- SAMPLE TARGET ----------------
    if state == "WAIT_TARGET_SAMPLE":
        style = USER_DATA[uid].get("style")

        await update.message.reply_text("🎨 Applying sample enhance...")

        # 🔥 HERE YOU CAN CALL AI (Nano Banana / Manus / API)
        # result = ai_style_transfer(style, photo)

        await update.message.reply_text("✅ Done! (Sample enhanced image)")
        return

    # ---------------- NEW ENHANCE ----------------
    if state == "WAIT_NEW_PHOTO":
        tool = USER_DATA[uid].get("tool", "Auto Enhance")

        await update.message.reply_text(f"⚡ Applying {tool}...")

        # 🔥 HERE YOU CAN CALL AI / EDIT ENGINE
        # result = enhance(photo, tool)

        await update.message.reply_text("✅ Done! Enhanced image")
        return

    await update.message.reply_text("⚠️ Please choose enhance type first.")

# ---------------- ERROR HANDLER ----------------
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error("Error: %s", context.error)

# ---------------- MAIN ----------------
def main():
    app = Application.builder().token(TOKEN).build()

    # 🚨 IMPORTANT FIX: avoid Telegram conflict
    app.bot.delete_webhook(drop_pending_updates=True)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))

    app.add_error_handler(error_handler)

    print("🤖 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
