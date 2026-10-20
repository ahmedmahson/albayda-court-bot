import os
import logging

import telebot
from telebot import types
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, '.env'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
)

API_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not API_TOKEN:
    raise RuntimeError(
        'TELEGRAM_BOT_TOKEN is not set. Create a .env file from .env.example and add your bot token.'
    )

bot = telebot.TeleBot(API_TOKEN)

INFO_TEXT = """
⚙️ النظام الإلكتروني المطور للاستعلام القضائي
تقنية معلومات محكمة البيضاء الابتدائية
برمجة وتطوير / احمد حسين محسون
📲 للتواصل والدعم الفني: 771421919
"""


def fetch_case_from_moj(case_num, hijri_year):
    url = "https://judg.moj.gov.ye/JUDDATALIST/CustomRetCaseMaster"
    payload = {
        'CaseNo': case_num,
        'HijriYear': hijri_year
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.post(url, data=payload, headers=headers, timeout=15)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            result_block = soup.find('div', {'id': 'resultContainer'}) or soup.find('table', {'class': 'table'})
            if result_block:
                return result_block.get_text(strip=True)
            if "لا توجد نتائج" in response.text or "عفواً" in response.text:
                return None
            return "تم الاتصال بالموقع بنجاح، يرجى التحقق من تفاصيل النتائج."
        return None
    except Exception as exc:
        logging.exception("Error while connecting to the Ministry site")
        return None


@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn_search = types.KeyboardButton('🔍 الاستعلام المباشر عن قضية')
    btn_info = types.KeyboardButton('ℹ️ معلومات النظام والملكية')
    markup.add(btn_search, btn_info)

    welcome_msg = (
        "مرحباً بك في نظام الاستعلام القضائي الإلكتروني المطور لـ محكمة البيضاء الابتدائية.\n\n"
        "البوت مرتبط مباشرة ببوابة وزارة العدل اليمنية للاستعلام الفوري.\n"
        "الرجاء اختيار الخدمة المطلوبة:"
    )
    bot.reply_to(message, welcome_msg, reply_markup=markup, parse_mode='Markdown')


@bot.message_handler(func=lambda message: True)
def handle_menu(message):
    if message.text == 'ℹ️ معلومات النظام والملكية':
        bot.reply_to(message, INFO_TEXT, parse_mode='Markdown')
    elif message.text == '🔍 الاستعلام المباشر عن قضية':
        msg = bot.send_message(
            message.chat.id,
            "📌 **الرجاء إدخال رقم القضية والسنة الهجرية بالصيغة المعتمدة:**\n\n"
            "`الرقم / السنة` (مثال: `101/1446` أو `150 / 1445`)",
            reply_markup=types.ForceReply(selective=True),
            parse_mode='Markdown'
        )
        bot.register_next_step_handler(msg, process_search)
    else:
        bot.reply_to(message, "الرجاء استخدام الأزرار المتاحة في القائمة أسفل الشاشة.")


def process_search(message):
    input_text = message.text.strip()
    bot.send_chat_action(message.chat.id, 'typing')

    if '/' in input_text:
        parts = input_text.split('/')
        case_num = parts[0].strip()
        hijri_year = parts[1].strip()
    else:
        bot.reply_to(
            message,
            "⚠️ صيغة المدخلات غير صحيحة.\nيرجى كتابة رقم القضية متبوعاً بشرطة و السنة الهجرية مثل: `101/1446`",
            parse_mode='Markdown'
        )
        return

    wait_msg = bot.reply_to(message, "⏳ جاري الاتصال بموقع وزارة العدل وجلب تفاصيل القضية...", parse_mode='Markdown')
    case_data = fetch_case_from_moj(case_num, hijri_year)

    if case_data:
        response = (
            f"⚖️ **نتيجة الاستعلام للقضية رقم ({case_num} / {hijri_year} هـ):**\n\n"
            f"{case_data}\n\n"
            f"----------------------------------\n"
            f"{INFO_TEXT}"
        )
    else:
        response = (
            f"❌ لم يتم العثور على بيانات للقضية رقم ({case_num} / {hijri_year} هـ) أو أن الخدمة غير متاحة مؤقتاً في موقع الوزارة.\n"
            f"يرجى التأكد من صحة الأرقام أو مراجعة المحكمة مباشرة.\n\n"
            f"----------------------------------\n"
            f"{INFO_TEXT}"
        )

    bot.edit_message_text(response, chat_id=message.chat.id, message_id=wait_msg.message_id, parse_mode='Markdown')


if __name__ == '__main__':
    logging.info('🚀 البوت المرتبط مباشرة بموقع وزارة العدل يعمل الآن...')
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
