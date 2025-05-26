import asyncio
import datetime
import pytz
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

#CONFIGURAÇÕES

API_KEY = "bf3c7810eb457a741586bce8885be575"
BASE_URL = "https://v3.football.api-sports.io"
BOT_TOKEN = "7803447059:AAFctdVYOdFjgBgo_umhxI-JOh90GWloqGk"
HEADERS = {"x-apisports-key": API_KEY}

#AJUSTA FUSO HORÁRIO

def ajustar_para_brasilia(data_iso):
    utc_time = datetime.datetime.fromisoformat(data_iso.replace("Z", "+00:00"))
    brasília_tz = pytz.timezone("America/Sao_Paulo")
    return utc_time.astimezone(brasília_tz).strftime("%Y-%m-%d %H:%M")

#BUSCAR ID DO TIME

async def buscar_id(nome):
    url = f"{BASE_URL}/teams?search={nome}"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=HEADERS)
        resultados = r.json().get("response", [])
        for time in resultados:
            if time["team"]["country"] == "Brazil" or nome.lower() in time["team"]["name"].lower():
                return time["team"]
                return None

#BUSCAR JOGO FUTURO

async def buscar_jogo(id1, id2):
    url = f"{BASE_URL}/fixtures/headtohead?h2h={id1}-{id2}"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=HEADERS)
        jogos = r.json().get("response", [])
        hoje = datetime.datetime.now(pytz.UTC)
        for jogo in jogos:
            data = datetime.datetime.fromisoformat(jogo["fixture"]["date"].replace("Z", "+00:00"))
            if data > hoje:
                return jogo
                return None

#BUSCAR CLASSIFICAÇÃO

async def buscar_classificacao(league_id, season, team_id):
    url = f"{BASE_URL}/standings?league={league_id}&season={season}"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=HEADERS)
        dados = r.json().get("response", [])
        if dados:
            for time in dados[0]["league"]["standings"][0]:
                if time["team"]["id"] == team_id:
                    return time["rank"]
                    return "N/D"

#BUSCAR Últimos Jogos

async def ultimos_jogos(team_id):
    hoje = datetime.datetime.now().strftime("%Y-%m-%d")
    url = f"{BASE_URL}/fixtures?team={team_id}&to={hoje}&status=FT&last=5"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=HEADERS)
        jogos = r.json().get("response", [])
        texto = ""
        for j in jogos:
            mand = j["teams"]["home"]["name"]
            visit = j["teams"]["away"]["name"]
            g1 = j["goals"]["home"]
            g2 = j["goals"]["away"]
            data = j["fixture"]["date"][:10]
            texto += f"{data}: {mand} {g1}x{g2} {visit}\n"
            return texto or "N/D"

#FUNÇÃO PRINCIPAL

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    if "x" not in texto:
        await update.message.reply_text("Envie no formato: time1 x time2")
        return

time1, time2 = map(str.strip, texto.lower().split("x"))
t1 = await buscar_id(time1)
t2 = await buscar_id(time2)

if not t1 or not t2:
    await update.message.reply_text("Time(s) não encontrado(s).")
    return

jogo = await buscar_jogo(t1["id"], t2["id"])
if not jogo:
    await update.message.reply_text("Não encontrei confronto futuro.")
    return

data_jogo = ajustar_para_brasilia(jogo["fixture"]["date"])
campeonato = jogo["league"]["name"]
temporada = jogo["league"]["season"]
league_id = jogo["league"]["id"]
mandante = jogo["teams"]["home"]
visitante = jogo["teams"]["away"]

texto1 = f"\ud83d\uddd3\ufe0f Próximo jogo entre {mandante['name']} (mandante) e {visitante['name']} (visitante)\n\ud83c\udfc6 {campeonato}\n\ud83d\udccd Data: {data_jogo}"
await update.message.reply_text(texto1)

# Classificação e escudos
rank1 = await buscar_classificacao(league_id, temporada, mandante['id'])
rank2 = await buscar_classificacao(league_id, temporada, visitante['id'])
escudo1 = mandante['logo']
escudo2 = visitante['logo']

texto2 = f"\ud83d\udcc8 Classificação atual:\n{mandante['name']}: {rank1}º lugar\n{visitante['name']}: {rank2}º lugar\n\n\ud83d\ude9a Escudos:\n{mandante['name']}: {escudo1}\n{visitante['name']}: {escudo2}"
await update.message.reply_text(texto2)

# Últimos jogos
ult1 = await ultimos_jogos(mandante['id'])
ult2 = await ultimos_jogos(visitante['id'])
texto3 = f"\ud83d\udcc9 Últimos jogos de {mandante['name']}:\n{ult1}\n\n\ud83d\udcc9 Últimos jogos de {visitante['name']}:\n{ult2}"
await update.message.reply_text(texto3)

#COMANDO /start

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Olá! Envie dois times no formato: time1 x time2")

#MAIN

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("Bot com API v3 rodando...")
    await app.run_polling()

if name == 'main': asyncio.run(main())