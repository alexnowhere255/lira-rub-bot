import os
import re
import time
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.environ["BOT_TOKEN"]

DEFAULT_RATE = 1.6
CACHE_SECONDS = 60 * 60

_cached_rate = DEFAULT_RATE
_cached_at = 0

def get_rate() -> float:
    global _cached_rate, _cached_at

    now = time.time()

    if now - _cached_at < CACHE_SECONDS:
        return _cached_rate

    try:
        url = "https://api.frankfurter.dev/v1/latest?base=TRY&symbols=RUB"
        response = requests.get(url, timeout=8)
        response.raise_for_status()

        data = response.json()
        rate = float(data["rates"]["RUB"])

        _cached_rate = rate
        _cached_at = now

        return rate

    except Exception:
        return _cached_rate or DEFAULT_RATE

def extract_number(text: str):
    text = text.replace(",", ".")
    match = re.search(r"\d+(\.\d+)?", text)
    return float(match.group()) if match else None

def looks_like_rub(text: str) -> bool:
    text = text.lower()
    return any(word in text for word in ["₽", "руб", "rub", "р"])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Кидай цену, я переведу.\n\n"
        "Примеры:\n"
        "700\n"
        "700₺\n"
        "700₽\n\n"
        "/kurs — показать курс"
    )

async def kurs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rate = get_rate()

    await update.message.reply_text(
        f"📈 Сейчас примерно:\n"
        f"1 ₺ = {rate:.2f} ₽\n"
        f"100 ₺ ≈ {100 * rate:.0f} ₽"
    )

async def convert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    amount = extract_number(text)

    if amount is None:
        await update.message.reply_text(
            "Напиши цену числом, например: 700, 700₺ или 700₽"
        )
        return

    rate = get_rate()

    if looks_like_rub(text):
        lira = amount / rate
        await update.message.reply_text(
            f"💸 {amount:g} ₽ ≈ {lira:.0f} ₺\n\n"
            f"📈 Курс: 1 ₺ = {rate:.2f} ₽"
        )
    else:
        rub = amount * rate
        await update.message.reply_text(
            f"💸 {amount:g} ₺ ≈ {rub:.0f} ₽\n\n"
            f"📈 Курс: 1 ₺ = {rate:.2f} ₽"
        )

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("kurs", kurs))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, convert))

app.run_polling()
