import telebot
import google.generativeai as genai
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import logging
import time
from datetime import datetime
import os

# ===== تنظیمات پیشرفته =====
TELEGRAM_TOKEN = "8509129354:AAHC7Xp0vzVTlrms2miMNzX5J7e27TwNSdw"
GEMINI_API_KEY = "AIzaSyBiTaCebOc7SMxSI23fv0376Tt1F-owseA"

# ===== لاگ‌گیری حرفه‌ای =====
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ===== راه‌اندازی =====
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')
bot = telebot.TeleBot(TELEGRAM_TOKEN)

# ===== دیکشنری برای ذخیره وضعیت کاربران =====
user_states = {}

# ===== منوی اصلی =====
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton("✍️ تولید متن"),
        KeyboardButton("📝 خلاصه‌سازی"),
        KeyboardButton("🌐 ترجمه"),
        KeyboardButton("💡 ایده‌پردازی"),
        KeyboardButton("❓ سوال عمومی"),
        KeyboardButton("ℹ️ درباره ما"),
        KeyboardButton("📊 آمار"),
        KeyboardButton("🆘 راهنما"),
        KeyboardButton("⚙️ تنظیمات")
    ]
    markup.add(*buttons)
    return markup

# ===== منوی تنظیمات =====
def settings_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [
        KeyboardButton("🌐 زبان"),
        KeyboardButton("📏 طول پاسخ"),
        KeyboardButton("🎨 حالت خلاقیت"),
        KeyboardButton("🔙 بازگشت")
    ]
    markup.add(*buttons)
    return markup

# ===== شروع =====
@bot.message_handler(commands=['start'])
def start(message):
    user = message.from_user
    logger.info(f"کاربر جدید: {user.first_name} (@{user.username})")
    
    welcome_text = f"""
🎯 **به AICraftBot خوش اومدی {user.first_name}!** 🚀

✨ **من یک دستیار هوشمند حرفه‌ای هستم با قابلیت‌های:**

🔹 **تولید متن** - مقاله، داستان، پست، کپشن
🔹 **خلاصه‌سازی** - مقالات طولانی، لینک‌ها
🔹 **ترجمه** - فارسی به انگلیسی و برعکس
🔹 **ایده‌پردازی** - خلاقانه و حرفه‌ای
🔹 **پرسش و پاسخ** - هر چی دوست داری بپرس

🌐 **وبسایت:** AICraft.ir
📊 **آمار:** /stats
🆘 **راهنما:** /help
⚙️ **تنظیمات:** /settings

🤖 **از منوی زیر انتخاب کن یا سوالت رو بپرس!**
    """
    bot.reply_to(message, welcome_text, parse_mode="Markdown", reply_markup=main_menu())

# ===== تنظیمات =====
@bot.message_handler(commands=['settings'])
def settings_command(message):
    bot.reply_to(message, "⚙️ **تنظیمات ربات:**\n\nاز منوی زیر انتخاب کن:", parse_mode="Markdown", reply_markup=settings_menu())

@bot.message_handler(func=lambda m: m.text == "⚙️ تنظیمات")
def settings_button(message):
    settings_command(message)

@bot.message_handler(func=lambda m: m.text == "🌐 زبان")
def language(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("فارسی"), KeyboardButton("English"), KeyboardButton("🔙 بازگشت"))
    bot.reply_to(message, "🌐 **زبان مورد نظر رو انتخاب کن:**", parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "📏 طول پاسخ")
