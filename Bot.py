import time
import instaloader
import schedule
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from datetime import datetime
import os
import requests
from flask import Flask

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

application = Application.builder().token(TELEGRAM_API_KEY).build()

# تعریف متغیرها
video_to_post = []
hashtags = "#viral"

# دریافت ویدیو از هشتگ
def download_videos_by_hashtag(hashtag):
    print(f"🔍 در حال دریافت ویدیوهای هشتگ #{hashtag} ...")
    posts = instaloader.Hashtag.from_name(L.context, hashtag).get_posts()

    for post in posts:
        if post.is_video:
            L.download_post(post, target="downloads")
            video_to_post.append(post)
            print(f"✅ ویدیو {post.shortcode} دانلود شد.")
            break

# دریافت محبوب‌ترین ویدیو از هشتگ
def get_most_popular_video(hashtag):
    print(f"🔥 در حال دریافت محبوب‌ترین ویدیو از #{hashtag} ...")
    posts = instaloader.Hashtag.from_name(L.context, hashtag).get_posts()

    best_post = None
    max_likes = 0

    for post in posts:
        if post.is_video and post.likes > max_likes:
            best_post = post
            max_likes = post.likes

    if best_post:
        L.download_post(best_post, target="downloads")
        video_to_post.append(best_post)
        print(f"✅ محبوب‌ترین ویدیو {best_post.shortcode} دانلود شد.")

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
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ تایید", callback_data="approve"),
             InlineKeyboardButton("❌ رد", callback_data="reject")]
        ])
    )

# کنترل دکمه‌ها
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "approve":
        post = video_to_post.pop(0)
        await query.message.reply_text("✅ پست تایید شد.")
        await context.bot.send_video(chat_id=update.effective_chat.id,
                                     video=open(f"downloads/{post.shortcode}.mp4", "rb"),
                                     caption=post.caption)

    elif query.data == "reject":
        video_to_post.pop(0)
        await query.message.reply_text("❌ پست رد شد و ویدیو جدید دریافت خواهد شد.")

# دریافت هشتگ از کاربر
async def handle_hashtag(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "waiting_for_hashtag" in context.user_data and context.user_data["waiting_for_hashtag"]:
        hashtag = update.message.text.replace("#", "")
        await update.message.reply_text(f"🔍 در حال دریافت ویدیوهای مرتبط با #{hashtag} ...")
        download_videos_by_hashtag(hashtag)
        context.user_data["waiting_for_hashtag"] = False

    elif "waiting_for_popular" in context.user_data and context.user_data["waiting_for_popular"]:
        hashtag = update.message.text.replace("#", "")
        await update.message.reply_text(f"🔥 در حال دریافت محبوب‌ترین ویدیو از #{hashtag} ...")
        get_most_popular_video(hashtag)
        context.user_data["waiting_for_popular"] = False

# منوی اصلی ربات
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📥 دریافت ویدیو با هشتگ", callback_data="download_by_hashtag")],
        [InlineKeyboardButton("🔥 دریافت محبوب‌ترین ویدیو", callback_data="download_popular")],
        [InlineKeyboardButton("🎬 بررسی ویدیوها", callback_data="approve_video")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🔹 لطفاً یکی از گزینه‌های زیر را انتخاب کنید:", reply_markup=reply_markup)

# اجرای سرور HTTP برای حفظ اجرای ربات
def run_flask_app():
    app.run(host='0.0.0.0', port=8080)

import threading
flask_thread = threading.Thread(target=run_flask_app)
flask_thread.start()

# ثبت دستورات و دکمه‌ها
application.add_handler(CommandHandler("start", main_menu))
application.add_handler(CallbackQueryHandler(button_handler))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_hashtag))

# شروع ربات تلگرام
print("🤖 ربات در حال اجرا است...")
application.run_polling()
