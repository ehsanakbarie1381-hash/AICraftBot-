import os
import logging
from collections import defaultdict

from flask import Flask, request
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import google.generativeai as genai

logging.basicConfig(level=logging.INFO)

TELEGRAM_BOT_TOKEN = os.getenv("8509129354:AAEGYDdGAbO0IypinF8wW5YtWZWl4OXaWIM")
GEMINI_API_KEY = os.getenv("AIzaSyBiTaCebOc7SMxSI23fv0376Tt1F-owseA")
CHANNEL_USERNAME = os.getenv("@AICraft-ir")  
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

WELCOME_STICKER_ID = os.getenv("WELCOME_STICKER_ID", "")
ERROR_STICKER_ID = os.getenv("ERROR_STICKER_ID", "")
JOIN_STICKER_ID = os.getenv("JOIN_STICKER_ID", "")
PROCESSING_STICKER_ID = os.getenv("PROCESSING_STICKER_ID", "")

bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

app = Flask(__name__)

# در عمل بهتره DB باشه؛ فعلاً در حافظه:
user_limits = defaultdict(lambda: {"q": 0, "sum": 0})


def is_member(user_id: int) -> bool:
    if not CHANNEL_USERNAME:
        return True
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception as e:
        logging.warning(f"check member error: {e}")
        return False


def over_limit(user_id: int, kind: str) -> bool:
    limits = {"q": 10, "sum": 3}
    return user_limits[user_id][kind] >= limits[kind]


def require_channel(user_id: int):
    if JOIN_STICKER_ID:
        try:
            bot.send_sticker(chat_id=user_id, sticker=JOIN_STICKER_ID)
        except Exception:
            pass
    text = (
        "برای ادامه استفاده از ربات، باید عضو کانال ما باشی 🌟\n"
        f"{CHANNEL_USERNAME}\n"
        "بعد از عضویت، دوباره پیام بده تا ادامه بدیم."
    )
    bot.send_message(chat_id=user_id, text=text)


def send_error(user_id: int, err: Exception, context_text: str = ""):
    # پیام برای کاربر
    if ERROR_STICKER_ID:
        try:
            bot.send_sticker(chat_id=user_id, sticker=ERROR_STICKER_ID)
        except Exception:
            pass
    bot.send_message(
        chat_id=user_id,
        text="مشکلی در پردازش درخواست پیش اومد. لطفاً کمی بعد دوباره امتحان کن.",
    )

    # گزارش برای ادمین
    if ADMIN_ID:
        try:
            bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    "⚠️ خطای جدید در ربات ثبت شد\n"
                    f"کاربر: {user_id}\n"
                    f"متن: {context_text[:200]}\n"
                    f"نوع خطا: {type(err).__name__}\n"
                    f"جزئیات: {err}"
                ),
            )
        except Exception:
            pass


