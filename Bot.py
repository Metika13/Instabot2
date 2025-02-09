import os
import random
import logging
from datetime import datetime, time
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, JobQueue
from instaloader import Instaloader, Profile

# تنظیمات
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")
SESSION_FILE = "instagram_session"
TARGET_PAGES = ["target_page1", "target_page2"]
HASHTAGS = ["viral", "trending"]
POSTING_TIME = time(12, 0)
APPROVAL_CHAT_ID = os.getenv("APPROVAL_CHAT_ID")

# تنظیمات Instaloader
L = Instaloader()
if os.path.exists(SESSION_FILE):
    L.load_session_from_file(INSTAGRAM_USERNAME, SESSION_FILE)
else:
    L.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
    L.save_session_to_file(SESSION_FILE)

# لاگ‌گیری
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# دستورات تلگرام
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("خوش آمدید! از /settime برای تغییر زمان پست استفاده کنید.")

async def settime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        global POSTING_TIME
        hour, minute = map(int, context.args[0].split(":"))
        POSTING_TIME = time(hour, minute)
        await update.message.reply_text(f"زمان پست به {POSTING_TIME} تنظیم شد.")
    except (IndexError, ValueError):
        await update.message.reply_text("فرمت صحیح: /settime HH:MM")

async def change_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global TARGET_PAGES
    TARGET_PAGES = context.args
    await update.message.reply_text(f"صفحات هدف به {', '.join(TARGET_PAGES)} به‌روزرسانی شدند.")

# توابع کمکی
def download_viral_video():
    for hashtag in HASHTAGS:
        try:
            posts = L.get_hashtag_posts(hashtag)
            for post in posts:
                if post.is_video and not post.is_pinned:
                    return post
        except Exception as e:
            logger.error(f"خطا در دریافت پست‌ها: {e}")
    return None

def download_random_story():
    try:
        page = random.choice(TARGET_PAGES)
        profile = Profile.from_username(L.context, page)
        stories = L.get_stories(userids=[profile.userid])
        for story in stories:
            for item in story.get_items():
                return item
    except Exception as e:
        logger.error(f"خطا در دریافت استوری: {e}")
    return None

async def approve_content(media, context: ContextTypes.DEFAULT_TYPE):
    try:
        if media.is_video:
            await context.bot.send_video(
                chat_id=APPROVAL_CHAT_ID,
                video=media.video_url,
                caption="این ویدیو تأیید شود؟"
            )
        else:
            await context.bot.send_photo(
                chat_id=APPROVAL_CHAT_ID,
                photo=media.url,
                caption="این عکس تأیید شود؟"
            )
        return True
    except Exception as e:
        logger.error(f"خطا در ارسال برای تأیید: {e}")
        return False

async def post_content(media, context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    try:
        if media.is_video:
            await context.bot.send_video(chat_id=chat_id, video=media.video_url)
        else:
            await context.bot.send_photo(chat_id=chat_id, photo=media.url)
        return True
    except Exception as e:
        logger.error(f"خطا در ارسال محتوا: {e}")
        return False

async def scheduled_post(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now().time()
    if now.hour == POSTING_TIME.hour and now.minute == POSTING_TIME.minute:
        media = download_viral_video()
        if media:
            approval_result = await approve_content(media, context)
            if approval_result:
                await post_content(media, context, APPROVAL_CHAT_ID)

async def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("settime", settime))
    application.add_handler(CommandHandler("changepage", change_page))

    job_queue = application.job_queue
    job_queue.run_repeating(scheduled_post, interval=60, first=10)

    # استفاده از run_polling برای جلوگیری از مشکلات با حلقه رویداد
    await application.run_polling()

if __name__ == "__main__":
    import asyncio
    # در اینجا بررسی می‌کنیم که آیا یک حلقه رویداد در حال اجرا است یا خیر
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
