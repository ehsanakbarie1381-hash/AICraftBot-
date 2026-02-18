import telebot
from google import genai
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from collections import defaultdict
import logging
import time
from datetime import datetime
import os
import threading
import http.server
import socketserver

# ===== تنظیمات اصلی =====
TELEGRAM_TOKEN = "8509129354:AAEzG_0bvTQnZ4S3w3LPZ4DIfAiQDVjp5MU"
GEMINI_API_KEY = "AIzaSyBiTaCebOc7SMxSI23fv0376Tt1F-owseA"

# ===== تنظیمات کانال =====
CHANNEL_USERNAME = "@AICraft_ir"
CHANNEL_LINK = "https://t.me/AICraft_ir"
FREE_QUESTIONS = 10
CHECK_PERIOD = 24 * 3600

# ===== لاگ‌گیری =====
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== راه‌اندازی هوش مصنوعی =====
client = genai.Client(api_key=GEMINI_API_KEY)
model = 'gemini-pro'
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ===== ذخیره سوالات کاربران =====
user_questions = defaultdict(list)

# ===== توابع کمکی =====
def is_member(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except Exception as e:
        logger.error(f"خطا در بررسی عضویت: {e}")
        return False

def check_question_limit(user_id):
    now = time.time()
    user_questions[user_id] = [t for t in user_questions[user_id] if now - t < CHECK_PERIOD]
    asked = len(user_questions[user_id])
    
    if is_member(user_id):
        return True, 0, asked
    
    if asked >= FREE_QUESTIONS:
        return False, FREE_QUESTIONS - asked, asked
    
    return True, FREE_QUESTIONS - asked, asked

def record_question(user_id):
    user_questions[user_id].append(time.time())

# ===== منوی اصلی =====
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton("✍️ تولید متن"),
        KeyboardButton("📄 خلاصه‌سازی"),
        KeyboardButton("🌐 ترجمه"),
        KeyboardButton("💡 ایده‌پردازی"),
        KeyboardButton("❓ پرسش"),
        KeyboardButton("📊 آمار من"),
        KeyboardButton("💎 درباره ما"),
        KeyboardButton("⚙️ تنظیمات")
    ]
    markup.add(*buttons)
    return markup

# ===== شروع =====
@bot.message_handler(commands=['start'])
def start(message):
    user = message.from_user
    logger.info(f"کاربر جدید: {user.first_name} (@{user.username})")
    
    welcome_text = f"""
💎 **به AICraft خوش اومدی {user.first_name}!** 💎

🧊 جایی که هوش مصنوعی با هنر **صنعت‌گری** می‌کنه

✨ **خدمات ما:**
🔮 **تولید متن** حرفه‌ای
🪞 **خلاصه‌سازی** هوشمند
💫 **ترجمه** دقیق
🌟 **ایده‌پردازی** خلاقانه

🎁 **سوالات رایگان:** {FREE_QUESTIONS} تا در روز
🔔 بعد از اون، عضو کانال شو: {CHANNEL_LINK}

🌐 **AICraft.ir**
    """
    bot.reply_to(message, welcome_text, parse_mode="Markdown", reply_markup=main_menu())

# ===== درباره ما =====
@bot.message_handler(func=lambda m: m.text == "💎 درباره ما")
def about(message):
    text = """
🤖 **AICraft**

🌟 **AI-Powered Content Creation Platform**

✅ **Features:**
• ✍️ Text generation
• 📝 Summarization
• 🌐 Translation
• 💡 Idea generation
• ❓ Q&A

🎁 **Free questions:** 10/day
🔔 After that, join: @AICraft_ir

🌐 **AICraft.ir**
🤖 **Version 3.0.0**
    """
    bot.reply_to(message, text, parse_mode="Markdown", reply_markup=main_menu())

# ===== آمار کاربر =====
@bot.message_handler(func=lambda m: m.text == "📊 آمار من")
def my_stats(message):
    user_id = message.from_user.id
    asked = len([t for t in user_questions[user_id] if time.time() - t < CHECK_PERIOD])
    
    if is_member(user_id):
        status = "🌟 عضو کانال (نامحدود)"
        remaining = "∞"
    else:
        status = "🔔 عضو نیستی"
        remaining = FREE_QUESTIONS - asked
    
    text = f"""
📊 **آمار سوالات شما**

✅ پرسیده شده: {asked}
⏳ باقی‌مانده: {remaining}
📌 وضعیت: {status}

🔗 {CHANNEL_LINK}
    """
    bot.reply_to(message, text, parse_mode="Markdown", reply_markup=main_menu())

