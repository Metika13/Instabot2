import os
import instaloader
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from dotenv import load_dotenv

# بارگذاری متغیرها از فایل .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
SESSION_FILE = os.getenv("SESSION_FILE")
CHAT_ID = os.getenv("CHAT_ID")
HASHTAG = os.getenv("HASHTAG")
SOURCE_PAGE = os.getenv("SOURCE_PAGE")
MIN_LIKES = int(os.getenv("MIN_LIKES"))
MIN_VIEWS = int(os.getenv("MIN_VIEWS"))
POST_INTERVAL = int(os.getenv("POST_INTERVAL"))

# راه‌اندازی ربات
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
scheduler = AsyncIOScheduler()

# راه‌اندازی Instaloader
loader = instaloader.Instaloader()
loader.load_session_from_file(SESSION_FILE)

# دکمه‌های کیبورد
keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add(KeyboardButton("📥 دانلود پست ترند"))
keyboard.add(KeyboardButton("📸 دانلود استوری"))
keyboard.add(KeyboardButton("⚙️ تنظیمات"))

# تابع دانلود پست ترند با فیلتر لایک و ویو
def download_trending_videos():
    posts = loader.get_hashtag_posts(HASHTAG)
    for post in posts:
        if post.is_video and post.likes >= MIN_LIKES and post.video_view_count >= MIN_VIEWS:
            loader.download_post(post, target="downloads")
            return f"downloads/{post.shortcode}.mp4"
    return None

# ارسال ویدیو به کانال
async def send_video():
    video = download_trending_videos()
    if video:
        await bot.send_video(CHAT_ID, open(video, 'rb'), caption="🎥 ویدیو ترند اینستاگرام!")
    else:
        await bot.send_message(CHAT_ID, "⚠️ ویدیویی با حداقل لایک و ویو پیدا نشد.")

# تابع دانلود استوری
def download_stories():
    loader.download_profiles([SOURCE_PAGE], profile_pic=False, stories=True)
    return [f for f in os.listdir('downloads') if f.endswith('.mp4')]

# تایید یا رد استوری
@dp.message_handler(lambda message: message.text == "📸 دانلود استوری")
async def handle_stories(message: types.Message):
    stories = download_stories()
    for story in stories:
        await bot.send_video(message.chat.id, open(story, 'rb'), caption="✅ تایید یا ❌ رد؟")

@dp.message_handler(lambda message: message.text == "✅ تایید")
async def approve_story(message: types.Message):
    await bot.send_video(CHAT_ID, open(message.reply_to_message.video.file_id, 'rb'), caption="📢 استوری تأیید شده!")

@dp.message_handler(lambda message: message.text == "❌ رد")
async def reject_story(message: types.Message):
    await message.reply("🚫 استوری رد شد.")

# تنظیمات
@dp.message_handler(lambda message: message.text == "⚙️ تنظیمات")
async def settings_menu(message: types.Message):
    settings_kb = ReplyKeyboardMarkup(resize_keyboard=True)
    settings_kb.add(KeyboardButton("🔄 تغییر هشتگ"))
    settings_kb.add(KeyboardButton("🔄 تغییر منبع استوری"))
    settings_kb.add(KeyboardButton("🔄 تغییر حداقل لایک/ویو"))
    settings_kb.add(KeyboardButton("🔄 تغییر زمان ارسال"))
    settings_kb.add(KeyboardButton("🔙 بازگشت"))
    await message.reply("⚙️ تنظیمات را انتخاب کنید:", reply_markup=settings_kb)

@dp.message_handler(lambda message: message.text == "🔄 تغییر هشتگ")
async def change_hashtag(message: types.Message):
    await message.reply("🔹 هشتگ جدید را ارسال کنید:")

@dp.message_handler(lambda message: message.text.startswith("#"))
async def set_hashtag(message: types.Message):
    global HASHTAG
    HASHTAG = message.text[1:]
    await message.reply(f"✅ هشتگ تغییر کرد به: {HASHTAG}")

@dp.message_handler(lambda message: message.text == "🔄 تغییر منبع استوری")
async def change_source_page(message: types.Message):
    await message.reply("🔹 نام صفحه جدید را ارسال کنید:")

@dp.message_handler(lambda message: message.text.startswith("@"))
async def set_source_page(message: types.Message):
    global SOURCE_PAGE
    SOURCE_PAGE = message.text[1:]
    await message.reply(f"✅ منبع استوری تغییر کرد به: {SOURCE_PAGE}")

@dp.message_handler(lambda message: message.text == "🔄 تغییر حداقل لایک/ویو")
async def change_min_likes_views(message: types.Message):
    await message.reply("🔹 حداقل تعداد لایک و ویو را با فرمت `لایک,ویو` ارسال کنید (مثال: 5000,20000)")

@dp.message_handler(lambda message: "," in message.text)
async def set_min_likes_views(message: types.Message):
    global MIN_LIKES, MIN_VIEWS
    likes, views = message.text.split(",")
    MIN_LIKES = int(likes.strip())
    MIN_VIEWS = int(views.strip())
    await message.reply(f"✅ حداقل لایک: {MIN_LIKES}, حداقل ویو: {MIN_VIEWS}")

@dp.message_handler(lambda message: message.text == "🔄 تغییر زمان ارسال")
async def change_post_interval(message: types.Message):
    await message.reply("🔹 زمان‌بندی جدید (به ساعت) را ارسال کنید:")

@dp.message_handler(lambda message: message.text.isdigit())
async def set_post_interval(message: types.Message):
    global POST_INTERVAL
    POST_INTERVAL = int(message.text)
    scheduler.remove_all_jobs()
    scheduler.add_job(send_video, 'interval', hours=POST_INTERVAL)
    await message.reply(f"✅ زمان‌بندی تغییر کرد به: {POST_INTERVAL} ساعت")

# زمان‌بندی ارسال پست
scheduler.add_job(send_video, 'interval', hours=POST_INTERVAL)
scheduler.start()

# استارت ربات
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    await message.reply("🤖 خوش آمدید! از دکمه‌های زیر استفاده کنید:", reply_markup=keyboard)

if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp)
