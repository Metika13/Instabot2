import time
import instaloader
import schedule
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from datetime import datetime
import os
import requests
from flask import Flask  # اضافه کردن Flask برای ایجاد سرور HTTP

# ایجاد یک سرور HTTP ساده
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
    print("فایل سشن با موفقیت دانلود شد.")
except Exception as e:
    print(f"خطا در دانلود فایل سشن: {e}")
    exit(1)

# بارگذاری سشن
L = instaloader.Instaloader()
try:
    L.load_session_from_file('mtkh13o', session_file_path)
    print("سشن با موفقیت بارگذاری شد.")
except Exception as e:
    print(f"خطا در بارگذاری سشن: {e}")
    exit(1)

# تنظیمات ربات
TELEGRAM_API_KEY = os.getenv('TELEGRAM_API_KEY')
if not TELEGRAM_API_KEY:
    print("کلید API تلگرام یافت نشد.")
    exit(1)

# ایجاد برنامه تلگرام
application = Application.builder().token(TELEGRAM_API_KEY).build()

# تعریف متغیرها
video_to_post = []
hashtags = "#viral"  # هشتگ برای جستجوی ویدیوهای وایرال

# دریافت ویدیوهای ترند از اینستاگرام
def download_trending_videos():
    print("در حال دانلود ویدیوهای ترند...")
    profile = instaloader.Profile.from_username(L.context, "instagram")  # صفحه اینستاگرام
    for post in profile.get_posts():
        if post.is_video:
            L.download_post(post, target="downloads")  # دانلود ویدیوها
            video_to_post.append(post)
            break  # برای دانلود فقط یک ویدیو در هر بار

# تایید ویدیو توسط کاربر
async def approve_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(video_to_post) == 0:
        await update.message.reply_text("هیچ ویدیویی برای ارسال وجود ندارد.")
        return

    post = video_to_post[0]
    caption = f"{post.caption} {hashtags}"

    await update.message.reply_video(
        video=open(f"downloads/{post.shortcode}.mp4", "rb"),
        caption=caption,
        reply_markup=InlineKeyboardMarkup([  # ایجاد دکمه‌ها برای تایید و عدم تایید
            [InlineKeyboardButton("تایید", callback_data="approve"),
             InlineKeyboardButton("عدم تایید", callback_data="reject")]
        ]))

# کنترل انتخاب کاربر برای تایید یا رد پست
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "approve":
        post = video_to_post.pop(0)
        # ارسال پست در کانال یا گروه
        await query.message.reply_text("پست تایید شد.")
        # ارسال به تلگرام
        await context.bot.send_video(chat_id=update.message.chat_id,
                                     video=open(f"downloads/{post.shortcode}.mp4", "rb"),
                                     caption=post.caption)
    elif query.data == "reject":
        video_to_post.pop(0)
        await query.message.reply_text("پست رد شد و ویدیو جدید پیدا خواهد شد.")
        download_trending_videos()  # جستجوی ویدیو جدید

# شروع ربات
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("سلام! من ربات مدیریت اینستاگرام هستم.")

# ثبت دستورات
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, approve_video))
application.add_handler(CallbackQueryHandler(button))

# اجرای سرور HTTP روی پورت 8080
def run_flask_app():
    app.run(host='0.0.0.0', port=8080)

# اجرای سرور HTTP در یک thread جداگانه
import threading
flask_thread = threading.Thread(target=run_flask_app)
flask_thread.start()

# شروع ربات تلگرام
print("ربات در حال اجرا است...")
application.run_polling()
