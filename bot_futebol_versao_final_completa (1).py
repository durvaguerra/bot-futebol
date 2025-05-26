import asyncio
import httpx
from datetime import datetime, timedelta, timezone
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# Configurações da API
API_KEY = "bf3c7810eb457a741586bce8885be575"
HEADERS = {"x-apisports-key": API_KEY}
BASE_URL = "https://v3.football.api-sports.io"

# Token do Bot
BOT_TOKEN = "7803447059:AAFctdVYOdFjgBgo_umhxI-JOh90GWloqGk"

# Funções auxiliares ----------------------------------------------

async def buscar_id_time(nome_time):
    url = f"{BASE_URL}/teams?search={nome_time}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS)
        if response.status_code == 200:
            dados = response.json()
            for time in dados["response"]:
                if time["team"]["country"] == "Brazil":
                    return time["team"]
    return None

async def buscar_proximo_jogo(id1, id2):
    url = f"{BASE_URL}/fixtures/headtohead?h2h={id1}-{id2}&next=1"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS)
        if response.status_code == 200:
            jogos = response.json()["response"]
            if jogos:
                return jogos[0]
    return None

async def buscar_ultimos_jogos(id_time):
    url = f"{BASE_URL}/fixtures?team={id_time}&last=5"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS)
        if response.status_code == 200:
            return response.json()["response"]
    return []

async def buscar_estatisticas(id_time, season):
    url = f"{BASE_URL}/teams/statistics?team={id_time}&season={season}&league=71"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=HEADERS)
        if response.status_code == 200:
            dados = response.json()
            stats = {
                "gols": dados.get("goals", {}).get("for", {}).get("average", {}).get("total", {}).get("home", "N/D"),
                "escanteios": dados.get("corners", {}).get("total", {}).get("home", "N/D"),
                "amarelos": dados.get("cards", {}).get("yellow", {}).get("total", {}).get("home", "N/D"),
                "vermelhos": dados.get("cards", {}).get("red", {}).get("total", {}).get("home", "N/D")
            }
            return stats
    return {"gols": "N/D", "escanteios": "N/D", "amarelos": "N/D", "vermelhos": "N/D"}

async def enviar_texto_em_partes(texto, update: Update):
    partes = [texto[i:i+4000] for i in range(0, len(texto), 4000)]
    for parte in partes:
        await update.message.reply_text(parte)

# Manipulador principal ------------------------------------------

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text

    # Separar nomes dos times
    if " x " in texto:
        time1, time2 = texto.split(" x ")
    elif " X " in texto:
        time1, time2 = texto.split(" X ")
    else:
        await update.message.reply_text("Formato inválido. Use: Time1 x Time2")
        return

    # Buscar dados dos times
    dados_time1 = await buscar_id_time(time1.strip())
    dados_time2 = await buscar_id_time(time2.strip())

    if not dados_time1 or not dados_time2:
        await update.message.reply_text("Não encontrei um dos times.")
        return

    id1, nome1, escudo1 = dados_time1["id"], dados_time1["name"], dados_time1["logo"]
    id2, nome2, escudo2 = dados_time2["id"], dados_time2["name"], dados_time2["logo"]

    # Buscar próximo confronto
    jogo = await buscar_proximo_jogo(id1, id2)
    if not jogo:
        await update.message.reply_text("Não encontrei confronto entre os times.")
        return

    mandante = jogo["teams"]["home"]["name"]
    visitante = jogo["teams"]["away"]["name"]
    data_jogo = jogo["fixture"]["date"]
    liga = jogo["league"]["name"]
    season = jogo["league"]["season"]

    data_obj = datetime.fromisoformat(data_jogo.replace("Z", "+00:00"))
    data_brasilia = data_obj.astimezone(timezone(timedelta(hours=-3))).strftime("%d/%m/%Y %H:%M")

    # Enviar informações do jogo
    texto1 = (
        f"📆 Próximo jogo entre {mandante} (mandante) e {visitante} (visitante)\n"
        f"🏆 {liga}\n📍 Data: {data_brasilia}\n"
        f"\n{mandante}: ![]({escudo1})\n{visitante}: ![]({escudo2})"
    )
    await update.message.reply_text(texto1)

    # Últimos jogos do mandante
    ult_mandante = await buscar_ultimos_jogos(id1)
    texto_m = f"📈 Últimos jogos de {mandante}:\n"
    for j in ult_mandante:
        dt = j["fixture"]["date"][:10]
        casa = j["teams"]["home"]["name"]
        fora = j["teams"]["away"]["name"]
        g1 = j["goals"]["home"]
        g2 = j["goals"]["away"]
        texto_m += f"{dt}: {casa} {g1}x{g2} {fora}\n"
    await update.message.reply_text(texto_m)

    # Últimos jogos do visitante
    ult_visitante = await buscar_ultimos_jogos(id2)
    texto_v = f"📈 Últimos jogos de {visitante}:\n"
    for j in ult_visitante:
        dt = j["fixture"]["date"][:10]
        casa = j["teams"]["home"]["name"]
        fora = j["teams"]["away"]["name"]
        g1 = j["goals"]["home"]
        g2 = j["goals"]["away"]
        texto_v += f"{dt}: {casa} {g1}x{g2} {fora}\n"
    await update.message.reply_text(texto_v)

    # Estatísticas médias
    stats_m = await buscar_estatisticas(id1, season)
    stats_v = await buscar_estatisticas(id2, season)

    texto_stats = (
        f"\n📊 Estatísticas médias:\n"
        f"- {mandante}: Gols: {stats_m['gols']} | Escanteios: {stats_m['escanteios']} | "
        f"CA: {stats_m['amarelos']} | CV: {stats_m['vermelhos']}\n"
        f"- {visitante}: Gols: {stats_v['gols']} | Escanteios: {stats_v['escanteios']} | "
        f"CA: {stats_v['amarelos']} | CV: {stats_v['vermelhos']}"
    )
    await update.message.reply_text(texto_stats)

    # Sugestões de mercado (placeholder)
    await update.message.reply_text("🎯 Sugestões de mercado:\n- Over 1.5 gols\n- Ambas marcam: Sim")

# Inicialização do Bot ------------------------------------------

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("Bot com análise completa v8 rodando...")
    asyncio.run(app.run_polling())
