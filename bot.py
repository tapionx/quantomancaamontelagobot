import os
import re
import json
import asyncio
import datetime
import logging

import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = os.getenv("TOKEN")
ADMIN_CHAT_ID = 6847615

SITE_URL = "https://www.quantomancaamontelago.it/"

RETRY_ATTEMPTS = 5
RETRY_COOLDOWN = 15  # secondi

# Nessun fallback hardcoded: finché il fetch non riesce la data non c'è
MONTELAGO = None

EVENT_DATA_RE = re.compile(r'<script[^>]*id="event-data"[^>]*>(.*?)</script>', re.DOTALL)

async def fetch_festival_date() -> datetime.datetime:
    async with httpx.AsyncClient() as client:
        response = await client.get(SITE_URL, timeout=10, follow_redirects=True)
    response.raise_for_status()
    match = EVENT_DATA_RE.search(response.text)
    if not match:
        raise ValueError('script id="event-data" non trovato nella pagina')
    event = json.loads(match.group(1))
    return datetime.datetime.fromisoformat(event["startDate"])

async def load_festival_date(application):
    global MONTELAGO
    for attempt in range(1, RETRY_ATTEMPTS + 1):
        try:
            MONTELAGO = await fetch_festival_date()
            logger.info("Data del festival caricata dal sito: %s", MONTELAGO)
            return
        except Exception:
            logger.exception("Tentativo %d/%d di scaricare la data fallito", attempt, RETRY_ATTEMPTS)
            if attempt < RETRY_ATTEMPTS:
                await asyncio.sleep(RETRY_COOLDOWN)
    logger.error("Impossibile scaricare la data del festival dopo %d tentativi", RETRY_ATTEMPTS)
    await application.bot.send_message(
        chat_id=ADMIN_CHAT_ID,
        text="⚠️ Non sono riuscito a scaricare la data del festival da {} dopo {} tentativi. Usa /reload per riprovare.".format(SITE_URL, RETRY_ATTEMPTS),
    )

async def post_init(application):
    # in background, così il bot risponde subito anche durante i retry
    application.create_task(load_festival_date(application))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(update)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Ciao! Usa il comando /quanto_manca per sapere quanto manca al Montelago Celtic Festival")

async def quanto_manca(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(update)
    if MONTELAGO is None:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Non conosco ancora la data del festival, riprova tra poco!")
        return
    now = datetime.datetime.now(datetime.timezone.utc)
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

async def reload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global MONTELAGO
    print(update)
    try:
        MONTELAGO = await fetch_festival_date()
        text = "Data ricaricata dal sito: {}".format(MONTELAGO)
    except Exception as e:
        text = "Errore nel ricaricare la data ({}), resta in uso: {}".format(e, MONTELAGO)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

if __name__ == '__main__':
    application = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)
    application.add_handler(CommandHandler("quanto_manca", quanto_manca))
    # comando "nascosto": non pubblicizzato nella UI di Telegram
    application.add_handler(CommandHandler("reload", reload))

    application.run_polling()
