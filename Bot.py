import time
import instaloader
import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from datetime import datetime
from flask import Flask
from instabot import Bot  # استفاده از Instabot برای ارسال پست‌ها در اینستاگرام

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

# متغیرهای جدید برای لایک و هشتگ
min_likes = 1000  # حداقل لایک برای انتخاب ویدیوها
hashtags = "#viral"  # هشتگ پیش‌فرض

# دانلود ویدیوهای ترند
def download_trending_videos():
    print("📥 در حال دانلود ویدیوهای ترند...")

    for hashtag in hashtags.split(","):
        try:
            posts = L.get_hashtag_posts(hashtag.strip())  # جستجو و دریافت پست‌های هشتگ
            for post in posts:
                if post.is_video and post.likes > min_likes:  # فیلتر ویدیوهای محبوب (بیش از 1000 لایک)
                    L.download_post(post, target="downloads")  # دانلود ویدیو
                    video_to_post.append(post)
                    print(f"✅ ویدیو {post.shortcode} با {post.likes} لایک دانلود شد.")
                    return
        except Exception as e:
            print(f"❌ خطا در دریافت ویدیوهای هشتگ #{hashtag}: {e}")

# تایید ویدیو توسط کاربر
async def approve_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(video_to_post) == 0:
        await update.message.reply_text("❌ هیچ ویدیویی برای ارسال وجود ندارد. لطفاً کمی صبر کنید تا ویدیو جدید دانلود شود.")
        download_trending_videos()  # درخواست دانلود ویدیوی جدید
        return

    post = video_to_post[0]
    caption = f"{post.caption} {hashtags}"

    # دکمه‌ها برای تایید یا رد ویدیو
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("تایید", callback_data="approve"),
         InlineKeyboardButton("رد", callback_data="reject")]
    ])

    await update.message.reply_video(
        video=open(f"downloads/{post.shortcode}.mp4", "rb"),
        caption=caption,
        reply_markup=keyboard)

# ارسال ویدیو به اینستاگرام
def post_to_instagram(video_path, caption):
    bot = Bot()  # ایجاد بوت اینستاگرام
    bot.login(username="your_instagram_username", password="your_instagram_password")  # وارد شدن به حساب اینستاگرام
    bot.upload_video(video_path, caption=caption)  # ارسال ویدیو به اینستاگرام

# کنترل انتخاب کاربر برای تایید یا رد پست
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data == "approve":
        post = video_to_post.pop(0)
        # ارسال ویدیو به اینستاگرام
        video_path = f"downloads/{post.shortcode}.mp4"
        caption = f"{post.caption} {hashtags}"
        post_to_instagram(video_path, caption)
        await query.message.reply_text("✅ پست تایید شد و در صفحه اینستاگرام ارسال خواهد شد.")
    elif query.data == "reject":
        video_to_post.pop(0)
        await query.message.reply_text("❌ پست رد شد و ویدیو جدید پیدا خواهد شد.")
        download_trending_videos()  # جستجوی ویدیو جدید

# تنظیم تعداد لایک و هشتگ‌ها از طریق دستورات ربات
async def set_min_likes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global min_likes
    try:
        min_likes = int(context.args[0])  # تغییر تعداد لایک‌ها
        await update.message.reply_text(f"حداقل لایک به {min_likes} تغییر یافت.")
    except (IndexError, ValueError):
        await update.message.reply_text("لطفاً یک عدد معتبر برای تعداد لایک وارد کنید.")

async def set_hashtags(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global hashtags
    hashtags = " ".join(context.args)  # تغییر هشتگ‌ها
    await update.message.reply_text(f"هشتگ‌ها به: {hashtags} تغییر یافت.")

# ایجاد دکمه‌ها برای دستورات اصلی
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("تایید ویدیو", callback_data="approve"),
         InlineKeyboardButton("تنظیم لایک‌ها", callback_data="set_likes"),
         InlineKeyboardButton("تنظیم هشتگ‌ها", callback_data="set_hashtags")]
    ])

    await update.message.reply_text("سلام! من ربات مدیریت اینستاگرام هستم. لطفاً یکی از گزینه‌ها را انتخاب کنید.", reply_markup=keyboard)

# ثبت دستورات
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("set_likes", set_min_likes))  # دستور برای تنظیم لایک
application.add_handler(CommandHandler("set_hashtags", set_hashtags))  # دستور برای تنظیم هشتگ‌ها
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
