import os
import logging
import requests
from flask import Flask, request
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from dotenv import load_dotenv

# بارگذاری متغیرهای محیطی
load_dotenv()

TOKEN = os.getenv("TOKEN")  # توکن ربات تلگرام
ADMIN_ID = int(os.getenv("ADMIN_ID", "562770229"))  # آیدی ادمین
CHANNEL_ID = os.getenv("CHANNEL_ID")  # مثلا: @yourchannel
CHANNEL_LOCK = os.getenv("CHANNEL_LOCK") == "true"  # آیا قفل کانال فعال است؟

# تنظیمات لاگ
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# توکن ربات و URL API تلگرام
BASE_URL = f"https://api.telegram.org/bot{TOKEN}/"

def send_message(chat_id, text, reply_markup=None):
    """ ارسال پیام به تلگرام """
    url = BASE_URL + "sendMessage"
    params = {"chat_id": chat_id, "text": text, "reply_markup": reply_markup}
    response = requests.post(url, params=params)
    return response

def send_photo(chat_id, photo, caption=None):
    """ ارسال عکس به تلگرام """
    url = BASE_URL + "sendPhoto"
    files = {"photo": photo}
    params = {"chat_id": chat_id, "caption": caption}
    response = requests.post(url, files=files, params=params)
    return response

def check_channel_membership(user_id):
    """ بررسی عضویت کاربر در کانال """
    url = BASE_URL + "getChatMember"
    params = {"chat_id": CHANNEL_ID, "user_id": user_id}
    response = requests.get(url, params=params)
    if response.status_code == 200:
        user_status = response.json()['result']['status']
        return user_status in ["member", "administrator", "creator"]
    return False

@app.route(f'/{TOKEN}', methods=['POST'])
def webhook():
    """ دریافت درخواست از تلگرام به عنوان webhook """
    json_str = request.get_data().decode("UTF-8")
    update = request.json
    message = update.get("message")
    
    if message:
        user_message = message.get("text")
        user_id = message.get("from").get("id")
        user_name = message.get("from").get("username", "کاربر ناشناس")
        
        # بررسی عضویت در کانال
        if CHANNEL_LOCK and not check_channel_membership(user_id):
            send_message(user_id, "برای ارسال پیام ناشناس باید عضو کانال شوید.")
            return "OK", 200

        # ساخت دکمه‌های شیشه‌ای برای ادمین
        keyboard = {
            "inline_keyboard": [
                [{"text": "📢 ارسال به کانال", "callback_data": f"send_to_channel_{user_message}"}],
                [{"text": "🖼️ تبدیل به تصویر", "callback_data": f"create_image_{user_message}"}]
            ]
        }

        # ارسال پیام به ادمین
        send_message(
            ADMIN_ID,
            f"📩 پیام ناشناس دریافت شد:\n\n{user_message}\n\n👤 فرستنده: @{user_name} (ID: {user_id})",
            reply_markup=keyboard
        )
        
        send_message(user_id, "✅ پیام شما ارسال شد!")

    return "OK", 200

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

@app.route("/")
def index():
    return "Bot is running!"

def set_webhook():
    """ تنظیم webhook برای ربات """
    webhook_url = f"https://unknown-bot-3ms9.onrender.com/{TOKEN}"
    url = BASE_URL + "setWebhook"
    params = {"url": webhook_url}
    requests.post(url, params=params)

if __name__ == "__main__":
    # تنظیم webhook
    set_webhook()
    
    # اجرای اپ Flask
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
