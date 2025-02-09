import os
import instaloader
import requests
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from flask import Flask, request

# ایجاد یک سرور HTTP ساده
app = Flask(__name__)

# تنظیمات ربات
TELEGRAM_API_KEY = os.getenv('TELEGRAM_API_KEY')
if not TELEGRAM_API_KEY:
    raise ValueError("کلید API تلگرام یافت نشد.")

# متغیرهای جدید برای لایک و هشتگ
min_likes = 1000  # حداقل لایک برای انتخاب ویدیوها
hashtags = "#viral"  # هشتگ پیش‌فرض
video_to_post = []  # لیست ویدیوهای دانلود شده

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
        except Exception as e:
            print(f"❌ خطا در دریافت ویدیوهای هشتگ #{hashtag}: {e}")

# ایجاد کیبورد پیش‌فرض
def get_reply_keyboard():
    keyboard = [
        [KeyboardButton("تایید ویدیو")],
        [KeyboardButton("تنظیم لایک‌ها"), KeyboardButton("تنظیم هشتگ‌ها")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=True)

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
        await update.message.reply_text("✅ پست تایید شد و در گروه/کانال ارسال خواهد شد.")
        await context.bot.send_video(chat_id=update.message.chat_id,
                                     video=open(f"downloads/{post.shortcode}.mp4", "rb"),
                                     caption=post.caption)
    elif text == "رد":
        video_to_post.pop(0)
        await update.message.reply_text("❌ پست رد شد و ویدیو جدید پیدا خواهد شد.")
        download_trending_videos()
    elif text == "تایید ویدیو":
        await approve_video(update, context)
    elif text == "تنظیم لایک‌ها":
        await update.message.reply_text("لطفاً تعداد لایک‌های مورد نظر را وارد کنید.")
    elif text == "تنظیم هشتگ‌ها":
        await update.message.reply_text("لطفاً هشتگ‌های مورد نظر را وارد کنید.")
    else:
        await update.message.reply_text("دستور نامعتبر است. لطفاً از کیبورد استفاده کنید.")

# تنظیم تعداد لایک و هشتگ‌ها از طریق دستورات ربات
async def set_min_likes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global min_likes
    try:
        min_likes = int(context.args[0])
        await update.message.reply_text(f"حداقل لایک به {min_likes} تغییر یافت.")
    except (IndexError, ValueError):
        await update.message.reply_text("لطفاً یک عدد معتبر برای تعداد لایک وارد کنید.")

async def set_hashtags(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global hashtags
    hashtags = " ".join(context.args)
    await update.message.reply_text(f"هشتگ‌ها به: {hashtags} تغییر یافت.")

# ایجاد دکمه‌ها برای دستورات اصلی
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "سلام! من ربات مدیریت اینستاگرام هستم. لطفاً یکی از گزینه‌ها را انتخاب کنید.",
        reply_markup=get_reply_keyboard()
    )

# ثبت دستورات
application = Application.builder().token(TELEGRAM_API_KEY).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("set_likes", set_min_likes))
application.add_handler(CommandHandler("set_hashtags", set_hashtags))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# وب‌هوک برای Render
@app.route('/')
def home():
    return "ربات تلگرام در حال اجرا است!"

@app.route('/webhook', methods=['POST'])
async def webhook():
    update = Update.de_json(await request.get_json(), application.bot)
    await application.update_queue.put(update)
    return 'ok'

# تنظیم وب‌هوک
async def set_webhook():
    webhook_url = "https://instabot2-1.onrender.com/webhook"
    await application.bot.set_webhook(url=webhook_url)
    print(f"Webhook set to: {webhook_url}")

# اجرای ربات
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
