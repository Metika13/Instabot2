import os
import random
import logging
import asyncio
import nest_asyncio  # ⬅️ اضافه کردن این کتابخانه برای حل مشکل event loop
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from instaloader import Instaloader, Profile, Post
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# تنظیمات
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")
SESSION_FILE = "instagram_session"
TARGET_PAGES = ["target_page1", "target_page2"]
HASHTAGS = ["viral", "trending"]
POSTING_TIME = "12:00"
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

# تنظیمات Scheduler
scheduler = AsyncIOScheduler()
scheduler.start()

# حل مشکل event loop
nest_asyncio.apply()

# دستورات تلگرام
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("خوش آمدید! از /settime برای تغییر زمان پست استفاده کنید.")

async def settime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        global POSTING_TIME
        POSTING_TIME = context.args[0]
        await update.message.reply_text(f"زمان پست به {POSTING_TIME} تنظیم شد.")
        schedule_post()
    except (IndexError, ValueError):
        await update.message.reply_text("فرمت صحیح: /settime HH:MM")

async def change_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        global TARGET_PAGES
        TARGET_PAGES = context.args
        await update.message.reply_text(f"صفحات هدف به {', '.join(TARGET_PAGES)} به‌روزرسانی شدند.")
    except IndexError:
        await update.message.reply_text("فرمت صحیح: /changepage page1 page2")

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
            await context.bot.send_video(
                chat_id=chat_id,
                video=media.video_url
            )
        else:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=media.url
            )
        return True
    except Exception as e:
        logger.error(f"خطا در ارسال محتوا: {e}")
        return False

# زمان‌بندی و اجرای خودکار
async def scheduled_post(application: Application):
    context = application.bot
    media = download_viral_video()
    if media:
        approval_result = await approve_content(media, context)
        if approval_result:
            post_result = await post_content(media, context, APPROVAL_CHAT_ID)
            if not post_result:
                logger.error("خطا در ارسال محتوا")
        else:
            logger.info("محتوا تأیید نشد")
    else:
        logger.info("محتوا پیدا نشد")

def schedule_post(application: Application):
    hour, minute = map(int, POSTING_TIME.split(":"))
    scheduler.add_job(
        scheduled_post,
        'cron',
        hour=hour,
        minute=minute,
        args=[application]
    )

# تابع اصلی
async def main():
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("settime", settime))
    application.add_handler(CommandHandler("changepage", change_page))
    
    # تنظیم زمان‌بندی اولیه
    schedule_post(application)
    
    await application.run_polling()

# اجرای صحیح در Render
if __name__ == "__main__":
    asyncio.run(main())  # ⬅️ حالا بدون خطای event loop اجرا می‌شود
