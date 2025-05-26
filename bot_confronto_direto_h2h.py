import asyncio
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import nest_asyncio
from datetime import datetime

API_KEY = "bf3c7810eb457a741586bce8885be575"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

async def buscar_id_time(nome_time):
    url = f"{BASE_URL}/teams"
    params = {"search": nome_time}
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=HEADERS, params=params)
        data = r.json()
    for team in data.get("response", []):
        if team["team"]["name"].lower().startswith(nome_time.lower()):
            return team["team"]["id"]
    return None

async def buscar_confronto_direto(id1, id2):
    url = f"{BASE_URL}/fixtures/headtohead"
    params = {
        "h2h": f"{id1}-{id2}",
        "season": datetime.now().year
    }
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=HEADERS, params=params)
        jogos = r.json().get("response", [])
    futuros = [j for j in jogos if j["fixture"]["date"] > datetime.now().isoformat()]
    return futuros[0] if futuros else None

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    if "x" not in texto.lower():
        await update.message.reply_text("Envie no formato: Time1 x Time2")
        return

    time1, time2 = [t.strip() for t in texto.lower().replace("x", "X").split("X")]

    id1 = await buscar_id_time(time1)
    id2 = await buscar_id_time(time2)

    if not id1 or not id2:
        await update.message.reply_text("Não encontrei um dos times.")
        return

    jogo = await buscar_confronto_direto(id1, id2)
    if not jogo:
        jogo = await buscar_confronto_direto(id2, id1)

    if not jogo:
        await update.message.reply_text("Não encontrei confronto entre os times.")
        return

    home = jogo["teams"]["home"]["name"]
    away = jogo["teams"]["away"]["name"]
    liga = jogo["league"]["name"]
    data = jogo["fixture"]["date"][:10]

    resposta = f"📆 Próximo jogo entre {home} (mandante) e {away} (visitante)\n"
    resposta += f"🏆 {liga}\n📍 Data: {data}"
    await update.message.reply_text(resposta)

async def main():
    app = ApplicationBuilder().token("7803447059:AAFctdVYOdFjgBgo_umhxI-JOh90GWloqGk").build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))
    print("Bot com confronto direto rodando...")
    await app.run_polling()

if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())