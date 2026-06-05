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
    cursor. Execute('''CREATE TABLE IF NOT EXISTS generated codes 
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

# --- BOT LOGIC ---
def get_main_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Generate Codes", callback_data="gen_menu"),
        types.InlineKeyboardButton("Pay ₹5000 (QR)", callback_data="pay_now"),
        types.InlineKeyboardButton("Stop", callback_data="stop_gen"),
        types.InlineKeyboardButton("Copy Codes", callback_data="copy_all"),
        types.InlineKeyboardButton("Support", url=f"https://t.me/{ADMIN_USERNAME.replace('@','')}")
    )
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "नमस्ते! Domino Generator कंट्रोल पैनल:", reply_markup=get_main_markup())

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.message.chat.id
    if call.data == "gen_menu":
        user_data[user_id] = {'step': 'waiting_count', 'logs': user_data.get(user_id, {}).get('logs', '')}
        bot.send_message(user_id, f"कितने कोड जनरेट करने हैं? (Max {MAX_LIMIT}):")
    
    elif call.data == "pay_now":
        if os.path.exists('qr.png'):
            with open('qr.png', 'rb') as photo:
                bot.send_photo(user_id, photo, caption="₹5000 का भुगतान करें। पेमेंट स्क्रीनशॉट मुझे भेजें, मैं आपको Access Code दूंगा।")
        else:
            bot.send_message(user_id, "QR कोड उपलब्ध नहीं है, एडमिन से संपर्क करें।")
            
    elif call.data == "stop_gen":
        if user_id in user_data: user_data[user_id]['step'] = 'stopped'
        bot.answer_callback_query(call.id, "Generation रोक दी गई है।")
    elif call.data == "copy_all":
        logs = user_data.get(user_id, {}).get('logs', "कोई कोड नहीं है।")
        bot.send_message(user_id, f"कॉपी के लिए सभी कोड्स:\n\n{logs}")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('step') == 'waiting_count')
def get_count(message):
    user_id = message.chat.id
    try:
        count = int(message.text)
        if count > MAX_LIMIT:
            bot.reply_to(message, f"सीमा पार! कृपया {MAX_LIMIT} या उससे कम संख्या डालें।")
            return
        user_data[user_id].update({'count': count, 'step': 'waiting_code'})
        bot.reply_to(message, "20-डिजिट का Access Code दर्ज करें:")
    except ValueError:
        bot.reply_to(message, "कृपया केवल संख्या लिखें।")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get('step') == 'waiting_code')
def verify_code(message):
    user_id = message.chat.id
    if message.text == ACCESS_CODE:
        bot.reply_to(message, "✅ Access Granted! जनरेशन शुरू हो रही है...")
        
        # यहाँ से सुनिश्चित करें कि logs खाली न हो
        if 'logs' not in user_data[user_id]:
            user_data[user_id]['logs'] = ""
            
        count = user_data[user_id].get('count', 0)
        
        for i in range(count):
            # अगर यूजर ने स्टॉप दबाया
            if user_data.get(user_id, {}).get('step') == 'stopped': 
                break
            
            data = get_next_code()
            if not data:
                bot.send_message(user_id, "❌ स्टॉक खत्म हो गया है!")
                break
                
            # कोड भेजना
            result = f"Voucher: {data['code']} | PIN: {data['pin']}"
            user_data[user_id]['logs'] += result + "\n"
            
            bot.send_message(user_id, f"🎟 कोड {i+1}:\n{result}")
            log_to_db(data['code'], data['pin'], message.from_user.username)
            
            time.sleep(1) # यहाँ टाइम कम करें ताकि बॉट रिस्पॉन्सिव रहे
            
        bot.send_message(user_id, "🏁 बैच पूरा हुआ।", reply_markup=get_main_markup())
        user_data[user_id]['step'] = 'finished'
    else:
        bot.reply_to(message, "❌ गलत Access Code!")

while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        time.sleep(5)
