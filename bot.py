import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

# YAHAN APNA BOTFATHER WALA API TOKEN PASTE KAREIN
TOKEN = '8522964450:AAHFceuLIFr3PNMFaxAu5X70zMcdM6I0ahg'
PASSWORD = "123456"

# 100 Codes ki list (Generator Logic)
mereCodes = [
    {"code": "100378118471001", "pin": "154001", "status": "Valid"},
    {"code": "100378118471002", "pin": "154002", "status": "Valid"},
    {"code": "100378118471003", "pin": "154003", "status": "Valid"},
    {"code": "100378118471004", "pin": "154004", "status": "Invalid"},
    {"code": "100378118471005", "pin": "154005", "status": "Valid"},
    {"code": "100378118471006", "pin": "154006", "status": "Valid"},
    {"code": "100378118471007", "pin": "154007", "status": "Valid"},
    {"code": "100378118471008", "pin": "154008", "status": "Invalid"},
    {"code": "100378118471009", "pin": "154009", "status": "Valid"},
    {"code": "100378118471010", "pin": "154010", "status": "Valid"}
    # Aap ismein baaki codes isi tarah add kar sakte hain
]

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
user_logged_in = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Domino Generator Bot v1.0\nLogin ke liye: /login 123456")

async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args and context.args[0] == PASSWORD:
        user_logged_in[update.effective_user.id] = True
        await update.message.reply_text("✅ Login Successful! /generate <count> ka use karein.")
    else:
        await update.message.reply_text("❌ Login Failed!")

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Yeh aapki QR photo file hai
    await update.message.reply_photo(photo=open('1000759882.jpg', 'rb'), caption="Payment QR: Scan and send screenshot.")

async def generate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not user_logged_in.get(update.effective_user.id):
        await update.message.reply_text("🔒 Login zaroori hai.")
        return

    try:
        count = int(context.args[0])
        await update.message.reply_text(f"⚙️ {count} codes generate ho rahe hain... (5 sec delay per code)")
        
        for i in range(count):
            data = mereCodes[i % len(mereCodes)]
            await asyncio.sleep(5) # 5 Second ka delay
            status = "✅ VALID" if data["status"] == "Valid" else "❌ INVALID"
            response = f"[{i+1}] Code: {data['code']}\nPIN: {data['pin']}\nStatus: {status}"
            await update.message.reply_text(response)
            
    except Exception as e:
        await update.message.reply_text("Error: /generate <number> sahi dalein.")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('login', login))
    application.add_handler(CommandHandler('buy', buy))
    application.add_handler(CommandHandler('generate', generate))
    application.run_polling()
