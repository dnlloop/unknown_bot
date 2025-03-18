import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, CallbackContext
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from dotenv import load_dotenv
import requests
import threading

# بارگذاری متغیرهای محیطی
load_dotenv()

TOKEN = os.getenv("7715250325:AAGTc78e_IT51cyv-wbaFtDGXQwAd0HlEOI")
ADMIN_ID = int(os.getenv("562770229"))  # آیدی ادمین
CHANNEL_ID = os.getenv("@psychoxz")  # مثلا: @yourchannel
CHANNEL_LOCK = os.getenv("CHANNEL_LOCK") == "true"  # آیا قفل کانال فعال است؟

# تنظیمات لاگ
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

def check_channel_membership(update: Update, context: CallbackContext):
    """ بررسی می‌کنه که کاربر عضو کانال هست یا نه """
    user_id = update.message.from_user.id
    try:
        user_status = context.bot.get_chat_member(CHANNEL_ID, user_id).status
        if user_status not in ["member", "administrator", "creator"]:
            update.message.reply_text("برای ارسال پیام ناشناس باید عضو کانال شوید.")
            return False
    except Exception as e:
        logger.error(f"Error checking channel membership: {e}")
        update.message.reply_text("خطایی رخ داد. لطفاً بعداً امتحان کنید.")
        return False
    return True

def handle_anonymous_message(update: Update, context: CallbackContext):
    """ دریافت پیام ناشناس از کاربران و ارسال به ادمین """
    if CHANNEL_LOCK and not check_channel_membership(update, context):
        return
    
    user_message = update.message.text
    user_id = update.message.from_user.id
    user_name = update.message.from_user.username if update.message.from_user.username else "کاربر ناشناس"

    # ساخت دکمه‌های شیشه‌ای برای ادمین
    keyboard = [
        [InlineKeyboardButton("📢 ارسال به کانال", callback_data=f"send_to_channel_{user_message}")],
        [InlineKeyboardButton("🖼️ تبدیل به تصویر", callback_data=f"create_image_{user_message}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # ارسال پیام به ادمین
    context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📩 پیام ناشناس دریافت شد:\n\n{user_message}\n\n👤 فرستنده: @{user_name} (ID: {user_id})",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

    update.message.reply_text("✅ پیام ناشناس شما ارسال شد!")

def send_to_channel_callback(update: Update, context: CallbackContext):
    """ ارسال پیام ناشناس به کانال توسط ادمین """
    query = update.callback_query
    message_text = query.data.split("_", 1)[1]

    if update.effective_user.id == ADMIN_ID:
        try:
            context.bot.send_message(CHANNEL_ID, f"📩 پیام ناشناس:\n\n{message_text}")
            query.answer("✅ پیام به کانال ارسال شد!")
        except Exception as e:
            logger.error(f"Error sending to channel: {e}")
            query.answer("❌ خطا در ارسال به کانال!")
    else:
        query.answer("❌ شما اجازه این کار را ندارید!")

def create_anonymous_image(message: str):
    """ تبدیل پیام ناشناس به تصویر """
    image = Image.new("RGB", (600, 300), color=(73, 109, 137))
    draw = ImageDraw.Draw(image)
    
    # تنظیم فونت
    font = ImageFont.load_default()

    # رسم متن روی تصویر
    draw.text((50, 120), message, fill=(255, 255, 255), font=font)

    # ذخیره تصویر
    byte_io = BytesIO()
    image.save(byte_io, "PNG")
    byte_io.seek(0)

    return byte_io

def create_image_callback(update: Update, context: CallbackContext):
    """ ادمین با زدن این دکمه، متن ناشناس را به تصویر تبدیل می‌کند """
    query = update.callback_query
    message_text = query.data.split("_", 1)[1]

    if update.effective_user.id == ADMIN_ID:
        image_bytes = create_anonymous_image(message_text)
        query.answer("✅ تصویر ساخته شد!")

        # ارسال تصویر به ادمین
        context.bot.send_photo(ADMIN_ID, photo=image_bytes, caption="🖼️ تصویر ناشناس ساخته شد!")
    else:
        query.answer("❌ شما اجازه این کار را ندارید!")

def start(update: Update, context: CallbackContext):
    update.message.reply_text("👋 سلام! من یک ربات ناشناس هستم. پیام ناشناس خود را ارسال کنید.")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_anonymous_message))
    dp.add_handler(CallbackQueryHandler(send_to_channel_callback, pattern="^send_to_channel_"))
    dp.add_handler(CallbackQueryHandler(create_image_callback, pattern="^create_image_"))

    updater.start_polling()
    updater.idle()

Token="7715250325:AAGTc78e_IT51cyv-wbaFtDGXQwAd0HlEOI"

def keep_alive():
    url = f"https://api.telegram.org/bot{Token}/getMe"
    while True:
        requests.get(url)
        print("Keep Alive Request Sent!")
        threading.Timer(600, keep_alive).start()  # هر 10 دقیقه اجرا میشه

keep_alive()

if __name__ == "__main__":
    main()
