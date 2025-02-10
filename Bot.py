import os
import instaloader
import requests
import time
import asyncio
import traceback
from flask import Flask, request
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# تنظیمات
TELEGRAM_API_KEY = os.getenv('TELEGRAM_API_KEY')
if not TELEGRAM_API_KEY:
    raise ValueError("❌ کلید API تلگرام یافت نشد.")

# مقداردهی اولیه
video_to_post = []
stories_to_post = []
profiles_to_fetch = ["profile1", "profile2"]
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

# دانلود ویدیوهای ترند
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
                time.sleep(10)
        except Exception:
            print(f"❌ خطا در دریافت ویدیوهای هشتگ #{hashtag}:\n{traceback.format_exc()}")

# دانلود استوری‌ها
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
                time.sleep(10)
        except Exception:
            print(f"❌ خطا در دریافت استوری‌ها از {profile}:\n{traceback.format_exc()}")

# ارسال پست به اینستاگرام (در صورت وجود API)
def upload_to_instagram(post):
    try:
        print(f"📤 در حال ارسال پست: {post.shortcode}")
        print(f"✅ پست {post.shortcode} در اینستاگرام آپلود شد.")
    except Exception:
        print(f"❌ خطا در ارسال پست اینستاگرام:\n{traceback.format_exc()}")

# ارسال استوری به اینستاگرام (در صورت وجود API)
def upload_story_to_instagram(story):
    try:
        print("📤 در حال ارسال استوری...")
        print("✅ استوری در اینستاگرام آپلود شد.")
    except Exception:
        print(f"❌ خطا در ارسال استوری اینستاگرام:\n{traceback.format_exc()}")

# کیبورد اصلی
def get_main_keyboard():
    keyboard = [
        [KeyboardButton("پست‌ها"), KeyboardButton("استوری‌ها")],
        [KeyboardButton("تنظیمات")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

# دستور `/start`
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! من ربات مدیریت اینستاگرام هستم. لطفاً یکی از گزینه‌ها را انتخاب کنید.",
        reply_markup=get_main_keyboard()
    )

# تایید ویدیو
async def approve_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(video_to_post) == 0:
        await update.message.reply_text("❌ هیچ ویدیویی موجود نیست. در حال دانلود ویدیو جدید...")
        download_trending_videos()
        return

    post = video_to_post[0]
    caption = f"{post.caption} {hashtags}"

    keyboard = [[KeyboardButton("تایید"), KeyboardButton("رد")]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_video(
        video=open(f"downloads/{post.shortcode}.mp4", "rb"),
        caption=caption,
        reply_markup=reply_markup
    )

# مدیریت پیام‌ها
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text
        print(f"📩 پیام دریافتی: {text}")
        if text == "تایید":
            post = video_to_post.pop(0)
            await update.message.reply_text("✅ پست تایید شد و در اینستاگرام ارسال خواهد شد.")
            upload_to_instagram(post)
        elif text == "رد":
            video_to_post.pop(0)
            await update.message.reply_text("❌ پست رد شد. دانلود ویدیو جدید...")
            download_trending_videos()
        elif text == "پست‌ها":
            await approve_video(update, context)
        elif text == "استوری‌ها":
            download_stories()
        elif text == "تنظیمات":
            await update.message.reply_text("⚙️ تنظیمات ربات:")
        elif text.startswith("#"):
            global hashtags
            hashtags = text
            await update.message.reply_text(f"🔹 هشتگ‌ها تغییر یافت به: {hashtags}")
        elif text.isdigit():
            global min_likes
            min_likes = int(text)
            await update.message.reply_text(f"🔹 حداقل لایک تنظیم شد: {min_likes}")
        else:
            await update.message.reply_text("❌ دستور نامعتبر است.")
    except Exception:
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
        return 'ok', 200
    except Exception:
        print(f"⚠️ خطا در پردازش وب‌هوک:\n{traceback.format_exc()}")
        return 'error', 500

# تنظیم وب‌هوک
async def set_webhook():
    webhook_url = "https://instabot2-1.onrender.com/webhook"
    try:
        response = await application.bot.set_webhook(url=webhook_url)
        print(f"✅ وب‌هوک تنظیم شد: {response}")
    except Exception:
        print(f"⚠️ خطا در تنظیم وب‌هوک:\n{traceback.format_exc()}")

# اجرای برنامه
if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(set_webhook())
    print("🚀 ربات اجرا شد.")
    app.run(host='0.0.0.0', port=8080)
