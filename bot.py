import telebot
import sqlite3
import os
import time
import random
import string
from telebot import types

# --- SETTINGS ---
BOT_TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN_HERE'
ADMIN_ID = 'YOUR_TELEGRAM_ID_HERE' 
ADMIN_USERNAME = "@YourUsername" 
MAX_LIMIT = 20 

bot = telebot.TeleBot(BOT_TOKEN)
user_data = {}

# --- DATABASE & FILE LOGIC ---
def init_db():
    conn = sqlite3.connect('generator_logs.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS generated_codes 
                      (id INTEGER PRIMARY KEY, voucher TEXT, pin TEXT, user TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS valid_keys 
                      (key_val TEXT PRIMARY KEY)''')
    conn.commit()
    conn.close()

def check_and_use_key(key):
    conn = sqlite3.connect('generator_logs.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM valid_keys WHERE key_val = ?", (key,))
    exists = cursor.fetchone()
    if exists:
        cursor.execute("DELETE FROM valid_keys WHERE key_val = ?", (key,))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

# --- ADMIN COMMANDS ---
@bot.message_handler(commands=['generate_keys'])
def admin_generate_keys(message):
    if str(message.chat.id) != ADMIN_ID:
        bot.reply_to(message, "❌ आप इसके लिए अधिकृत नहीं हैं!")
        return
    new_keys = [''.join(random.choices(string.ascii_uppercase + string.digits, k=16)) for _ in range(100)]
    conn = sqlite3.connect('generator_logs.db')
    cursor = conn.cursor()
    for key in new_keys:
        cursor.execute("INSERT OR IGNORE INTO valid_keys (key_val) VALUES (?)", (key,))
    conn.commit()
    conn.close()
    bot.reply_to(message, "✅ 100 नई यूनिक कीज़ सफलतापूर्वक जेनरेट हो गई हैं!")

@bot.message_handler(commands=['view_keys'])
def admin_view_keys(message):
    if str(message.chat.id) != ADMIN_ID:
        return
    conn = sqlite3.connect('generator_logs.db')
    cursor = conn.cursor()
    cursor.execute("SELECT key_val FROM valid_keys")
    keys = cursor.fetchall()
    conn.close()
    
    if not keys:
        bot.reply_to(message, "📭 कोई की उपलब्ध नहीं है।")
    else:
        # Sirf pehli 20 dikhayega taki chat spam na ho
        keys_list = "\n".join([k[0] for k in keys[:20]])
        bot.reply_to(message, f"📋 बची हुई कीज़ (कुल {len(keys)}):\n\n{keys_list}\n\n...और भी हैं।")

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
    bot.reply_to(message, "नमस्ते! Domino Generator कंट्रोल पैनल:", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.chat.id
    text = message.text

    if text == "🏠 Main Menu":
        user_data[user_id] = {}
        bot.send_message(user_id, "वापस मेनू में आपका स्वागत है:", reply_markup=get_main_keyboard())
        return

    elif text == "⚡ Generate Codes":
        user_data[user_id] = {'step': 'waiting_count', 'logs': user_data.get(user_id, {}).get('logs', '')}
        bot.send_message(user_id, f"कितने कोड जनरेट करने हैं? (Max {MAX_LIMIT}):", reply_markup=get_back_keyboard())

    elif text == "⚠️ Disclaimer":
        disclaimer_text = (
            "⚠️ **Disclaimer:**\n\n"
            "यदि आप किसी भी तरह की समस्या का सामना कर रहे हैं, "
            "तो '📞 Support' पर क्लिक करके अपनी समस्या बताएं। "
            "हम 24h/48h उपलब्ध हैं।"
        )
        bot.send_message(user_id, disclaimer_text, parse_mode="Markdown")

    elif user_data.get(user_id, {}).get('step') == 'waiting_code':
        if check_and_use_key(text):
            bot.reply_to(message, "✅ Key Valid है! जनरेशन शुरू हो रही है...")
            # ... (yahan baaki code generation ka loop wahi purana wala rahega)
            user_data[user_id]['step'] = 'finished'
        else:
            bot.reply_to(message, "❌ Invalid या Used Key! कृपया सही Key डालें।")

    # ... (baaki logic waisa hi rahega)

bot.polling(none_stop=True)
