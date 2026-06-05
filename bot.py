import telebot
import sqlite3
import os
import time
from telebot import types

# --- SETTINGS ---
BOT_TOKEN = '8522964450:AAFPAOqiv6cpt2lF8JhRT6_UGw_1LjQwE7U'
ADMIN_ID = '1102140969' 
ADMIN_USERNAME = "@CuteGirl21459" 
ACCESS_CODE = "IR83JLLPcbf4Ur4axS0m"
MAX_LIMIT = 20 

bot = telebot.TeleBot(BOT_TOKEN)
user_data = {}

# --- DATABASE & FILE LOGIC ---
def init_db():
    conn = sqlite3.connect('generator_logs.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS generated_codes 
                      (id INTEGER PRIMARY KEY, voucher TEXT, pin TEXT, user TEXT)''')
    conn.commit()
    conn.close()

def log_to_db(voucher, pin, user):
    conn = sqlite3.connect('generator_logs.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO generated_codes (voucher, pin, user) VALUES (?, ?, ?)", (voucher, pin, user))
    conn.commit()
    conn.close()

def get_next_code():
    if not os.path.exists('codes.txt'): return None
    with open('codes.txt', 'r') as f:
        lines = f.readlines()
    if not lines: return None
    line = lines[0].strip()
    if ':' not in line: return None
    code, pin = line.split(':')
    with open('codes.txt', 'w') as f:
        f.writelines(lines[1:])
    return {"code": code, "pin": pin}

init_db()

# --- KEYBOARDS ---
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton("⚡ Generate Codes"),
        types.KeyboardButton("💰 Payment"),
        types.KeyboardButton("🛑 Stop"),
        types.KeyboardButton("📋 Copy Codes"),
        types.KeyboardButton("📞 Support"),
        types.KeyboardButton("⚠️ Disclaimer")
    )
    return markup

def get_back_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("🏠 Main Menu"))
    return markup

# --- BOT LOGIC ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_data[message.chat.id] = {}
    bot.reply_to(message, "नमस्ते! Domino Generator कंट्रोल पैनल में आपका स्वागत है:", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.chat.id
    text = message.text

    # 1. Main Menu Logic
    if text == "🏠 Main Menu":
        user_data[user_id] = {}
        bot.send_message(user_id, "वापस मेनू में आपका स्वागत है:", reply_markup=get_main_keyboard())
        return

    # 2. Main Button Actions
    elif text == "⚡ Generate Codes":
        user_data[user_id] = {'step': 'waiting_count', 'logs': user_data.get(user_id, {}).get('logs', '')}
        bot.send_message(user_id, f"कितने कोड जनरेट करने हैं? (Max {MAX_LIMIT}):", reply_markup=get_back_keyboard())

    elif text == "💰 Payment":
        if os.path.exists('qr.png'):
            with open('qr.png', 'rb') as photo:
                bot.send_photo(user_id, photo, caption="₹5000 का भुगतान करें।")
        else:
            bot.send_message(user_id, "QR कोड उपलब्ध नहीं है।")

    elif text == "🛑 Stop":
        if user_id in user_data: user_data[user_id]['step'] = 'stopped'
        bot.send_message(user_id, "Generation रोक दी गई है।")

    elif text == "📋 Copy Codes":
        logs = user_data.get(user_id, {}).get('logs', "कोई कोड नहीं है।")
        bot.send_message(user_id, f"कॉपी के लिए सभी कोड्स:\n\n{logs}")

    elif text == "📞 Support":
        support_url = f"https://t.me/{ADMIN_USERNAME.replace('@','')}"
        bot.send_message(user_id, f"किसी भी समस्या के लिए यहाँ संपर्क करें:\n{support_url}")

    elif text == "⚠️ Disclaimer":
        disclaimer_text = (
            "⚠️ **Disclaimer & Support:**\n\n"
            "बॉट से जनरेट किए हुए सारे कोड वैलिड नहीं होंगे "
            "आपको खुद चेक करना होगा कोड वैलिड है या नहीं \n\n"
            "आपको डोमिनोज के kart वैल्यू पर जाना है वाउचर , "
            "कोड अप्लाई करके देखना है जितने कोड आपको वैलिड दिखाई दे "
            "उनको सेव करलेना हम जल्दी ही वोट में अपडेट करेंगे चेकर लगाने की "
        )
        bot.send_message(user_id, disclaimer_text, parse_mode="Markdown")

    # 3. Steps Processing
    elif user_data.get(user_id, {}).get('step') == 'waiting_count':
        try:
            count = int(text)
            if count > MAX_LIMIT:
                bot.reply_to(message, f"अधिकतम {MAX_LIMIT} तक ही चुन सकते हैं।")
                return
            user_data[user_id].update({'count': count, 'step': 'waiting_code'})
            bot.reply_to(message, "20-डिजिट का Access Code दर्ज करें:")
        except ValueError:
            bot.reply_to(message, "कृपया केवल संख्या लिखें।")

    elif user_data.get(user_id, {}).get('step') == 'waiting_code':
        if text == ACCESS_CODE:
            bot.reply_to(message, "✅ जनरेशन शुरू हो रही है...")
            count = user_data[user_id].get('count', 0)
            for i in range(count):
                if user_data.get(user_id, {}).get('step') == 'stopped': break
                data = get_next_code()
                if not data:
                    bot.send_message(user_id, "❌ स्टॉक खत्म हो गया है!")
                    break
                result = f"Voucher: {data['code']} | PIN: {data['pin']}"
                user_data[user_id]['logs'] += result + "\n"
                bot.send_message(user_id, f"🍕 कोड {i+1}:\n{result}")
                log_to_db(data['code'], data['pin'], message.from_user.username)
                time.sleep(1)
            bot.send_message(user_id, "🍕 Genrate successfully", reply_markup=get_main_keyboard())
            user_data[user_id]['step'] = 'finished'
        else:
            bot.reply_to(message, "❌ गलत Access Code!")

bot.polling(none_stop=True)
