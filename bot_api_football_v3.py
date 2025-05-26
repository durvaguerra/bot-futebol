import asyncio
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

API_KEY = "bf3c7810eb457a741586bce8885be575"
BASE_URL = "https://v3.football.api-sports.io"

HEADERS = {
    "x-apisports-key": API_KEY
}

async def buscar_time(nome_time):
    url = f"{BASE_URL}/teams"
    params = {"search": nome_time}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS, params=params)
    data = response.json()
    return data["response"][0]["team"]["id"] if data["response"] else None

async def buscar_partidas_proximas(team_id):
    url = f"{BASE_URL}/fixtures"
    params = {"team": team_id, "next": 1}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS, params=params)
    return response.json()["response"]

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    if "x" not in texto and "X" not in texto:
        await update.message.reply_text("Envie no formato: Time1 x Time2")
        return

    time1, time2 = [t.strip() for t in texto.lower().replace("x", "X").split("X")]

    id1 = await buscar_time(time1)
    id2 = await buscar_time(time2)

    if not id1 or not id2:
        await update.message.reply_text("Não encontrei um dos times.")
        return

    jogos1 = await buscar_partidas_proximas(id1)
    jogos2 = await buscar_partidas_proximas(id2)

    confronto = None
    for j in jogos1:
        if j["teams"]["home"]["id"] == id2 or j["teams"]["away"]["id"] == id2:
            confronto = j
            break

    if not confronto:
        for j in jogos2:
            if j["teams"]["home"]["id"] == id1 or j["teams"]["away"]["id"] == id1:
                confronto = j
                break

    if not confronto:
        await update.message.reply_text("Não encontrei confronto entre os times.")
        return

    home = confronto["teams"]["home"]["name"]
    away = confronto["teams"]["away"]["name"]
    date = confronto["fixture"]["date"][:10]
    liga = confronto["league"]["name"]

    msg = f"📆 Próximo jogo entre {home} (mandante) e {away} (visitante)"
    msg += f"🏆 {liga}📍 Data: {date}"

    await update.message.reply_text(msg)

async def main():
    app = ApplicationBuilder().token("7803447059:AAFctdVYOdFjgBgo_umhxI-JOh90GWloqGk").build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))
    print("Bot com API v3 rodando...")
    await app.run_polling()

import nest_asyncio

if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())