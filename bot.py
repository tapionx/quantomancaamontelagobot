import os
import datetime
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.getenv("TOKEN")

# 2025-07-29T16:00:00.000
MONTELAGO = datetime.datetime(2025, 7, 29, 16, 0, 0)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(update)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Ciao! Usa il comando /quanto_manca per sapere quanto manca al Montelago Celtic Festival")

async def quanto_manca(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(update)
    now = datetime.datetime.now()
    if MONTELAGO < now:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="CI SIAMO!")
        return
    delta = MONTELAGO - now
    delta_text = 'Mancano {} giorni, {} ore, {} minuti e {} secondi al <a href="https://www.montelagocelticfestival.it/">Montelago Celtic Festival</a>'.format(delta.days, delta.seconds // 3600, (delta.seconds // 60) % 60, delta.seconds % 60)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, 
        text=delta_text,
        parse_mode='HTML',
        disable_web_page_preview=True,
    )  

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).build()
    
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)
    application.add_handler(CommandHandler("quanto_manca", quanto_manca))
    
    application.run_polling()
