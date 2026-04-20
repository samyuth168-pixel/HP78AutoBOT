import os
import logging
import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
import io
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Configuration (Using Environment Variables) ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))

# --- Brand and Group Configuration ---
BRAND_GROUPS = {
    "BMW": "https://t.me/hp78autobmw",
    "Porsche": "https://t.me/hp78autoporsche",
    "LandRover": "https://t.me/hp78autolandrover",
    "Alphard": "https://t.me/hp78autoalphard",
    "Ford": "https://t.me/hp78autoford",
}

# --- Contact Information ---
CONTACT_NUMBERS = ["071 545 9999", "096 629 6629"]
CONTACT_TELEGRAM_URL = "https://t.me/Kinhap"

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect("bot_analytics.db")
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS clicks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            brand TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()

def log_click(user_id, username, brand):
    conn = sqlite3.connect("bot_analytics.db")
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO clicks (user_id, username, brand) VALUES (?, ?, ?)",
        (user_id, username, brand),
    )
    conn.commit()
    conn.close()

def get_report():
    conn = sqlite3.connect("bot_analytics.db")
    cursor = conn.cursor()
    cursor.execute(
        "SELECT brand, COUNT(*) FROM clicks GROUP BY brand ORDER BY COUNT(*) DESC"
    )
    results = cursor.fetchall()
    conn.close()
    return results

def generate_report_chart():
    conn = sqlite3.connect("bot_analytics.db")
    df = pd.read_sql_query("SELECT brand, COUNT(*) as count FROM clicks GROUP BY brand", conn)
    conn.close()
    if df.empty: return None
    plt.figure(figsize=(10, 6))
    plt.bar(df["brand"], df["count"], color="skyblue")
    plt.xlabel("Car Brand")
    plt.ylabel("Number of Clicks")
    plt.title("Customer Brand Interest")
    plt.xticks(rotation=45)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()
    return buf

def generate_report_csv():
    conn = sqlite3.connect("bot_analytics.db")
    df = pd.read_sql_query("SELECT * FROM clicks", conn)
    conn.close()
    if df.empty: return None
    buf = io.BytesIO()
    df.to_csv(buf, index=False)
    buf.seek(0)
    return buf

