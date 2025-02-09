import os
import instaloader
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
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

# تایید ویدیو توسط کاربر
async def approve_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(video_to_post) == 0:
        await update.message.reply_text("❌ هیچ ویدیویی برای ارسال وجود ندارد. لطفاً کمی صبر کنید تا ویدیو جدید دانلود شود.")
        download_trending_videos()
        return

    post = video_to_post[0]
    caption = f"{post.caption} {hashtags}"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("تایید", callback_data="approve"),
         InlineKeyboardButton("رد", callback_data="reject")]
    ])

    await update.message.reply_video(
        video=open(f"downloads/{post.shortcode}.mp4", "rb"),
        caption=caption,
        reply_markup=keyboard)

# کنترل انتخاب کاربر برای تایید یا رد پست
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "approve":
        post = video_to_post.pop(0)
        await query.message.reply_text("✅ پست تایید شد و در گروه/کانال ارسال خواهد شد.")
        await context.bot.send_video(chat_id=query.message.chat_id,
                                     video=open(f"downloads/{post.shortcode}.mp4", "rb"),
                                     caption=post.caption)
    elif query.data == "reject":
        video_to_post.pop(0)
        await query.message.reply_text("❌ پست رد شد و ویدیو جدید پیدا خواهد شد.")
        download_trending_videos()

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
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("تایید ویدیو", callback_data="approve_video")],
        [InlineKeyboardButton("تنظیم لایک‌ها", callback_data="set_likes"),
         InlineKeyboardButton("تنظیم هشتگ‌ها", callback_data="set_hashtags")]
    ])
    await update.message.reply_text("سلام! من ربات مدیریت اینستاگرام هستم. لطفاً یکی از گزینه‌ها را انتخاب کنید.", reply_markup=keyboard)

# ثبت دستورات
application = Application.builder().token(TELEGRAM_API_KEY).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("set_likes", set_min_likes))
application.add_handler(CommandHandler("set_hashtags", set_hashtags))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, approve_video))
application.add_handler(CallbackQueryHandler(button))

# وب‌هوک برای Render
@app.route('/webhook', methods=['POST'])
async def webhook():
    update = Update.de_json(await request.get_json(), application.bot)
    await application.update_queue.put(update)
    return 'ok'

# اجرای ربات
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
