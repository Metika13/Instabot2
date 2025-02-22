import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters
from instagrapi import Client

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Instagram client
cl = Client()

# Load Instagram session from file
def load_instagram_session():
    session_file = "mtkh13o.json"  # Path to your session file
    if os.path.exists(session_file):
        cl.load_settings(session_file)
    else:
        raise FileNotFoundError("Session file not found!")

# Command to start the bot
async def start(update: Update, context):
    await update.message.reply_text('Hello! I am your Telegram bot. Use /instagram to interact with Instagram.')

# Command to fetch Instagram profile info
async def instagram(update: Update, context):
    try:
        load_instagram_session()
        user_id = cl.user_id  # Get your Instagram user ID
        user_info = cl.user_info(user_id)  # Fetch your profile info
        response = f"Instagram Profile:\nUsername: {user_info.username}\nFollowers: {user_info.follower_count}\nFollowing: {user_info.following_count}"
        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Error fetching Instagram data: {e}")
        await update.message.reply_text("Failed to fetch Instagram data. Please check logs.")

# Main function to run the bot
def main():
    # Get the bot token from environment variables
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("No TELEGRAM_BOT_TOKEN found in environment variables.")

    # Build the application
    application = ApplicationBuilder().token(token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("instagram", instagram))

    # Start the bot
    application.run_polling()

if __name__ == '__main__':
    main()
