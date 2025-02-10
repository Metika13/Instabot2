import os
import time
import random
import schedule
from pyrogram import Client, filters, types
from instaloader import Instaloader, Profile
import requests
from config import BOT_TOKEN, INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD
from datetime import datetime, timedelta
import sqlite3
from moviepy.editor import VideoFileClip
import logging

# تنظیمات لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

app = Client("my_account", api_id=YOUR_API_ID, api_hash=YOUR_API_HASH, bot_token=BOT_TOKEN)
loader = Instaloader()
loader.load_session_from_file(INSTAGRAM_USERNAME, "mtkh13o_session")

# --- پایگاه داده ---
conn = sqlite3.connect('bot_database.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        media_path TEXT,
        caption TEXT,
        hashtags TEXT,
        min_likes INTEGER,
        approved INTEGER DEFAULT 0,
        scheduled_time TEXT
    )
''')
conn.commit()

# --- توابع ---

def download_trending_videos(hashtag, min_likes):
    try:
        logger.info(f"شروع دانلود ویدیوهای ترند با هشتگ {hashtag} و حداقل لایک {min_likes}")
        loader.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
        posts = loader.get_hashtag_posts(hashtag)
        trending_videos = []
        for post in posts:
            if post.is_video and post.likes >= min_likes:
                trending_videos.append(post)
                if len(trending_videos) >= 5:
                    break
        logger.info(f"تعداد {len(trending_videos)} ویدیو دانلود شد.")
        return trending_videos
    except Exception as e:
        logger.error(f"خطا در دانلود ویدیوها: {e}")
        return []

def download_stories(usernames):
    try:
        logger.info(f"شروع دانلود استوری از صفحات {usernames}")
        stories = []
        for username in usernames:
            try:
                profile = Profile.from_username(loader.context, username)
                for story in profile.get_stories():
                    stories.append(story)
                if len(stories) >= 5:
                    break
            except Exception as e:
                logger.error(f"خطا در دانلود استوری از {username}: {e}")
        logger.info(f"تعداد {len(stories)} استوری دانلود شد.")
        return stories
    except Exception as e:
        logger.error(f"خطا در دانلود استوری‌ها: {e}")
        return []

def post_to_instagram(media_path, caption):
    try:
        logger.info(f"شروع ارسال پست به اینستاگرام: {media_path}")
        loader.login(INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD)
        loader.upload_post(media_path, caption=caption)
        logger.info(f"پست با موفقیت منتشر شد: {media_path}")
        return True
    except Exception as e:
        logger.error(f"خطا در ارسال پست به اینستاگرام: {e}")
        return False

def suggest_trending_videos():
    logger.info("در حال جستجوی ویدیوهای ترند از منابع دیگر...")
    # ... (کد جستجوی ویدیوها از منابع دیگر)
    return []

def process_media(media_path, caption, hashtags, min_likes):
    logger.info(f"رسانه برای تایید ذخیره شد: {media_path}")
    cursor.execute("INSERT INTO posts (media_path, caption, hashtags, min_likes) VALUES (?, ?, ?, ?)", (media_path, caption, hashtags, min_likes))
    conn.commit()
    return "رسانه برای تایید ذخیره شد."

def get_pending_posts():
    logger.info("در حال واکشی پست‌های pending...")
    cursor.execute("SELECT * FROM posts WHERE approved = 0")
    return cursor.fetchall()

def approve_post(post_id):
    logger.info(f"در حال تایید پست با ID: {post_id}")
    cursor.execute("UPDATE posts SET approved = 1 WHERE id = ?", (post_id,))
    conn.commit()
    return "پست تایید شد."

def reject_post(post_id):
    logger.info(f"در حال حذف پست با ID: {post_id}")
    cursor.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    return "پست حذف شد."

def schedule_post(post_id, scheduled_time):
    logger.info(f"در حال زمان‌بندی پست با ID: {post_id} برای زمان {scheduled_time}")
    cursor.execute("UPDATE posts SET scheduled_time = ? WHERE id = ?", (scheduled_time, post_id))
    conn.commit()
    return "زمان‌بندی پست ثبت شد."

def get_scheduled_posts():
    logger.info("در حال واکشی پست‌های زمان‌بندی شده...")
    cursor.execute("SELECT * FROM posts WHERE approved = 1 AND scheduled_time IS NOT NULL")
    return cursor.fetchall()

# --- دستورات ربات ---

@app.on_message(filters.command("start"))
def start_command(client, message):
    logger.info("کاربر وارد ربات شد.")
    keyboard = types.InlineKeyboardMarkup(
        [
            [
                types.InlineKeyboardButton("دانلود ویدیوهای ترند", callback_data="download_trending"),
                types.InlineKeyboardButton("دانلود استوری‌ها", callback_data="download_stories")
            ],
            [
                types.InlineKeyboardButton("مشاهده پست‌های pending", callback_data="pending_posts"),
                types.InlineKeyboardButton("مشاهده پست‌های زمان‌بندی شده", callback_data="scheduled_posts")
            ],
            [
                types.InlineKeyboardButton("تنظیم زمان‌بندی", callback_data="set_schedule")
            ]
        ]
    )
    message.reply_text("به ربات مدیریت اینستاگرام خوش آمدید!", reply_markup=keyboard)

@app.on_callback_query()
def handle_callback_query(client, query):
    if query.data == "download_trending":
        hashtag = "#explore"  # مقدار پیش فرض
        min_likes = 1000  # مقدار پیش فرض
        videos = download_trending_videos(hashtag, min_likes)
        if videos:
            for video in videos:
                media_path = f"{video.shortcode}.mp4"
                loader.download_post(video, filename=media_path)
                caption = f"{video.caption} #{hashtag}"
                hashtags = hashtag
                query.message.reply_text(process_media(media_path, caption, hashtags, min_likes))
        else:
            query.message.reply_text("ویدیویی با این هشتگ و حداقل لایک یافت نشد.")
    elif query.data == "download_stories":
        usernames = ["your_username1", "your_username2"] # لیست صفحات مورد نظر
        stories = download_stories(usernames)
        if stories:
            for story in stories:
                media_path = f"{story.user_id}_{story.date_utc.timestamp()}.{story.is_video and 'mp4' or 'jpg'}"
                loader.download_story(story, filename=media_path)
                query.message.reply_text(process_media(media_path, "", "", 0))
        else:
            query.message.reply_text("استوری‌ای از این صفحات یافت نشد.")
    elif query.data == "pending_posts":
        posts = get_pending_posts()
        if posts:
            for post in posts:
           message_text = f"ID: {post[0]}\nمسیر: {post[1]}\nکپشن: {post[2]}\nهشتگ‌ها: {post[3]}\nحداقل لایک: {post[4]}"
                # تقسیم پیام به بخش‌های کوچکتر
                for chunk in (message_text[i:i+1024] for i in range(0, len(message_text), 1024)):  # Parentheses instead of brackets
                     query.message.reply_text(chunk)  # This line MUST be indented
                for chunk in [message_text[i:i+1024] for i in range(0, len(message_text), 1024)]:
                    query.message.reply_text(chunk)
        else:
            query.message.reply_text("هیچ پست pending وجود ندارد.")
    elif query.data == "scheduled_posts":
        posts = get_scheduled_posts()
        if posts:
            for post in posts:
                message_text = f"ID: {post[0]}\nمسیر: {post[1]}\nکپشن: {post[2]}\nهشتگ‌ها: {post[3]}\nحداقل لایک: {post[4]}\nزمان‌بندی: {post[6]}"
                # تقسیم پیام به بخش‌های کوچکتر
                for chunk in [message_text[i:i+1024] for i in range(0, len(message_text), 1024)]:
                    query.message.reply_text(chunk)
        else:
            query.message.reply_text("هیچ پست زمان‌بندی شده وجود ندارد.")
    elif query.data == "set_schedule":
      #  کد تنظیم زمان‌بندی
        query.message.reply_text("برای تنظیم زمان‌بندی، لطفا ID پست و زمان مورد نظر خود را وارد کنید (به عنوان مثال: 1 2024-03-15 10:00:00).")

        @app.on_message(filters.regex(r"^\d+ \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"))
        def set_schedule_time(client, message):
            try:
                post_id, scheduled_time = message.text.split()
                schedule_post(int(post_id), scheduled_time)
                query.message.reply_text("زمان‌بندی با موفقیت ثبت شد.")
            except Exception as e:
                query.message.reply_text(f"خطا در تنظیم زمان‌بندی: {e}")

# --- زمان‌بندی ---

def schedule_posts():
    posts = get_scheduled_posts()
    for post in posts:
        if post[6] and post[6] <= datetime.now().strftime("%Y-%m-%d %H:%M:%S"): # scheduled time is passed
            if post_to_instagram(post[1], post[2]):
                cursor.execute("DELETE FROM posts WHERE id = ?", (post[0],))
                conn.commit()
                logger.info(f"پست با ID {post[0]} در اینستاگرام منتشر و از پایگاه داده حذف شد.")

schedule.every(10).minutes.do(schedule_posts) # هر 10 دقیقه اجرا شود
while True:
    schedule.run_pending()
    time.sleep(1)

app.run()
