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

async def buscar_confronto_futuro(id1, id2):
    url = f"{BASE_URL}/fixtures/headtohead"
    params = {"h2h": f"{id1}-{id2}"}
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=HEADERS, params=params)
        jogos = r.json().get("response", [])
    futuros = [j for j in jogos if j["fixture"]["status"]["short"] in ["NS", "TBD"]]
    if futuros:
        return sorted(futuros, key=lambda j: j["fixture"]["date"])[0]
    return None

async def buscar_ultimos_jogos(id_time):
    url = f"{BASE_URL}/fixtures"
    params = {"team": id_time, "last": 5}
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=HEADERS, params=params)
        return r.json().get("response", [])

def formatar_jogo(jogo):
    data = datetime.fromisoformat(jogo["fixture"]["date"].replace("Z", "+00:00")).strftime("%Y-%m-%d")
    home = jogo["teams"]["home"]["name"]
    away = jogo["teams"]["away"]["name"]
    gols_home = jogo["goals"]["home"]
    gols_away = jogo["goals"]["away"]
    placar = f"{home} {gols_home}x{gols_away} {away}"
    return f"{data}: {placar}"

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

    jogo = await buscar_confronto_futuro(id1, id2)
    if not jogo:
        jogo = await buscar_confronto_futuro(id2, id1)
    if not jogo:
        await update.message.reply_text("Não encontrei confronto futuro entre os times.")
        return

    home = jogo["teams"]["home"]["name"]
    away = jogo["teams"]["away"]["name"]
    liga = jogo["league"]["name"]
    data = jogo["fixture"]["date"]
    dt = datetime.fromisoformat(data.replace("Z", "+00:00")).strftime("%Y-%m-%d %H:%M")

    texto_jogo = f"📆 Próximo jogo entre {home} (mandante) e {away} (visitante)\n"
    texto_jogo += f"🏆 {liga}\n📍 Data: {dt}"
    await update.message.reply_text(texto_jogo)

    id_mandante = jogo["teams"]["home"]["id"]
    id_visitante = jogo["teams"]["away"]["id"]

    ult_mandante = await buscar_ultimos_jogos(id_mandante)
    ult_visitante = await buscar_ultimos_jogos(id_visitante)

    texto_mandante = f"📈 Últimos jogos de {home}:\n"
    for jogo in ult_mandante:
        texto_mandante += formatar_jogo(jogo) + "\n"

    texto_visitante = f"📈 Últimos jogos de {away}:\n"
    for jogo in ult_visitante:
        texto_visitante += formatar_jogo(jogo) + "\n"

    await update.message.reply_text(texto_mandante.strip())
    await update.message.reply_text(texto_visitante.strip())

async def main():
    app = ApplicationBuilder().token("7803447059:AAFctdVYOdFjgBgo_umhxI-JOh90GWloqGk").build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))
    print("Bot com últimos jogos rodando...")
    await app.run_polling()

if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())