# ===== تنظیمات =====
@bot.message_handler(func=lambda m: m.text == "⚙️ تنظیمات")
def settings(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("🌐 زبان پاسخ"),
        KeyboardButton("📏 طول متن"),
        KeyboardButton("🎨 خلاقیت"),
        KeyboardButton("🔙 بازگشت")
    )
    bot.reply_to(message, "⚙️ **تنظیمات:**", parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🔙 بازگشت")
def back_to_main(message):
    bot.reply_to(message, "🔙 بازگشت به منوی اصلی", reply_markup=main_menu())

# ===== راهنمای دکمه‌ها =====
@bot.message_handler(func=lambda m: m.text in ["✍️ تولید متن", "📄 خلاصه‌سازی", "🌐 ترجمه", "💡 ایده‌پردازی", "❓ پرسش"])
def guide(message):
    guides = {
        "✍️ تولید متن": "📝 **موضوع متن رو بنویس:**",
        "📄 خلاصه‌سازی": "📄 **متن یا لینک رو بفرست:**",
        "🌐 ترجمه": "🌍 **متن رو بفرست:**",
        "💡 ایده‌پردازی": "💭 **موضوع ایده رو بگو:**",
        "❓ پرسش": "❓ **سوالت رو بپرس:**"
    }
    bot.reply_to(message, guides[message.text], parse_mode="Markdown")

# ===== پاسخگویی هوشمند با محدودیت =====
@bot.message_handler(func=lambda m: True)
def handle(message):
    user_id = message.from_user.id
    
    can_ask, remaining, asked = check_question_limit(user_id)
    
    if not can_ask:
        keyboard = InlineKeyboardMarkup()
        keyboard.add(InlineKeyboardButton("🔔 عضو کانال شو", url=CHANNEL_LINK))
        keyboard.add(InlineKeyboardButton("✅ عضو شدم", callback_data="check_membership"))
        
        bot.reply_to(
            message,
            f"⛔ **محدودیت سوال**\n\n"
            f"شما {FREE_QUESTIONS} سوال رایگان داشتی.\n"
            f"همه رو پرسیدی! 🙃\n\n"
            f"🔔 برای سوال نامحدود، عضو کانال ما شو:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        return
    
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        record_question(user_id)
        
        prompt = f"تو دستیار AICraft هستی. صمیمی و خلاقانه به فارسی پاسخ بده. کاربر: {message.text}"
        
        response = client.models.generate_content(
            model='gemini-pro',
            contents=prompt
        )
        
        if not is_member(user_id):
            remaining_msg = f"\n\n⏳ {remaining} سوال رایگان باقی مونده.\n🔔 {CHANNEL_LINK}"
        else:
            remaining_msg = "\n\n🌟 عضو کانال هستی، سوالات نامحدود!"
        
        bot.reply_to(message, response.text[:4000] + remaining_msg, reply_markup=main_menu())
        
    except Exception as e:
        logger.error(f"خطا: {e}")
        bot.reply_to(message, "⚠️ **خطا! دوباره تلاش کن.**", parse_mode="Markdown", reply_markup=main_menu())

# ===== بررسی عضویت =====
@bot.callback_query_handler(func=lambda call: call.data == "check_membership")
def check_membership(call):
    user_id = call.from_user.id
    
    if is_member(user_id):
        bot.edit_message_text(
            "✅ **عضویت تأیید شد!**\n\nاکنون می‌تونی سوالات نامحدود بپرسی.",
            call.message.chat.id,
            call.message.message_id,
            parse_mode="Markdown"
        )
    else:
        bot.answer_callback_query(
            call.id,
            "❌ هنوز عضو نشدی! اول عضو شو.",
            show_alert=True
        )

# ===== توابع اجرایی برای Render =====
def run_bot():
    """اجرای اصلی ربات"""
    bot.infinity_polling()

def run_dummy_server():
    """سرور فیک برای راضی کردن Render"""
    PORT = int(os.environ.get("PORT", 8080))
    handler = http.server.SimpleHTTPRequestHandler
    
    class SilentHandler(handler):
        def log_message(self, format, *args):
            pass  # خاموش کردن لاگ‌های اضافی
    
    try:
        with socketserver.TCPServer(("", PORT), SilentHandler) as httpd:
            print(f"✅ Dummy server running on port {PORT} (for Render)")
            httpd.serve_forever()
    except Exception as e:
        print(f"⚠️ Dummy server error: {e}")

# ===== اجرای اصلی =====
if __name__ == "__main__":
    print("="*50)
    print("🤖 **AICraft Bot - نسخه نهایی ۳.۰**")
    print("="*50)
    print(f"⏰ زمان راه‌اندازی: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📊 وضعیت: فعال ✅")
    print(f"🎁 سوالات رایگان: {FREE_QUESTIONS} تا")
    print(f"🔗 کانال: {CHANNEL_LINK}")
    print("="*50)
    print("🚀 منتظر پیام‌ها...")
    print("="*50)
    
    # اجرای همزمان ربات و سرور فیک
    bot_thread = threading.Thread(target=run_bot)
    server_thread = threading.Thread(target=run_dummy_server)
    
    bot_thread.start()
    server_thread.start()
    
    bot_thread.join()
    server_thread.join()
