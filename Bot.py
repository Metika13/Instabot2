import os
import time
import random
import schedule
from pyrogram import Client, filters, types
from instaloader import Instaloader, Profile
import requests
from config import BOT_TOKEN, CHANNEL_ID, INSTAGRAM_USERNAME, INSTAGRAM_PASSWORD
from datetime import datetime, timedelta
import sqlite3
from moviepy.editor import VideoFileClip

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

# ... (توابع دانلود و ارسال پست به اینستاگرام بدون تغییر)

def process_media(media_path, caption, hashtags, min_likes):
    cursor.execute("INSERT INTO posts (media_path, caption, hashtags, min_likes) VALUES (?, ?, ?, ?)", (media_path, caption, hashtags, min_likes))
    conn.commit()
    return "رسانه برای تایید ذخیره شد."

def get_pending_posts():
    cursor.execute("SELECT * FROM posts WHERE approved = 0")
    return cursor.fetchall()

def approve_post(post_id):
    cursor.execute("UPDATE posts SET approved = 1 WHERE id = ?", (post_id,))
    conn.commit()
    return "پست تایید شد."

def reject_post(post_id):
    cursor.execute("DELETE FROM posts WHERE id = ?", (post_id,))
    conn.commit()
    return "پست حذف شد."

def schedule_post(post_id, scheduled_time):
    cursor.execute("UPDATE posts SET scheduled_time = ? WHERE id = ?", (scheduled_time, post_id))
    conn.commit()
    return "زمان‌بندی پست ثبت شد."

def get_scheduled_posts():
    cursor.execute("SELECT * FROM posts WHERE approved = 1 AND scheduled_time IS NOT NULL")
    return cursor.fetchall()

# --- دستورات ربات ---

@app.on_message(filters.command("start"))
def start_command(client, message):
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
        # ... (کد دانلود ویدیوهای ترند با استفاده از دکمه‌های کیبورد)
    elif query.data == "download_stories":
        # ... (کد دانلود استوری‌ها با استفاده از دکمه‌های کیبورد)
    elif query.data == "pending_posts":
        # ... (کد نمایش پست‌های pending با استفاده از دکمه‌های کیبورد)
    elif query.data == "scheduled_posts":
        # ... (کد نمایش پست‌های زمان‌بندی شده با استفاده از دکمه‌های کیبورد)
    elif query.data == "set_schedule":
        # ... (کد تنظیم زمان‌بندی با استفاده از دکمه‌های کیبورد)

# ... (بقیه دستورات ربات بدون تغییر)

# --- زمان‌بندی ---

def schedule_posts():
    posts = get_scheduled_posts()
    for post in posts:
        if post[6] <= datetime.now().strftime("%Y-%m-%d %H:%M:%S"): # scheduled time is passed
            if post_to_instagram(post[1], post[2]):
                cursor.execute("DELETE FROM posts WHERE id = ?", (post[0],))
                conn.commit()

schedule.every(10).minutes.do(schedule_posts) # هر 10 دقیقه اجرا شود

while True:
    schedule.run_pending()
    time.sleep(1)

app.run()
