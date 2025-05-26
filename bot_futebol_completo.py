import asyncio
import datetime
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "7803447059:AAFctdVYOdFjgBgo_umhxI-JOh90GWLoqGk"
API_KEY = "3241e99e70msh4608824e5e36fcp11fa9bjsn53fda60e0ec4"
HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
}

def detectar_temporada():
    hoje = datetime.datetime.now(datetime.timezone.utc)
    return hoje.year if hoje.month >= 7 else hoje.year - 1

async def buscar_id_time(nome_time):
    url = "https://api-football-v1.p.rapidapi.com/v3/teams"
    params = {"search": nome_time}
    async with httpx.AsyncClient() as client:
        resposta = await client.get(url, headers=HEADERS, params=params)
        dados = resposta.json()
        for item in dados["response"]:
            if item["team"]["name"].lower() == nome_time.lower():
                return item["team"]["id"], item["team"]["name"]
        if dados["response"]:
            return dados["response"][0]["team"]["id"], dados["response"][0]["team"]["name"]
        return None, nome_time

async def buscar_proximo_jogo(id1, id2):
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures/headtohead"
    params = {"h2h": f"{id1}-{id2}"}
    async with httpx.AsyncClient() as client:
        resposta = await client.get(url, headers=HEADERS, params=params)
        dados = resposta.json()
        jogos_futuros = [j for j in dados["response"] if j["fixture"]["status"]["short"] in ["NS", "TBD"]]
        if not jogos_futuros:
            return None
        return sorted(jogos_futuros, key=lambda j: j["fixture"]["date"])[0]

def converter_data_utc_para_brasilia(data_str):
    data_utc = datetime.datetime.fromisoformat(data_str.replace("Z", "+00:00"))
    fuso_brasilia = datetime.timezone(datetime.timedelta(hours=-3))
    return data_utc.astimezone(fuso_brasilia).strftime("%Y-%m-%d %H:%M")

async def buscar_ultimos_jogos(id_time, temporada):
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    params = {"team": id_time, "season": temporada, "status": "FT", "limit": 5}
    async with httpx.AsyncClient() as client:
        resposta = await client.get(url, headers=HEADERS, params=params)
        jogos = resposta.json().get("response", [])
        resultados = []
        for j in jogos:
            time_casa = j["teams"]["home"]["name"]
            time_fora = j["teams"]["away"]["name"]
            gols_casa = j["goals"]["home"]
            gols_fora = j["goals"]["away"]
            data = j["fixture"]["date"][:10]
            resultados.append(f"{data}: {time_casa} {gols_casa}x{gols_fora} {time_fora}")
        return resultados

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    if "x" not in texto.lower():
        await update.message.reply_text("Envie os dois times no formato: time1 x time2")
        return

    time1, time2 = map(str.strip, texto.lower().split("x"))
    temporada = detectar_temporada()

    id1, nome1 = await buscar_id_time(time1)
    id2, nome2 = await buscar_id_time(time2)

    if not id1 or not id2:
        await update.message.reply_text("Time(s) não encontrado(s).")
        return

    jogo = await buscar_proximo_jogo(id1, id2)
    if not jogo:
        await update.message.reply_text("Não encontrei confronto futuro.")
        return

    mandante = jogo["teams"]["home"]["name"]
    visitante = jogo["teams"]["away"]["name"]
    campeonato = jogo["league"]["name"]
    data = converter_data_utc_para_brasilia(jogo["fixture"]["date"])

    texto = f"📆 Próximo jogo entre {mandante} (mandante) e {visitante} (visitante)"
    texto += f"🏆 {campeonato}\n 📍 Data: {data}"

    await update.message.reply_text(texto)

    ultimos1 = await buscar_ultimos_jogos(id1, temporada)
    ultimos2 = await buscar_ultimos_jogos(id2, temporada)

    await update.message.reply_text(
        f"📉 Últimos jogos de {nome1}:\n" +
        ("\n".join(ultimos1) if ultimos1 else "N/D")
    )

    await update.message.reply_text(
        f"📉 Últimos jogos de {nome2}:\n" +
        ("\n".join(ultimos2) if ultimos2 else "N/D")
    )

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("Bot com análise completa v8 rodando...")
    await app.run_polling()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if str(e).startswith("This event loop is already running"):
            loop = asyncio.get_event_loop()
            loop.create_task(main())
            loop.run_forever()
        else:
            raise
