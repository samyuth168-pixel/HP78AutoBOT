import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# =====================
# LOGGING
# =====================
logging.basicConfig(level=logging.INFO)

# =====================
# USER STATES MEMORY
# =====================
user_state = {}
user_style_photo = {}

# STATES
CHOOSING_MODE = "CHOOSING_MODE"
WAIT_STYLE = "WAIT_STYLE"
WAIT_TARGET = "WAIT_TARGET"
NEW_ENHANCE_CHOOSE = "NEW_ENHANCE_CHOOSE"
WAIT_NEW_PHOTO = "WAIT_NEW_PHOTO"

# =====================
# MENU
# =====================
main_menu = ReplyKeyboardMarkup(
    [["🖼 Sample Enhance", "✨ New Enhance"]],
    resize_keyboard=True
)

enhance_menu = ReplyKeyboardMarkup(
    [["Brightness", "HD", "Smooth", "AI Enhance"]],
    resize_keyboard=True
)

# =====================
# START
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user_state[uid] = CHOOSING_MODE

    await update.message.reply_text(
        "Welcome ✨\nChoose enhancement type:",
        reply_markup=main_menu
    )

# =====================
# HANDLE TEXT
# =====================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text

    state = user_state.get(uid, CHOOSING_MODE)

    # =====================
    # MAIN MENU
    # =====================
    if text == "🖼 Sample Enhance":
        user_state[uid] = WAIT_STYLE
        await update.message.reply_text(
            "📤 Send 1 STYLE photo first (this will be copied to other photos)"
        )
        return

    if text == "✨ New Enhance":
        user_state[uid] = NEW_ENHANCE_CHOOSE
        await update.message.reply_text(
            "Choose enhancement type:",
            reply_markup=enhance_menu
        )
        return

    # =====================
    # NEW ENHANCE CHOICE
    # =====================
    if state == NEW_ENHANCE_CHOOSE:
        user_state[uid] = WAIT_NEW_PHOTO
        user_state[f"{uid}_enhance_type"] = text

        await update.message.reply_text(
            f"Selected: {text}\nNow send your photo 📸"
        )
        return

    # =====================
    # BLOCK RANDOM TEXT
    # =====================
    await update.message.reply_text(
        "Please use menu buttons only.",
        reply_markup=main_menu
    )

# =====================
# HANDLE PHOTO
# =====================
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = user_state.get(uid, CHOOSING_MODE)

    photo_file = update.message.photo[-1].file_id

    # =====================
    # SAMPLE STYLE PHOTO
    # =====================
    if state == WAIT_STYLE:
        user_style_photo[uid] = photo_file
        user_state[uid] = WAIT_TARGET

        await update.message.reply_text(
            "✅ Style saved!\nNow send target photo(s) to apply this style."
        )
        return

    # =====================
    # APPLY SAMPLE STYLE
    # =====================
    if state == WAIT_TARGET:
        await update.message.reply_text("🎨 Processing sample enhance...")

        # HERE YOU WILL CALL AI API (Nano Banana / Manus AI / etc)
        await update.message.reply_text("✅ Done! (Sample enhanced photo returned)")
        return

    # =====================
    # NEW ENHANCE MODE
    # =====================
    if state == WAIT_NEW_PHOTO:
        enhance_type = user_state.get(f"{uid}_enhance_type", "AI Enhance")

        await update.message.reply_text(f"🎨 Processing {enhance_type}...")

        # PLACEHOLDER AI PROCESS
        await update.message.reply_text("✅ Done! (Enhanced photo returned)")
        return

    await update.message.reply_text(
        "Please choose enhancement type first.",
        reply_markup=main_menu
    )

# =====================
# MAIN APP
# =====================
def main():
    app = ApplicationBuilder().token("YOUR_BOT_TOKEN_HERE").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
