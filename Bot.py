import requests
import instaloader
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
import schedule
import time

# URL فایل سشن در گیت‌هاب
SESSION_URL = "https://github.com/yourusername/yourrepository/raw/main/mtkh13o.session"
SESSION_FILE = "mtkh13o.session"

# بارگذاری فایل سشن از گیت‌هاب
def download_session_file():
    try:
        print("در حال دانلود فایل سشن...")
        response = requests.get(SESSION_URL)
        with open(SESSION_FILE, 'wb') as file:
            file.write(response.content)
        print("فایل سشن با موفقیت دانلود شد.")
    except Exception as e:
        print(f"خطا در دانلود فایل سشن: {e}")

# ورود به اینستاگرام با استفاده از سشن
def login_instagram():
    L = instaloader.Instaloader()
    
    try:
        # بارگذاری سشن از فایل
        L.load_session_from_file(SESSION_FILE)
        print("با موفقیت وارد اینستاگرام شدید.")
    except FileNotFoundError:
        print("فایل سشن یافت نشد، لطفاً دوباره وارد شوید.")
        username = input("نام کاربری اینستاگرام: ")
        password = input("رمز عبور اینستاگرام: ")
        L.context.log("در حال ورود...")
        L.login(username, password)
        L.save_session_to_file(SESSION_FILE)
        print("سشن ذخیره شد.")
    return L

# ارسال و پست و استوری از ویدیوهای دانلود شده
async def post_video_to_telegram(update: Update, context: CallbackContext):
    # بررسی و دانلود ویدیو
    video_url = "https://www.instagram.com/p/xxxxxx/"  # آدرس ویدیو یا پست اینستاگرام
    L = login_instagram()
    post = instaloader.Post.from_shortcode(L.context, video_url.split("/")[-2])
    
    # بررسی وضعیت پست و ارسال به تلگرام
    if post.is_video:
        video_file = post.url
        await update.message.chat.send_video(video=video_file)
        await update.message.reply_text("ویدیو با موفقیت ارسال شد.")
    else:
        await update.message.reply_text("این پست ویدیو نیست.")

# زمان‌بندی برای ارسال پست‌ها
def schedule_posting(update: Update, context: CallbackContext):
    # برنامه‌ریزی ارسال در زمان خاص
    schedule.every().day.at("12:00").do(post_video_to_telegram, update=update, context=context)
    update.message.reply_text("برنامه‌ریزی ارسال پست با موفقیت انجام شد.")

    while True:
        schedule.run_pending()
        time.sleep(1)

# ایجاد و راه‌اندازی ربات تلگرام
def main():
    # توکن ربات تلگرام خود را وارد کنید
    TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN"

    # ایجاد اپلیکیشن برای ربات تلگرام
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # دستورات ربات
    application.add_handler(CommandHandler("start", lambda update, context: update.message.reply_text("سلام! من ربات تلگرام هستم.")))
    application.add_handler(CommandHandler("post", post_video_to_telegram))
    application.add_handler(CommandHandler("schedule", schedule_posting))

    # شروع ربات
    application.run_polling()

# اجرای ربات
if __name__ == '__main__':
    # دانلود فایل سشن از گیت‌هاب
    download_session_file()
    # اجرای ربات تلگرام
    main()
