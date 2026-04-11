import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO)

user_state = {}
user_style = {}

CHOOSING = "CHOOSING"
WAIT_STYLE = "WAIT_STYLE"
WAIT_TARGET = "WAIT_TARGET"

menu = ReplyKeyboardMarkup(
    [["🖼 Sample Enhance", "✨ New Enhance"]],
    resize_keyboard=True
)

# =====================
# START
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_state[update.effective_user.id] = CHOOSING

    await update.message.reply_text(
        "✨ Choose enhancement type:",
        reply_markup=menu
    )

# =====================
# TEXT
# =====================
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text

    if text == "🖼 Sample Enhance":
        user_state[uid] = WAIT_STYLE
        await update.message.reply_text("📤 Send 1 STYLE photo")
        return

    if text == "✨ New Enhance":
        await update.message.reply_text("This feature coming next update 🚀")
        return

    await update.message.reply_text("Use buttons only.", reply_markup=menu)

# =====================
# PHOTO
# =====================
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    state = user_state.get(uid, CHOOSING)

    photo = update.message.photo[-1].file_id

    # SAVE STYLE
    if state == WAIT_STYLE:
        user_style[uid] = photo
        user_state[uid] = WAIT_TARGET

        await update.message.reply_text("✅ Style saved!\nNow send target photo")
        return

    # PROCESS TARGET
    if state == WAIT_TARGET:
        await update.message.reply_text("🎨 Processing AI enhance...")

        # HERE YOU CONNECT REAL AI (Replicate / Stability / etc)
        await update.message.reply_text("✅ Done! (AI result here)")
        return

# =====================
# SAFE START (FIX WEBHOOK ISSUE)
# =====================
async def post_init(app):
    await app.bot.delete_webhook(drop_pending_updates=True)

# =====================
# MAIN
# =====================
def main():
    app = ApplicationBuilder().token("YOUR_BOT_TOKEN_HERE").post_init(post_init).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
