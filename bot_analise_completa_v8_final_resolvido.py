
import asyncio
import httpx
import nest_asyncio
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = "7803447059:AAFctdVYOdFjgBgo_umhxI-JOh90GWloqGk"
API_KEY = "x-rapidapi-key: 3241e99e70msh46d8894245e36fcp11fa9bjsn53fda60e6ec4"
HEADERS = {"X-RapidAPI-Key": API_KEY, "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"}

async def buscar_id_nome_time(nome_time):
    url = f"https://api-football-v1.p.rapidapi.com/v3/teams"
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=HEADERS, params={"search": nome_time})
        if r.status_code == 200 and r.json()["response"]:
            time = r.json()["response"][0]["team"]
            return time["id"], time["name"]
    return None, None

async def buscar_confronto(id1, id2):
    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures/headtohead"
    params = {"h2h": f"{id1}-{id2}", "last": 1}
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=HEADERS, params=params)
        if r.status_code == 200 and r.json()["response"]:
            jogos = r.json()["response"]
            for jogo in jogos:
                data_jogo = datetime.fromisoformat(jogo["fixture"]["date"].replace("Z", "+00:00"))
                if data_jogo > datetime.now(timezone.utc):
                    return jogo
    return None

async def buscar_ultimos_jogos(id_time):
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    params = {"team": id_time, "last": 5}
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=HEADERS, params=params)
        if r.status_code == 200:
            return r.json()["response"]
    return []

async def buscar_estatisticas(id_time, temporada):
    url = f"https://api-football-v1.p.rapidapi.com/v3/teams/statistics"
    params = {"team": id_time, "season": temporada, "league": 71}
    async with httpx.AsyncClient() as client:
        r = await client.get(url, headers=HEADERS, params=params)
        if r.status_code == 200:
            data = r.json()["response"]
            gols = data.get("goals", {}).get("for", {}).get("average", {}).get("total", {}).get("home", "N/D")
            escanteios = data.get("corners", {}).get("total", "N/D")
            amarelos = data.get("cards", {}).get("yellow", {}).get("total", {}).get("home", "N/D")
            vermelhos = data.get("cards", {}).get("red", {}).get("total", {}).get("home", "N/D")
            return gols, escanteios, amarelos, vermelhos
    return "N/D", "N/D", "N/D", "N/D"

def formatar_ultimos_jogos(jogos):
    texto = ""
    for jogo in jogos:
        d = jogo["fixture"]["date"][:10]
        casa = jogo["teams"]["home"]["name"]
        fora = jogo["teams"]["away"]["name"]
        g_casa = jogo["goals"]["home"]
        g_fora = jogo["goals"]["away"]
        texto += f"{d}: {casa} {g_casa}x{g_fora} {fora}\n"
    return texto.strip()

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    if " x " not in texto.lower():
        await update.message.reply_text("Envie no formato: time1 x time2")
        return
    t1, t2 = map(str.strip, texto.lower().split(" x "))
    id1, nome1 = await buscar_id_nome_time(t1)
    id2, nome2 = await buscar_id_nome_time(t2)
    if not id1 or not id2:
        await update.message.reply_text("Time(s) não encontrado(s).")
        return
    jogo = await buscar_confronto(id1, id2)
    if not jogo:
        await update.message.reply_text("Não encontrei confronto futuro.")
        return
    data = jogo["fixture"]["date"][:10]
    campeonato = jogo["league"]["name"]
    mandante = jogo["teams"]["home"]["name"]
    visitante = jogo["teams"]["away"]["name"]
    temporada = jogo["league"]["season"]

    ult1 = await buscar_ultimos_jogos(id1)
    ult2 = await buscar_ultimos_jogos(id2)
    gols1, esc1, am1, vm1 = await buscar_estatisticas(id1, temporada)
    gols2, esc2, am2, vm2 = await buscar_estatisticas(id2, temporada)

    texto_final = f"Proximo jogo entre {mandante} (mandante) e {visitante} (visitante)\n"
    texto_final += f"Campeonato: {campeonato}\nData: {data}\n\n"
    texto_final += f"Ultimos jogos de {mandante}:\n{formatar_ultimos_jogos(ult1)}\n\n"
    texto_final += f"Ultimos jogos de {visitante}:\n{formatar_ultimos_jogos(ult2)}\n\n"
    texto_final += f"Estatisticas medias:\n- {mandante}: Gols: {gols1} | Escanteios: {esc1} | CA: {am1} | CV: {vm1}\n"
    texto_final += f"- {visitante}: Gols: {gols2} | Escanteios: {esc2} | CA: {am2} | CV: {vm2}"

    await update.message.reply_text(texto_final)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Envie o confronto no formato: flamengo x vasco")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("Bot com análise completa v8 rodando.")
    await app.run_polling()

if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())
