import time
import instaloader
import schedule
import requests
import os
import threading
from flask import Flask
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ایجاد سرور HTTP ساده برای حفظ آنلاین بودن ربات
app = Flask(__name__)

@app.route('/')
def home():
    return "ربات تلگرام در حال اجرا است!"

# دانلود فایل سشن از گیت‌هاب
session_file_url = 'https://github.com/Metika13/Instabot2/raw/main/mtkh13o_session.json'
session_file_path = './mtkh13o_session.json'

try:
    response = requests.get(session_file_url)
    with open(session_file_path, 'wb') as file:
        file.write(response.content)
    print("✅ فایل سشن با موفقیت دانلود شد.")
except Exception as e:
    print(f"❌ خطا در دانلود فایل سشن: {e}")
    exit(1)

# بارگذاری سشن اینستاگرام
L = instaloader.Instaloader()
try:
    L.load_session_from_file('mtkh13o', session_file_path)
    print("✅ سشن اینستاگرام بارگذاری شد.")
except Exception as e:
    print(f"❌ خطا در بارگذاری سشن: {e}")
    exit(1)

# تنظیمات ربات
TELEGRAM_API_KEY = os.getenv('TELEGRAM_API_KEY')
if not TELEGRAM_API_KEY:
    print("❌ کلید API تلگرام یافت نشد.")
    exit(1)

# ایجاد برنامه تلگرام
application = Application.builder().token(TELEGRAM_API_KEY).build()

# لیست پست‌های دانلود شده
video_to_post = []
hashtags = ["viral", "trending", "fyp", "explore"]  # لیست هشتگ‌ها

# دریافت ویدیوهای محبوب از اینستاگرام
def download_trending_videos():
    print("📥 در حال دانلود ویدیوهای ترند...")
    
    for hashtag in hashtags:
        try:
            posts = L.get_hashtag_posts(hashtag)
            for post in posts:
                if post.is_video and post.likes > 1000:  # فیلتر ویدیوهای محبوب (بیش از 1000 لایک)
                    L.download_post(post, target="downloads")  # دانلود ویدیو
                    video_to_post.append(post)
                    print(f"✅ ویدیو {post.shortcode} با {post.likes} لایک دانلود شد.")
                    return
        except Exception as e:
            print(f"❌ خطا در دریافت ویدیوهای هشتگ #{hashtag}: {e}")

# دکمه‌های کیبورد معمولی
reply_keyboard = [
    [KeyboardButton("✅ تأیید پست"), KeyboardButton("❌ رد پست")],
    [KeyboardButton("🔄 دریافت ویدیوی جدید")]
]
reply_markup = ReplyKeyboardMarkup(reply_keyboard, resize_keyboard=True)

# ارسال ویدیو برای تأیید
async def send_post_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(video_to_post) == 0:
        await update.message.reply_text("❌ هیچ ویدیویی برای ارسال وجود ندارد.")
        return

    post = video_to_post[0]
    caption = f"{post.caption} #viral #trending"

    await update.message.reply_video(
        video=open(f"downloads/{post.shortcode}.mp4", "rb"),
        caption=caption,
        reply_markup=reply_markup
    )

# دریافت انتخاب کاربر
async def handle_reply_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "✅ تأیید پست":
        if len(video_to_post) > 0:
            post = video_to_post.pop(0)
            await update.message.reply_text("✅ پست تأیید شد و در حال ارسال به تلگرام است...")

            await context.bot.send_video(
                chat_id=update.effective_chat.id,
                video=open(f"downloads/{post.shortcode}.mp4", "rb"),
                caption=post.caption
            )
        else:
            await update.message.reply_text("❌ لیست پست‌ها خالی است!")

    elif text == "❌ رد پست":
        if len(video_to_post) > 0:
            video_to_post.pop(0)
            await update.message.reply_text("❌ پست رد شد. در حال جستجوی ویدیوی جدید...")
            download_trending_videos()
        else:
            await update.message.reply_text("❌ هیچ ویدیویی برای رد کردن وجود ندارد.")

    elif text == "🔄 دریافت ویدیوی جدید":
        await update.message.reply_text("🔍 در حال دریافت ویدیوی جدید از اینستاگرام...")
        download_trending_videos()
        await send_post_options(update, context)

# دستور `/start`
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 سلام! من ربات مدیریت اینستاگرام هستم.", reply_markup=reply_markup)

# ثبت دستورات
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_reply_buttons))

# اجرای سرور HTTP
def run_flask_app():
    app.run(host='0.0.0.0', port=8080)

flask_thread = threading.Thread(target=run_flask_app)
flask_thread.start()

# زمان‌بندی دانلود ویدیوها
schedule.every(30).minutes.do(download_trending_videos)

# اجرای زمان‌بندی در پس‌زمینه
def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(10)

scheduler_thread = threading.Thread(target=run_scheduler)
scheduler_thread.start()

# شروع ربات تلگرام
print("🤖 ربات در حال اجرا است...")
application.run_polling()
