import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram.ext import CallbackContext

# تنظیمات اولیه
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# هشتگ و تعداد لایک
hashtag = '#example'
min_likes = 10

# دستورات
async def start(update: Update, context: CallbackContext) -> None:
    user = update.effective_user
    await update.message.reply_text(f'سلام {user.first_name}! برای شروع، یکی از دستورات را انتخاب کنید.',
                                  reply_markup=start_keyboard())

async def set_hashtag(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("لطفاً هشتگ جدید را وارد کنید:")

async def change_hashtag(update: Update, context: CallbackContext) -> None:
    global hashtag
    hashtag = update.message.text
    await update.message.reply_text(f"هشتگ جدید تنظیم شد: {hashtag}")

async def set_likes(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text("لطفاً حداقل تعداد لایک‌ها را وارد کنید:")

async def change_likes(update: Update, context: CallbackContext) -> None:
    global min_likes
    try:
        min_likes = int(update.message.text)
        await update.message.reply_text(f"حداقل تعداد لایک‌ها تنظیم شد: {min_likes}")
    except ValueError:
        await update.message.reply_text("لطفاً یک عدد صحیح وارد کنید.")

async def handle_video(update: Update, context: CallbackContext) -> None:
    video = update.message.video
    if video:
        # بررسی تعداد لایک و هشتگ‌ها (فرضی)
        if min_likes >= 10:  # فقط ویدیوهایی که حداقل 10 لایک دارند
            await update.message.reply_text(f"ویدیو با هشتگ {hashtag} و حداقل {min_likes} لایک تایید شد!")
        else:
            await update.message.reply_text(f"ویدیو تایید نشد. حداقل {min_likes} لایک باید داشته باشد.")
    else:
        await update.message.reply_text("لطفاً یک ویدیو ارسال کنید.")

# تعریف کیبورد اینلاین
def start_keyboard():
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = [
        [InlineKeyboardButton("تغییر هشتگ", callback_data='change_hashtag')],
        [InlineKeyboardButton("تغییر حداقل لایک‌ها", callback_data='change_likes')],
        [InlineKeyboardButton("ارسال ویدیو", callback_data='send_video')],
    ]
    return InlineKeyboardMarkup(keyboard)

async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    if query.data == 'change_hashtag':
        await query.edit_message_text("لطفاً هشتگ جدید را وارد کنید:")
    elif query.data == 'change_likes':
        await query.edit_message_text("لطفاً حداقل تعداد لایک‌ها را وارد کنید:")
    elif query.data == 'send_video':
        await query.edit_message_text("لطفاً یک ویدیو ارسال کنید.")

# اصلی
def main() -> None:
    # توکن ربات
    token = 'YOUR_BOT_API_TOKEN'

    # ایجاد اپلیکیشن و دستورات
    application = Application.builder().token(token).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, change_hashtag))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, change_likes))
    application.add_handler(MessageHandler(filters.VIDEO, handle_video))

    # اجرا
    application.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
