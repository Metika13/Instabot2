import os
import random
import logging
from datetime import datetime
from telegram import Update, InputMediaVideo, InputMediaPhoto
from telegram.ext import Updater, CommandHandler, CallbackContext
from instaloader import Instaloader, Profile, Post
from apscheduler.schedulers.background import BackgroundScheduler

# تنظیمات
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD")
SESSION_FILE = "instagram_session"
TARGET_PAGES = ["target_page1", "target_page2"]  # صفحاتی که استوری‌ها از آن‌ها دانلود می‌شوند
HASHTAGS = ["viral", "trending"]  # هشتگ‌ها برای پیدا کردن پست‌های ویرال
POSTING_TIME = "12:00"  # زمان پیش‌فرض پست (فرمت 24 ساعته)
APPROVAL_CHAT_ID = os.getenv("APPROVAL_CHAT_ID")  # چت آیدی برای تأیید محتوا

# تنظیمات Instaloader
L = Instaloader()
if os.path.exists(SESSION_FILE):
    L.load_session_from_file(INSTAGRAM_USERNAME, SESSION_FILE)
else:
    L.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
    L.save_session_to_file(SESSION_FILE)

# تنظیمات Scheduler
scheduler = BackgroundScheduler()
scheduler.start()

# لاگ‌گیری
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# دستورات تلگرام
def start(update: Update, context: CallbackContext):
    update.message.reply_text("خوش آمدید! از /settime برای تغییر زمان پست استفاده کنید.")

def settime(update: Update, context: CallbackContext):
    try:
        global POSTING_TIME
        POSTING_TIME = context.args[0]
        update.message.reply_text(f"زمان پست به {POSTING_TIME} تنظیم شد.")
        schedule_post()
    except IndexError:
        update.message.reply_text("Usage: /settime HH:MM")

def change_page(update: Update, context: CallbackContext):
    try:
        global TARGET_PAGES
        TARGET_PAGES = context.args
        update.message.reply_text(f"صفحات هدف به {', '.join(TARGET_PAGES)} به‌روزرسانی شدند.")
    except IndexError:
        update.message.reply_text("Usage: /changepage page1 page2")

# توابع دانلود و پست
def download_viral_video():
    for hashtag in HASHTAGS:
        posts = L.get_hashtag_posts(hashtag)
        for post in posts:
            if post.is_video and not post.is_pinned:
                return post
    return None

def download_random_story():
    page = random.choice(TARGET_PAGES)
    profile = Profile.from_username(L.context, page)
    stories = L.get_stories(userids=[profile.userid])
    for story in stories:
        for item in story.get_items():
            return item
    return None

def approve_content(media):
    # ارسال محتوا برای تأیید
    if media.is_video:
        context.bot.send_video(chat_id=APPROVAL_CHAT_ID, video=media.video_url, caption="این ویدیو تأیید شود؟")
    else:
        context.bot.send_photo(chat_id=APPROVAL_CHAT_ID, photo=media.url, caption="این عکس تأیید شود؟")
    # منتظر تأیید بمانید (منطق پاسخ کاربر را پیاده‌سازی کنید)

def post_content(media):
    if media.is_video:
        context.bot.send_video(chat_id=update.message.chat_id, video=media.video_url)
    else:
        context.bot.send_photo(chat_id=update.message.chat_id, photo=media.url)

def scheduled_post():
    media = download_viral_video()
    if media and approve_content(media):
        post_content(media)
    else:
        logger.info("هیچ محتوای تأیید شده‌ای پیدا نشد.")

def schedule_post():
    hour, minute = map(int, POSTING_TIME.split(":"))
    scheduler.add_job(scheduled_post, 'cron', hour=hour, minute=minute)

# تابع اصلی
def main():
    updater = Updater(TELEGRAM_BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("settime", settime))
    dp.add_handler(CommandHandler("changepage", change_page))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
