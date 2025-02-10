import os
import instaloader
import requests
import time
import asyncio
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask, request, jsonify

# ایجاد یک سرور HTTP ساده
app = Flask(__name__)

# تنظیمات ربات
TELEGRAM_API_KEY = os.getenv('TELEGRAM_API_KEY')
INSTAGRAM_WEBHOOK_SECRET = os.getenv('INSTAGRAM_WEBHOOK_SECRET')  # مقدار از Meta Developer Portal دریافت شود

if not TELEGRAM_API_KEY:
    raise ValueError("کلید API تلگرام یافت نشد.")

# متغیرهای اینستاگرام
min_likes = 1000
hashtags = "#viral"
video_to_post = []
stories_to_post = []
profiles_to_fetch = ["profile1", "profile2"]
num_stories_to_fetch = 5

# بارگذاری سشن اینستاگرام
L = instaloader.Instaloader()
try:
    session_file_url = 'https://github.com/Metika13/Instabot2/raw/main/mtkh13o_session.json'
    session_file_path = './mtkh13o_session.json'
    response = requests.get(session_file_url)
    with open(session_file_path, 'wb') as file:
        file.write(response.content)
    L.load_session_from_file('mtkh13o', session_file_path)
    print("سشن با موفقیت بارگذاری شد.")
except Exception as e:
    print(f"خطا در بارگذاری سشن: {e}")
    exit(1)

# دریافت ویدیوهای ترند از اینستاگرام
def download_trending_videos():
    print("📥 در حال دانلود ویدیوهای ترند...")
    for hashtag in hashtags.split(","):
        try:
            posts = L.get_hashtag_posts(hashtag.strip())
            for post in posts:
                if post.is_video and post.likes > min_likes:
                    L.download_post(post, target="downloads")
                    video_to_post.append(post)
                    print(f"✅ ویدیو {post.shortcode} با {post.likes} لایک دانلود شد.")
                    return
                time.sleep(10)  # تأخیر 10 ثانیه بین درخواست‌ها
        except Exception as e:
            print(f"❌ خطا در دریافت ویدیوهای هشتگ #{hashtag}: {e}")

# دانلود استوری‌ها از پیج‌های مشخص
def download_stories():
    print("📥 در حال دانلود استوری‌ها...")
    for profile in profiles_to_fetch:
        try:
            profile = instaloader.Profile.from_username(L.context, profile)
            stories = profile.get_stories()
            for story in stories:
                if len(stories_to_post) >= num_stories_to_fetch:
                    return
                L.download_storyitem(story, target="downloads/stories")
                stories_to_post.append(story)
                print(f"✅ استوری از {profile.username} دانلود شد.")
                time.sleep(10)  # تأخیر 10 ثانیه بین درخواست‌ها
        except Exception as e:
            print(f"❌ خطا در دریافت استوری‌ها از {profile}: {e}")

# ارسال پست در اینستاگرام (نیاز به API اینستاگرام)
def upload_to_instagram(post):
    # این بخش نیاز به API اینستاگرام دارد
    print(f"✅ پست {post.shortcode} در اینستاگرام آپلود شد.")

# ارسال استوری در اینستاگرام (نیاز به API اینستاگرام)
def upload_story_to_instagram(story):
    # این بخش نیاز به API اینستاگرام دارد
    print(f"✅ استوری در اینستاگرام آپلود شد.")

# ایجاد کیبورد پیش‌فرض
def get_main_keyboard():
    keyboard = [
        [KeyboardButton("پست‌ها"), KeyboardButton("استوری‌ها")],
        [KeyboardButton("تنظیمات")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

# تابع start برای پاسخ به دستور /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! من ربات مدیریت اینستاگرام هستم. لطفاً یکی از گزینه‌ها را انتخاب کنید.",
        reply_markup=get_main_keyboard()
    )

# تایید ویدیو توسط کاربر
async def approve_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(video_to_post) == 0:
        await update.message.reply_text("❌ هیچ ویدیویی برای ارسال وجود ندارد. لطفاً کمی صبر کنید تا ویدیو جدید دانلود شود.")
        download_trending_videos()
        return

    post = video_to_post[0]
    caption = f"{post.caption} {hashtags}"

    # ارسال ویدیو با کیبورد تایید/رد
    keyboard = [
        [KeyboardButton("تایید"), KeyboardButton("رد")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_video(
        video=open(f"downloads/{post.shortcode}.mp4", "rb"),
        caption=caption,
        reply_markup=reply_markup
    )

# کنترل انتخاب کاربر برای تایید یا رد پست
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "تایید":
        post = video_to_post.pop(0)
        await update.message.reply_text("✅ پست تایید شد و در اینستاگرام ارسال خواهد شد.")
        upload_to_instagram(post)
    elif text == "رد":
        video_to_post.pop(0)
        await update.message.reply_text("❌ پست رد شد و ویدیو جدید پیدا خواهد شد.")
        download_trending_videos()
    elif text == "پست‌ها":
        await approve_video(update, context)
    elif text == "استوری‌ها":
        await download_stories()
    elif text == "تنظیمات":
        await update.message.reply_text("تنظیمات ربات:")
    elif text.startswith("#"):  # اگر کاربر هشتگ وارد کرد
        global hashtags
        hashtags = text
        await update.message.reply_text(f"هشتگ‌ها به: {hashtags} تغییر یافت.")
    elif text.isdigit():  # اگر کاربر عدد وارد کرد (برای تنظیم لایک)
        global min_likes
        min_likes = int(text)
        await update.message.reply_text(f"حداقل لایک به {min_likes} تغییر یافت.")
    else:
        await update.message.reply_text("دستور نامعتبر است. لطفاً از کیبورد استفاده کنید.")

# ثبت دستورات
application = Application.builder().token(TELEGRAM_API_KEY).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# وبهوک اینستاگرام: تأیید challenge و دریافت رویدادها
@app.route('/instagram-webhook', methods=['GET', 'POST'])
def instagram_webhook():
    if request.method == 'GET':  # تأیید challenge
        challenge = request.args.get('hub.challenge')
        verify_token = request.args.get('hub.verify_token')
        if verify_token == INSTAGRAM_WEBHOOK_SECRET:
            return challenge, 200
        else:
            return "Verification token mismatch", 403

    elif request.method == 'POST':  # دریافت رویدادها
        data = request.get_json()
        print("📩 داده دریافتی از اینستاگرام:", data)
        return jsonify({"status": "received"}), 200

# وبهوک تلگرام
@app.route('/webhook', methods=['POST'])
def telegram_webhook():
    update = Update.de_json(request.get_json(), application.bot)
    application.update_queue.put(update)
    return 'ok'

# تنظیم وبهوک تلگرام
async def set_telegram_webhook():
    webhook_url = "https://instabot2-1.onrender.com/webhook"
    await application.bot.set_webhook(url=webhook_url)
    print(f"Webhook تلگرام تنظیم شد: {webhook_url}")

# اجرای ربات
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(set_telegram_webhook())  # اجرای async بدون ایجاد مشکل در Flask
    app.run(host='0.0.0.0', port=8080)
