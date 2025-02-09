import time
import instaloader
import schedule
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, CallbackContext, CallbackQueryHandler
from datetime import datetime
import os
import requests

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

updater = Updater(TELEGRAM_API_KEY, use_context=True)
dispatcher = updater.dispatcher

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
def approve_video(update: Update, context: CallbackContext):
    if len(video_to_post) == 0:
        update.message.reply_text("هیچ ویدیویی برای ارسال وجود ندارد.")
        return

    post = video_to_post[0]
    caption = f"{post.caption} {hashtags}"

    update.message.reply_video(
        video=open(f"downloads/{post.shortcode}.mp4", "rb"),
        caption=caption,
        reply_markup=InlineKeyboardMarkup([  # ایجاد دکمه‌ها برای تایید و عدم تایید
            [InlineKeyboardButton("تایید", callback_data="approve"),
             InlineKeyboardButton("عدم تایید", callback_data="reject")]
        ]))
    
# کنترل انتخاب کاربر برای تایید یا رد پست
def button(update: Update, context: CallbackContext):
    query = update.callback_query
    if query.data == "approve":
        post = video_to_post.pop(0)
        # ارسال پست در کانال یا گروه
        query.message.reply_text("پست تایید شد.")
        # ارسال به تلگرام
        context.bot.send_video(chat_id=update.message.chat_id,
                               video=open(f"downloads/{post.shortcode}.mp4", "rb"),
                               caption=post.caption)
    elif query.data == "reject":
        video_to_post.pop(0)
        query.message.reply_text("پست رد شد و ویدیو جدید پیدا خواهد شد.")
        download_trending_videos()  # جستجوی ویدیو جدید

# زمان‌بندی ارسال پست‌ها
def schedule_posts():
    schedule.every(10).minutes.do(download_trending_videos)  # هر 10 دقیقه یک بار ویدیو دانلود می‌شود

    while True:
        schedule.run_pending()
        time.sleep(1)

# شروع ربات
def start(update: Update, context: CallbackContext):
    update.message.reply_text("سلام! من ربات مدیریت اینستاگرام هستم.")

def main():
    # ثبت دستورات
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(filters.text & ~filters.command, approve_video))
    dispatcher.add_handler(CallbackQueryHandler(button))

    # شروع ربات تلگرام
    updater.start_polling()

    # شروع زمان‌بندی ارسال پست‌ها
    schedule_posts()

if __name__ == '__main__':
    main()
