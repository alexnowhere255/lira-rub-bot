import os
import re
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.environ["BOT_TOKEN"]
DEFAULT_RATE = 1.6

def get_rate() -> float:
    try:
        url = "https://api.frankfurter.dev/v1/latest?base=TRY&symbols=RUB"
        data = requests.get(url, timeout=8).json()
        return float(data["rates"]["RUB"])
    except Exception:
        return DEFAULT_RATE

def extract_number(text: str):
    text = text.replace(",", ".")
    match = re.search(r"\d+(\.\d+)?", text)
    return float(match.group()) if match else None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Кидай цену в лирах: 350\n"
        "Я переведу в рубли по актуальному курсу.\n\n"
        "/kurs — показать курс"
    )

async def kurs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rate = get_rate()
    await update.message.reply_text(f"Сейчас примерно: 1 ₺ = {rate:.2f} ₽")

async def convert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    amount = extract_number(update.message.text)

    if amount is None:
        await update.message.reply_text("Напиши цену числом, например: 350 или 350₺")
        return

    rate = get_rate()
    rub = amount * rate

    await update.message.reply_text(
        f"{amount:g} ₺ ≈ {rub:.0f} ₽\n"
        f"Курс: 1 ₺ = {rate:.2f} ₽"
    )

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("kurs", kurs))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, convert))

app.run_polling()