# --- Bot Commands and Handlers ---
async def post_init(application: Application) -> None:
    """Cleanup any existing webhooks before starting polling."""
    await application.bot.delete_webhook(drop_pending_updates=True)
    logger.info("Existing webhooks deleted and pending updates dropped.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a message with inline buttons for car brands."""
    keyboard = [
        [
            InlineKeyboardButton(brand, callback_data=brand)
            for brand in list(BRAND_GROUPS.keys())[i : i + 2]
        ]
        for i in range(0, len(BRAND_GROUPS), 2)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    caption = (
        "សូមស្វាគមន៍មកកាន់ឆានែលលក់ឡានរបស់យើង! សូមជ្រើសរើសម៉ាកឡានដែលអ្នកចង់មើល៖\n\n"
        "Welcome to our car sales channel! Please select a brand to view our latest listings:"
    )
    
    # Using a generic car image placeholder
    await update.message.reply_photo(
        photo="https://images.unsplash.com/photo-1494976388531-d1058494cdd8?q=80&w=2070&auto=format&fit=crop",
        caption=caption,
        reply_markup=reply_markup,
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles button clicks for brand selection."""
    query = update.callback_query
    brand = query.data
    user = query.from_user
    chat_type = query.message.chat.type

    # Log the click for analytics
    log_click(user.id, user.username, brand)
    logger.info(f"User {user.id} ({user.username}) clicked brand: {brand}")

    group_link = BRAND_GROUPS.get(brand)
    logger.info(f"Retrieved group link for {brand}: {group_link}")

    if not group_link:
        await query.answer("Sorry, that brand is not currently available.", show_alert=True)
        return

    # Prepare the response message
    keyboard = [
        [InlineKeyboardButton(f"👁️ View {brand} Cars", url=group_link)],
        [
            InlineKeyboardButton(f"📞 {CONTACT_NUMBERS[0]}", url=f"tel:{CONTACT_NUMBERS[0].replace(' ', '')}"),
            InlineKeyboardButton(f"📞 {CONTACT_NUMBERS[1]}", url=f"tel:{CONTACT_NUMBERS[1].replace(' ', '')}"),
        ],
        [InlineKeyboardButton("💬 Telegram Contact", url=CONTACT_TELEGRAM_URL)],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    caption = (
        f"ជម្រើសដ៏ល្អ! អ្នកបានជ្រើសរើស {brand}។ សូមចុចប៊ូតុងខាងក្រោមដើម្បីចូលរួមក្រុម និងមើលស្តុកឡានបច្ចុប្បន្ន។\n\n"
        f"Great choice! You've selected {brand}. Click the button below to join the dedicated group and see our current stock."
    )

    if chat_type == 'channel':
        # When clicked in a channel, send a private message to the user
        try:
            await context.bot.send_message(
                chat_id=user.id,
                text=caption,
                reply_markup=reply_markup
            )
            await query.answer("I've sent the details to your private messages! សូមពិនិត្យមើលសារឯកជនរបស់អ្នក។", show_alert=True)
        except Exception as e:
            # If the user hasn't started the bot, we can't send a private message
            await query.answer(
                "Please start the bot first! សូមចុច 'Start' លើប៊ូតុងខាងក្រោម ដើម្បីទទួលបានព័ត៌មាន។", 
                show_alert=True,
                url=f"https://t.me/{context.bot.username}?start=start"
            )
    else:
        # If clicked in a private chat or group, edit the existing message
        await query.answer()
        try:
            await query.edit_message_caption(
                caption=caption,
                reply_markup=reply_markup,
            )
        except:
            # Fallback if the message doesn't have a caption (is a text message)
            await query.edit_message_text(
                text=caption,
                reply_markup=reply_markup,
            )

async def post_to_channel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Admin command to post the interactive brand selection to a channel."""
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if not context.args:
        await update.message.reply_text("Please provide the channel username. Example: /post @yourchannel")
        return

    channel_id = context.args[0]
    keyboard = [
        [
            InlineKeyboardButton(brand, callback_data=brand)
            for brand in list(BRAND_GROUPS.keys())[i : i + 2]
        ]
        for i in range(0, len(BRAND_GROUPS), 2)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    caption = (
        "សូមស្វាគមន៍មកកាន់ឆានែលលក់ឡានរបស់យើង! សូមជ្រើសរើសម៉ាកឡានដែលអ្នកចង់មើល៖\n\n"
        "Welcome to our car sales channel! Please select a brand to view our latest listings:"
    )
    
    try:
        await context.bot.send_photo(
            chat_id=channel_id,
            photo="https://images.unsplash.com/photo-1494976388531-d1058494cdd8?q=80&w=2070&auto=format&fit=crop",
            caption=caption,
            reply_markup=reply_markup,
        )
        await update.message.reply_text(f"Successfully posted to {channel_id}!")
    except Exception as e:
        await update.message.reply_text(f"Failed to post: {str(e)}\nMake sure the bot is an Admin in the channel.")

async def handle_new_post(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles the /newpost command and subsequent photo/caption input."""
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return
    
    if not context.args:
        await update.message.reply_text("Please provide the channel username. Example: /newpost @yourchannel")
        return

    # Store the target channel in user_data for the next step
    context.user_data['target_channel'] = context.args[0]
    context.user_data['waiting_for_post'] = True
    
    await update.message.reply_text(
        f"Okay! Now please **send me the photo** you want to post to {context.args[0]}. "
        "Make sure to include your **caption** with the photo!"
    )

async def process_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Processes the photo and caption sent by the admin for a new post."""
    if update.effective_user.id != ADMIN_USER_ID or not context.user_data.get('waiting_for_post'):
        return

    target_channel = context.user_data.get('target_channel')
    
    if not update.message.photo:
        await update.message.reply_text("Please send a **photo** with a caption.")
        return

    # Get the photo and caption
    photo_file_id = update.message.photo[-1].file_id
    caption = update.message.caption if update.message.caption else ""

    # Add the brand selection buttons
    keyboard = [
        [
            InlineKeyboardButton(brand, callback_data=brand)
            for brand in list(BRAND_GROUPS.keys())[i : i + 2]
        ]
        for i in range(0, len(BRAND_GROUPS), 2)
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await context.bot.send_photo(
            chat_id=target_channel,
            photo=photo_file_id,
            caption=caption,
            reply_markup=reply_markup,
        )
        await update.message.reply_text(f"✅ Successfully posted to {target_channel}!")
        # Clear the state
        context.user_data['waiting_for_post'] = False
    except Exception as e:
        await update.message.reply_text(f"❌ Failed to post: {str(e)}")

async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Generates a report for the admin."""
    if update.effective_user.id != ADMIN_USER_ID:
        await update.message.reply_text("You are not authorized to view this report.")
        return

    report_data = get_report()
    if not report_data:
        await update.message.reply_text("No clicks recorded yet.")
        return

    report_text = "📊 *Customer Click Report*\n\n"
    report_text += "| Brand | Clicks |\n| :--- | :--- |\n"
    for brand, count in report_data:
        report_text += f"| {brand} | {count} |\n"

    await update.message.reply_text(report_text, parse_mode="Markdown")

    chart_buf = generate_report_chart()
    if chart_buf:
        await update.message.reply_photo(photo=chart_buf, caption="Click Distribution Chart")

    csv_buf = generate_report_csv()
    if csv_buf:
        await update.message.reply_document(document=csv_buf, filename="click_report.csv", caption="Detailed Click Data (CSV)")

def main() -> None:
    """Start the bot."""
    init_db()
    
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN environment variable is not set!")
        return

    logger.info(f"Starting bot with Admin ID: {ADMIN_USER_ID}")
    
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("post", post_to_channel))
    application.add_handler(CommandHandler("newpost", handle_new_post))
    application.add_handler(CommandHandler("report", report_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    # Handle photos sent by the admin for /newpost
    from telegram.ext import MessageHandler, filters
    application.add_handler(MessageHandler(filters.PHOTO, process_admin_message))
    
    logger.info("Bot is polling for updates...")
    # Use drop_pending_updates=True to prevent conflict on restart
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
