import asyncio
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import nest_asyncio
from datetime import datetime
import requests

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

    resposta = f"📆 Próximo jogo entre {home} (mandante) e {away} (visitante)\n"
    resposta += f"🏆 {liga}\n📍 Data: {dt}"

    # Últimos jogos (forçando temporada 2023 porque o plano gratuito não permite 2025)
    ultimos1 = await buscar_ultimos_jogos(id1, 2023)
    ultimos2 = await buscar_ultimos_jogos(id2, 2023)

    texto_ultimos = "📈 Últimos jogos:\n\n"

    texto_ultimos += f"{nome1}:\n"
    if ultimos1:
        for jogo in ultimos1:
            texto_ultimos += f"{jogo['data']}: {jogo['placar']}\n"
    else:
        texto_ultimos += "Sem dados disponíveis.\n"

    texto_ultimos += f"\n{nome2}:\n"
    if ultimos2:
        for jogo in ultimos2:
            texto_ultimos += f"{jogo['data']}: {jogo['placar']}\n"
    else:
        texto_ultimos += "Sem dados disponíveis.\n"

    # Adicione essa linha onde for combinar as mensagens
    mensagem += f"\n\n{texto_ultimos}"
    texto_jogos = "\n\n📈 Últimos jogos:\n"
    texto_jogos += f"\n{jogo['teams']['home']['name']}:\n" + "\n".join(ultimos_jogos_mandante)
    texto_jogos += f"\n\n{jogo['teams']['away']['name']}:\n" + "\n".join(ultimos_jogos_visitante)

    resposta += texto_jogos
    await update.message.reply_text(resposta)

def buscar_ultimos_jogos(time_id, temporada):
    url = f"{BASE_URL}/fixtures"
    params = {
        "team": time_id,
        "season": temporada,
        "status": "FT",
        "limit": 5
    }
    response = requests.get(url, headers=HEADERS, params=params)
    print("Resposta últimos jogos:", response.text)  # ADICIONE ESTA LINHA
    data = response.json()

    jogos = []
    for item in data.get("response", []):
        try:
            data_jogo = item["fixture"]["date"][:10]
            mandante = item["teams"]["home"]["name"]
            visitante = item["teams"]["away"]["name"]
            placar_mandante = item["goals"]["home"]
            placar_visitante = item["goals"]["away"]
            jogos.append(f"{data_jogo}: {mandante} {placar_mandante}x{placar_visitante} {visitante}")
        except Exception as e:
            print("Erro ao processar jogo:", e)
    return jogos


async def main():
    app = ApplicationBuilder().token("7803447059:AAFctdVYOdFjgBgo_umhxI-JOh90GWloqGk").build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))
    print("Bot com confronto futuro rodando...")
    await app.run_polling()

if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())