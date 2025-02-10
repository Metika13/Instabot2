import os
import instaloader
import requests
import time
import asyncio
import traceback
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import nest_asyncio

# فعال‌سازی nest_asyncio
nest_asyncio.apply()

# تنظیمات
TELEGRAM_API_KEY = os.getenv('TELEGRAM_API_KEY')
if not TELEGRAM_API_KEY:
    raise ValueError("❌ کلید API تلگرام یافت نشد.")

# مقداردهی اولیه
video_to_post = []
stories_to_post = []
profiles_to_fetch = ["profile1", "profile2"]  # جایگزین کنید با نام‌های کاربری اینستاگرام
min_likes = 1000
hashtags = "#viral"
num_stories_to_fetch = 5

# ایجاد Flask
app = Flask(__name__)

# مقداردهی اولیه Instaloader
L = instaloader.Instaloader()
try:
    session_url = 'https://github.com/Metika13/Instabot2/raw/main/mtkh13o_session.json'
    session_path = './mtkh13o_session.json'
    response = requests.get(session_url)
    with open(session_path, 'wb') as file:
        file.write(response.content)
    L.load_session_from_file('mtkh13o', session_path)
    print("✅ سشن اینستاگرام با موفقیت بارگذاری شد.")
except Exception as e:
    print(f"❌ خطا در بارگذاری سشن:\n{traceback.format_exc()}")
    exit(1)

# ایجاد پوشه‌های مورد نیاز
if not os.path.exists("downloads"):
    os.makedirs("downloads")
if not os.path.exists("downloads/stories"):
    os.makedirs("downloads/stories")

# دانلود ویدیوهای ترند
def download_trending_videos():
    print("📥 در حال دانلود ویدیوهای ترند...")
    for hashtag in hashtags.split(","):
        try:
            print(f"🔍 در حال جستجو برای هشتگ: #{hashtag.strip()}")
            posts = L.get_hashtag_posts(hashtag.strip())
            for post in posts:
                if post.is_video and post.likes > min_likes:
                    print(f"🎥 ویدیو {post.shortcode} با {post.likes} لایک یافت شد.")
                    L.download_post(post, target="downloads")
                    video_to_post.append(post)
                    break  # فقط یک ویدیو برای هر هشتگ دانلود می‌شود
        except Exception as e:
            print(f"⚠️ خطا در دانلود ویدیو:\n{traceback.format_exc()}")

# دانلود استوری‌ها
def download_stories():
    print("📥 در حال دانلود استوری‌ها...")
    for profile in profiles_to_fetch:
        try:
            print(f"🔍 در حال جستجو برای پروفایل: {profile}")
            profile = instaloader.Profile.from_username(L.context, profile)
            stories = profile.get_stories()
            for story in stories:
                if story.is_video:
                    print(f"🎥 استوری {story.shortcode} یافت شد.")
                    L.download_story(story, target="downloads/stories")
                    stories_to_post.append(story)
                    break  # فقط یک استوری برای هر پروفایل دانلود می‌شود
        except Exception as e:
            print(f"⚠️ خطا در دانلود استوری:\n{traceback.format_exc()}")

# دستور شروع ربات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text('🟢 ربات تلگرام فعال است!')
        print("✅ کاربر دستور /start را اجرا کرد.")
    except Exception as e:
        print(f"⚠️ خطا در دستور شروع:\n{traceback.format_exc()}")

# پردازش پیام‌های کاربر
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text
        print(f"📩 پیام دریافتی: {text}")
        if text.startswith("#"):
            global hashtags
            hashtags = text
            print(f"🔹 هشتگ‌ها تغییر یافت به: {hashtags}")
            await update.message.reply_text(f"🔹 هشتگ‌ها تغییر یافت به: {hashtags}")
        elif text.isdigit():
            global min_likes
            min_likes = int(text)
            print(f"🔹 حداقل لایک تنظیم شد: {min_likes}")
            await update.message.reply_text(f"🔹 حداقل لایک تنظیم شد: {min_likes}")
        else:
            print("❌ دستور نامعتبر است.")
            await update.message.reply_text("❌ دستور نامعتبر است.")
    except Exception as e:
        print(f"⚠️ خطا در پردازش پیام:\n{traceback.format_exc()}")

# ثبت دستورات ربات
application = Application.builder().token(TELEGRAM_API_KEY).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# صفحه اصلی وب
@app.route('/')
def home():
    return "✅ ربات تلگرام در حال اجرا است!"

# وب‌هوک
@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()
        print(f"📩 داده دریافتی:\n{data}")
        update = Update.de_json(data, application.bot)
        application.update_queue.put_nowait(update)
        print("✅ پیام به صف اضافه شد.")
        return 'ok', 200
    except Exception as e:
        print(f"⚠️ خطا در پردازش وب‌هوک:\n{traceback.format_exc()}")
        return 'error', 500

# تنظیم وب‌هوک در تلگرام
async def set_webhook():
    webhook_url = 'https://instabot2-1.onrender.com/webhook'
    try:
        await application.bot.set_webhook(webhook_url)
        print(f"✅ وب‌هوک به {webhook_url} تنظیم شد.")
    except Exception as e:
        print(f"❌ خطا در تنظیم وب‌هوک:\n{traceback.format_exc()}")

# اجرای برنامه
if __name__ == '__main__':
    # اجرای تنظیم وب‌هوک به صورت غیرهمزمان در پس‌زمینه
    loop = asyncio.get_event_loop()
    loop.create_task(set_webhook())
    # راه‌اندازی سرور Flask
    app.run(host="0.0.0.0", port=8080)