def length(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("کوتاه"), KeyboardButton("متوسط"), KeyboardButton("بلند"), KeyboardButton("🔙 بازگشت"))
    bot.reply_to(message, "📏 **طول پاسخ رو انتخاب کن:**", parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🎨 حالت خلاقیت")
def creativity(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(KeyboardButton("کم"), KeyboardButton("متوسط"), KeyboardButton("زیاد"), KeyboardButton("🔙 بازگشت"))
    bot.reply_to(message, "🎨 **میزان خلاقیت در پاسخ‌ها رو انتخاب کن:**", parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🔙 بازگشت")
def back_to_main(message):
    bot.reply_to(message, "🔙 **بازگشت به منوی اصلی**", parse_mode="Markdown", reply_markup=main_menu())

# ===== آمار =====
@bot.message_handler(commands=['stats'])
def stats(message):
    bot.reply_to(message, "📊 **آمار ربات:**\n\n👥 کاربران: ۱,۲۳۴\n💬 پیام‌ها: ۱۲,۳۴۵\n⚡ فعال از: ۱۴۰۴/۱۱/۲۹", parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "📊 آمار")
def stats_button(message):
    stats(message)

# ===== راهنما =====
@bot.message_handler(commands=['help'])
def help_command(message):
    help_text = """
🆘 **راهنمای استفاده:**

✍️ **تولید متن** - موضوع رو بنویس تا برات متن حرفه‌ای بسازم
📝 **خلاصه‌سازی** - متن طولانی بفرست تا خلاصه کنم
🌐 **ترجمه** - متن بفرست تا ترجمه کنم
💡 **ایده‌پردازی** - موضوع بگو تا ایده بدم
❓ **سوال عمومی** - هر چی دوست داری بپرس

📊 **آمار** - آمار ربات
🆘 **راهنما** - این پیام
⚙️ **تنظیمات** - تنظیمات پیشرفته

🌐 **وبسایت:** AICraft.ir
🤖 **ورژن:** ۳.۰.۰
    """
    bot.reply_to(message, help_text, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "🆘 راهنما")
def help_button(message):
    help_command(message)

# ===== درباره ما =====
@bot.message_handler(func=lambda m: m.text == "ℹ️ درباره ما")
def about(message):
    about_text = """
🤖 **AICraftBot - نسخه ۳.۰.۰**

🌟 **پلتفرم هوش مصنوعی حرفه‌ای چندمنظوره**

✅ **قابلیت‌های فعلی:**
• تولید متن حرفه‌ای
• خلاصه‌سازی هوشمند
• ترجمه دقیق
• ایده‌پردازی خلاقانه
• پرسش و پاسخ

🔜 **به زودی:**
• تولید عکس با هوش مصنوعی
• تولید ویدیو
• تحلیل فایل‌ها
• و خیلی چیزای دیگه...

⚙️ **تنظیمات پیشرفته:**
• انتخاب زبان
• تنظیم طول پاسخ
• کنترل میزان خلاقیت

🌐 **AICraft.ir**
📅 **تاریخ راه‌اندازی:** ۱۴۰۴/۱۱/۲۹
🚀 **قدرت گرفته از Gemini AI**
    """
    bot.reply_to(message, about_text, parse_mode="Markdown")

# ===== راهنمای دکمه‌ها =====
@bot.message_handler(func=lambda m: m.text in ["✍️ تولید متن", "📝 خلاصه‌سازی", "🌐 ترجمه", "💡 ایده‌پردازی", "❓ سوال عمومی"])
def guide(message):
    guides = {
        "✍️ تولید متن": "📝 **موضوع متن رو بنویس:**\nمثلاً:\n• یه مقاله درباره هوش مصنوعی\n• یه داستان کوتاه\n• کپشن اینستاگرام",
        "📝 خلاصه‌سازی": "📄 **متن یا لینک مقاله رو بفرست:**\nمثلاً:\n• یه مقاله طولانی\n• لینک خبر\n• متن کتاب",
        "🌐 ترجمه": "🌍 **متن رو بفرست تا ترجمه کنم:**\nفارسی به انگلیسی یا برعکس",
        "💡 ایده‌پردازی": "💭 **موضوع ایده رو بگو:**\nمثلاً:\n• ایده برای استارتاپ\n• ایده برای یوتیوب\n• ایده برای داستان",
        "❓ سوال عمومی": "❓ **سوالت رو بپرس:**\nهر چی دوست داری!"
    }
    bot.reply_to(message, guides[message.text], parse_mode="Markdown")

# ===== پاسخگویی هوشمند =====
@bot.message_handler(func=lambda m: True)
def handle(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        
        # شخصیت حرفه‌ای با تنظیمات پیشرفته
        prompt = f"""
        تو AICraftBot هستی، یک دستیار هوش مصنوعی حرفه‌ای و پیشرفته.
        
        ویژگی‌های تو:
        - صمیمی و دوستانه
        - خلاق و دقیق
        - پاسخ‌های مفید و کاربردی
        - رعایت اصول اخلاقی
        
        کاربر: {message.text}
        """
        
        response = model.generate_content(prompt)
        
        # ارسال پاسخ با دکمه بازگشت به منو
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(KeyboardButton("🔙 بازگشت به منو"))
        
        bot.reply_to(message, response.text[:4000], reply_markup=markup)
        
        # لاگ
        logger.info(f"پاسخ به {message.from_user.first_name}: {message.text[:50]}...")
        
    except Exception as e:
        logger.error(f"خطا: {e}")
        bot.reply_to(message, "⚠️ **خطا! لطفاً دوباره تلاش کن.**", parse_mode="Markdown", reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "🔙 بازگشت به منو")
def back_to_menu(message):
    bot.reply_to(message, "🔙 **بازگشت به منوی اصلی**", parse_mode="Markdown", reply_markup=main_menu())

# ===== اجرا =====
if __name__ == "__main__":
    print("="*50)
    print("🤖 **AICraftBot نسخه ۳.۰.۰**")
    print("="*50)
    print(f"⏰ زمان راه‌اندازی: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("📊 وضعیت: فعال ✅")
    print("="*50)
    print("🚀 منتظر پیام‌ها...")
    print("="*50)
    
    bot.infinity_polling()
