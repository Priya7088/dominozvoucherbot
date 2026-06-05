import telebot
import gspread
import random
import string
import time
from oauth2client.service_account import ServiceAccountCredentials
from telebot import types

# --- SETTINGS ---
BOT_TOKEN = '8522964450:AAFPAOqiv6cpt2lF8JhRT6_UGw_1LjQwE7U'  # Apna Telegram Bot Token yahan dalein
ADMIN_USERNAME = "@CuteGirl21459"            # Apna Telegram Username dalein
MAX_LIMIT = 20 

# --- GOOGLE SHEETS CONFIG ---
JSON_FILE = 'ivory-setup-498503-g0-2b244256e56a'          # Apni downloaded JSON file ka sahi naam yahan likhein
SHEET_NAME = 'Domino_Bot_Db'               # Apni Google Sheet ka exact naam yahan likhein

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(Domino_Bot_Db, scope)
client = gspread.authorize(creds)
spreadsheet = client.open('Domino\_Bot\_Db')

# Alag-alag tabs ko connect karna
sheet_stock = spreadsheet.worksheet("Stock")
sheet_keys = spreadsheet.worksheet("Access_Keys")
sheet_logs = spreadsheet.worksheet("Logs")

bot = telebot.TeleBot(BOT_TOKEN)
user_data = {}

# --- BOT LOGIC & DATABASE SYSTEMS VIA GOOGLE SHEETS ---

def init_sheets():
    """Agar sheet khali hai to apne aap 50 unique codes generate karke save karega"""
    records = sheet_keys.get_all_records()
    if len(records) == 0:
        print("Google Sheet me koi keys nahi mili. 50 new keys generate ho rahi hain...")
        bulk_data = []
        for _ in range(50):
            # 20-digit unique access key banana
            key = ''.join(random.choices(string.ascii_letters + string.digits, k=20))
            bulk_data.append([key, "Unused", ""])
        sheet_keys.append_rows(bulk_data)
        print("✅ 50 unique keys Google Sheet ke 'Access_Keys' tab me save ho gayi hain!")

def is_user_authorized(user_id):
    """Check karna ki kya user ki Telegram ID pehle se registered hai"""
    records = sheet_keys.get_all_records()
    for row in records:
        if str(row.get('Telegram_ID')) == str(user_id):
            return True
    return False

def activate_user_code(user_id, input_key):
    """User ke access code ko verify karna, use 'Used' mark karna aur ID lock karna"""
    records = sheet_keys.get_all_records()
    # row index sheet me 2 se start hota hai kyunki row 1 header hai
    for i, row in enumerate(records, start=2):
        if row.get('Key') == input_key and row.get('Status') == "Unused":
            sheet_keys.update_cell(i, 2, "Used")
            sheet_keys.update_cell(i, 3, str(user_id))
            return True
    return False

def get_next_code_from_sheet():
    """Stock tab se sabse upar wala ek code nikalna aur use sheet se delete karna"""
    row_data = sheet_stock.row_values(2)  # Row 2 (Pehla real data)
    if not row_data or len(row_data) < 2:
        return None
    voucher = row_data[0]
    pin = row_data[1]
    sheet_stock.delete_rows(2)  # Is code ko stock se delete kar dena taaki repeat na ho
    return {"code": voucher, "pin": pin}

def log_to_sheet(voucher, pin, user):
    """Generated codes ka record Logs tab me dalna"""
    current_time = time.strftime("%Y-%m-%d %H:%M:%S")
    sheet_logs.append_row([voucher, pin, user, current_time])

# Sheets check karein
init_sheets()

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

# --- BOT HANDLERS ---
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_data[message.chat.id] = {}
    bot.reply_to(message, "Namaste! Domino Generator Control Panel me aapka swagat hai:", reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = message.chat.id
    text = message.text

    if text == "🏠 Main Menu":
        user_data[user_id] = {}
        bot.send_message(user_id, "Wapas menu me aapka swagat hai:", reply_markup=get_main_keyboard())
        return

    elif text == "⚡ Generate Codes":
        if is_user_authorized(user_id):
            user_data[user_id] = {'step': 'waiting_count', 'logs': ''}
            bot.send_message(user_id, f"✅ Aapka account verified hai!\nKitne code generate karne hain? (Max {MAX_LIMIT}):", reply_markup=get_back_keyboard())
        else:
            user_data[user_id] = {'step': 'waiting_access_code'}
            bot.send_message(user_id, "🔒 Aap verified nahi hain!\nKripya apna 20-digit ka One-Time Access Code darj karein:", reply_markup=get_back_keyboard())

    elif text == "💰 Payment":
        bot.send_message(user_id, "₹5000 ka bhugtan karein aur admin ko screenshot bhejein.")

    elif text == "🛑 Stop":
        if user_id in user_data: user_data[user_id]['step'] = 'stopped'
        bot.send_message(user_id, "Generation rok di gayi hai.")

    elif text == "📋 Copy Codes":
        logs = user_data.get(user_id, {}).get('logs', "Koi code nahi hai.")
        bot.send_message(user_id, f"Copy ke liye sabhi codes:\n\n{logs}")

    elif text == "📞 Support":
        support_url = f"https://t.me/{ADMIN_USERNAME.replace('@','')}"
        bot.send_message(user_id, f"Kisi bhi samasya ke liye yahan sampark karein:\n{support_url}")

    elif text == "⚠️ Disclaimer":
        disclaimer_text = "⚠️ **Disclaimer:**\n\nYeh bot keval educational purposes ke liye hai."
        bot.send_message(user_id, disclaimer_text, parse_mode="Markdown")

    # Access Code Verification Logic
    elif user_data.get(user_id, {}).get('step') == 'waiting_access_code':
        if activate_user_code(user_id, text):
            bot.reply_to(message, "🎉 Badhai ho! Access Code verify ho gaya hai aur aapki Telegram ID bot se jud gayi hai.")
            user_data[user_id] = {'step': 'waiting_count', 'logs': ''}
            bot.send_message(user_id, f"Ab batayein, aapko kitne code chahiye? (Max {MAX_LIMIT}):")
        else:
            bot.reply_to(message, "❌ Galat ya pehle se istemal kiya hua Access Code!")

    # Domino Code Generation Logic
    elif user_data.get(user_id, {}).get('step') == 'waiting_count':
        try:
            count = int(text)
            if count > MAX_LIMIT:
                bot.reply_to(message, f"Adhiktam {MAX_LIMIT} tak hi chun sakte hain.")
                return
                
            bot.reply_to(message, "✅ Generation shuru ho rahi hai...")
            for i in range(count):
                if user_data.get(user_id, {}).get('step') == 'stopped': break
                
                data = get_next_code_from_sheet()
                if not data:
                    bot.send_message(user_id, "❌ Stock khatam ho gaya hai! Google Sheet check karein.")
                    break
                    
                result = f"Voucher: {data['code']} | PIN: {data['pin']}"
                if 'logs' not in user_data[user_id]:
                    user_data[user_id]['logs'] = ""
                user_data[user_id]['logs'] += result + "\n"
                
                bot.send_message(user_id, f"🍕 Code {i+1}:\n{result}")
                log_to_sheet(data['code'], data['pin'], message.from_user.username or "Unknown")
                time.sleep(1)
                
            bot.send_message(user_id, "Code successfully Generated.", reply_markup=get_main_keyboard())
            user_data[user_id]['step'] = 'finished'
            
        except ValueError:
            bot.reply_to(message, "Kripya keval sankhya (number) likhein.")

print("Bot shuru ho raha hai... Google Sheet check karein!")
bot.polling(none_stop=True)