def main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("🧠 چت هوشمند", callback_data="menu_chat"),
            InlineKeyboardButton("📄 خلاصه مقاله", callback_data="menu_summary"),
        ],
        [
            InlineKeyboardButton("🎙️ پیام صوتی", callback_data="menu_voice"),
            InlineKeyboardButton("📊 وضعیت حساب", callback_data="menu_status"),
        ],
        [
            InlineKeyboardButton("🔗 عضویت کانال", url=f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def handle_chat(user_id: int, chat_id: int, text: str):
    if over_limit(user_id, "q") and not is_member(user_id):
        require_channel(user_id)
        return

    prompt = text.strip() or "سلام"
    if PROCESSING_STICKER_ID:
        try:
            bot.send_sticker(chat_id=chat_id, sticker=PROCESSING_STICKER_ID)
        except Exception:
            pass

    try:
        resp = model.generate_content(prompt)
        reply = resp.text or "نتونستم جواب مناسبی بسازم."
        user_limits[user_id]["q"] += 1
        bot.send_message(chat_id=chat_id, text=reply)
    except Exception as e:
        logging.exception("chat error")
        send_error(user_id, e, context_text=prompt)


def handle_summary(user_id: int, chat_id: int, text: str):
    if over_limit(user_id, "sum") and not is_member(user_id):
        require_channel(user_id)
        return

    content = text.strip()
    if not content:
        bot.send_message(chat_id=chat_id, text="لطفاً متن یا مقاله‌ای برای خلاصه‌سازی ارسال کن.")
        return

    prompt = f"این متن را به صورت خلاصه و منظم به فارسی خلاصه کن:\n\n{content}"

    if PROCESSING_STICKER_ID:
        try:
            bot.send_sticker(chat_id=chat_id, sticker=PROCESSING_STICKER_ID)
        except Exception:
            pass

    try:
        resp = model.generate_content(prompt)
        reply = resp.text or "نتونستم خلاصه مناسبی بسازم."
        user_limits[user_id]["sum"] += 1
        bot.send_message(chat_id=chat_id, text=reply)
    except Exception as e:
        logging.exception("summary error")
        send_error(user_id, e, context_text=content)


def handle_voice(user_id: int, chat_id: int, voice: telegram.Voice):
    # اینجا باید API تبدیل صوت به متن وصل شود
    # فعلاً فقط پیام راهنما می‌فرستیم
    bot.send_message(
        chat_id=chat_id,
        text="🎙️ پشتیبانی از تبدیل صوت به متن در نسخه بعدی فعال می‌شود.",
    )


@app.route("/", methods=["GET"])
def index():
    return "AICraftBot is running", 200


@app.route("/webhook", methods=["POST"])
def webhook():
    update = telegram.Update.de_json(request.get_json(force=True), bot)

    # CallbackQuery (منوی شیشه‌ای)
    if update.callback_query:
        cq = update.callback_query
        data = cq.data
        user_id = cq.from_user.id
        chat_id = cq.message.chat.id

        if data == "menu_chat":
            bot.answer_callback_query(cq.id)
            bot.send_message(
                chat_id=chat_id,
                text="متن خودت رو برای چت هوشمند بفرست یا از دستور /chat استفاده کن.",
            )
        elif data == "menu_summary":
            bot.answer_callback_query(cq.id)
            bot.send_message(
                chat_id=chat_id,
                text="متن یا مقاله‌ات رو بفرست و از /summary هم می‌تونی استفاده کنی.",
            )
        elif data == "menu_voice":
            bot.answer_callback_query(cq.id)
            bot.send_message(
                chat_id=chat_id,
                text="یک پیام صوتی بفرست تا روی آن کار کنیم (در نسخه بعدی).",
            )
        elif data == "menu_status":
            bot.answer_callback_query(cq.id)
            stats = user_limits.get(user_id, {"q": 0, "sum": 0})
            bot.send_message(
                chat_id=chat_id,
                text=(
                    "📊 وضعیت حساب:\n"
                    f"سؤالات متنی استفاده‌شده: {stats['q']} / 10\n"
                    f"خلاصه‌ها استفاده‌شده: {stats['sum']} / 3"
                ),
            )
        return "ok", 200

    if not update.message:
        return "ok", 200

    msg = update.message
    chat_id = msg.chat.id
    user_id = msg.from_user.id
    text = msg.text or ""

    # پنل ادمین ساده
    if user_id == ADMIN_ID and text.startswith("/admin"):
        stats = user_limits.get(user_id, {"q": 0, "sum": 0})
        bot.send_message(
            chat_id=chat_id,
            text=(
                "پنل ادمین ✅\n"
                f"سؤالات شما: {stats['q']}\n"
                f"خلاصه‌های شما: {stats['sum']}"
            ),
        )
        return "ok", 200

    # /start
    if text.startswith("/start"):
        if WELCOME_STICKER_ID:
            try:
                bot.send_sticker(chat_id=chat_id, sticker=WELCOME_STICKER_ID)
            except Exception:
                pass
        bot.send_message(
            chat_id=chat_id,
            text=(
                "سلام 👋 من ربات AICraft هستم.\n"
                "می‌تونی با من چت کنی، مقاله بفرستی تا خلاصه کنم، و از منوی زیر استفاده کنی.\n"
            ),
            reply_markup=main_menu_keyboard(),
        )
        return "ok", 200

    # دستورات متنی
    if text.startswith("/chat"):
        prompt = text.replace("/chat", "", 1)
        handle_chat(user_id, chat_id, prompt)
        return "ok", 200

    if text.startswith("/summary"):
        content = text.replace("/summary", "", 1)
        handle_summary(user_id, chat_id, content)
        return "ok", 200

    # پیام صوتی
    if msg.voice:
        handle_voice(user_id, chat_id, msg.voice)
        return "ok", 200

    # پیش‌فرض: چت آزاد
    handle_chat(user_id, chat_id, text)
    return "ok", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
