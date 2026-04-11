import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")

# States (simple memory)
USER_STATE = {}

# Menu
main_menu = ReplyKeyboardMarkup(
    [["🖼 Sample Enhance", "✨ New Enhance"]],
    resize_keyboard=True
)

style_menu = ReplyKeyboardMarkup(
    [["🎨 Use This as Style"], ["🔙 Back"]],
    resize_keyboard=True
)

enhance_menu = ReplyKeyboardMarkup(
    [["⚡ Brightness", "📸 HD Quality"], ["🎯 Auto Enhance"], ["🔙 Back"]],
    resize_keyboard=True
)


# ---------------- START ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    USER_STATE[user_id] = {"step": "choose_mode"}

    await update.message.reply_text(
        "👋 Welcome!\nChoose enhancement type:",
        reply_markup=main_menu
    )


# ---------------- TEXT HANDLER ----------------
async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    state = USER_STATE.get(user_id, {"step": "choose_mode"})

    # BACK
    if text == "🔙 Back":
        USER_STATE[user_id] = {"step": "choose_mode"}
        await update.message.reply_text("Choose again:", reply_markup=main_menu)
        return

    # ---------------- MAIN MENU ----------------
    if state["step"] == "choose_mode":

        if text == "🖼 Sample Enhance":
            USER_STATE[user_id] = {"step": "await_style_photo"}
            await update.message.reply_text(
                "📤 Send 1 STYLE photo first (this will be copied to other photos)",
                reply_markup=style_menu
            )
            return

        if text == "✨ New Enhance":
            USER_STATE[user_id] = {"step": "choose_new_tool"}
            await update.message.reply_text(
                "Choose enhancement tool:",
                reply_markup=enhance_menu
            )
            return

    # ---------------- NEW ENHANCE ----------------
    if state["step"] == "choose_new_tool":

        USER_STATE[user_id]["tool"] = text
        USER_STATE[user_id]["step"] = "await_photo_new"

        await update.message.reply_text(
            f"✅ Selected: {text}\nNow send your photo 📸"
        )
        return

    # fallback
    await update.message.reply_text("Please use menu buttons only.")


# ---------------- PHOTO HANDLER ----------------
async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    state = USER_STATE.get(user_id, {"step": "choose_mode"})

    photo = update.message.photo[-1].file_id

    # ---------------- SAMPLE STYLE PHOTO ----------------
    if state["step"] == "await_style_photo":
        USER_STATE[user_id] = {
            "step": "await_target_photo_sample",
            "style_photo": photo
        }

        await update.message.reply_text(
            "✅ Style saved!\nNow send target photo(s) to apply this style."
        )
        return

    # ---------------- SAMPLE TARGET PHOTO ----------------
    if state["step"] == "await_target_photo_sample":
        style = state.get("style_photo")

        await update.message.reply_text("🎨 Processing sample enhance...")

        # 🔥 HERE YOU CALL YOUR AI (Nano Banana / Manus / API)
        # result = ai_style_transfer(style, photo)

        await update.message.reply_text("✅ Done! (Sample enhanced photo returned)")
        return

    # ---------------- NEW ENHANCE PHOTO ----------------
    if state["step"] == "await_photo_new":
        tool = state.get("tool", "Auto Enhance")

        await update.message.reply_text(f"⚡ Applying {tool}...")

        # 🔥 HERE YOU CALL YOUR AI / EDIT LOGIC
        # result = enhance(photo, tool)

        await update.message.reply_text("✅ Done! Enhanced photo sent.")
        return

    await update.message.reply_text("Please select enhancement type first.")


# ---------------- MAIN ----------------
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    app.add_handler(MessageHandler(filters.PHOTO, photo_handler))

    print("Bot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
