import asyncio
import nest_asyncio
import datetime
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# === CONFIGURAÇÕES ===
API_KEY = "bf3c7810eb457a741586bce8885be575"
BOT_TOKEN = "7803447059:AAFctdVYOdFjgBgo_umhxI-JOh90GWloqGk"
API_URL = "https://v3.football.api-sports.io"

headers = {
    "x-apisports-key": API_KEY
}

# === FUNÇÕES AUXILIARES ===

def detectar_temporada():
    hoje = datetime.datetime.now(datetime.timezone.utc).date()
    return hoje.year + 1 if hoje.month >= 7 else hoje.year

def buscar_time_id(nome):
    response = requests.get(f"{API_URL}/teams", headers=headers, params={"search": nome})
    data = response.json()
    if data["results"] > 0:
        for t in data["response"]:
            if t["team"]["name"].lower().startswith(nome.lower()):
                return t["team"]["id"], t["team"]["name"]
    return None, None

def buscar_confronto(id1, id2):
    temporada = detectar_temporada()
    response = requests.get(f"{API_URL}/fixtures/headtohead", headers=headers, params={"h2h": f"{id1}-{id2}", "season": temporada})
    data = response.json()
    jogos = data.get("response", [])
    futuros = [j for j in jogos if j["fixture"]["status"]["short"] in ("NS", "TBD")]
    return sorted(futuros, key=lambda j: j["fixture"]["date"]) if futuros else None

def converter_data_utc_para_brasilia(data_utc):
    dt_utc = datetime.datetime.fromisoformat(data_utc.replace("Z", "+00:00"))
    dt_brasilia = dt_utc - datetime.timedelta(hours=3)
    return dt_brasilia.strftime("%d/%m/%Y %H:%M")

def gerar_analise_jogo(jogo):
    mandante = jogo["teams"]["home"]["name"]
    visitante = jogo["teams"]["away"]["name"]
    campeonato = jogo["league"]["name"]
    data = converter_data_utc_para_brasilia(jogo["fixture"]["date"])
    texto1 = f"📆 Próximo jogo entre {mandante} (mandante) e {visitante} (visitante)\n"
    texto1 += f"🏆 {liga}\n📍 Data: {data_brasilia}\n"
    texto1 += f"\n{mandante}: ![]({escudo1})\n{visitante}: ![]({escudo2})"

# === HANDLER ===

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if "x" not in update.message.text.lower():
        await update.message.reply_text("Envie a partida no formato: Time A x Time B")
        return
    time1, time2 = map(str.strip, update.message.text.lower().split("x", 1))
    id1, nome1 = buscar_time_id(time1)
    id2, nome2 = buscar_time_id(time2)
    if not id1 or not id2:
        await update.message.reply_text("Não encontrei um dos times. Verifique os nomes.")
        return
    jogos = buscar_confronto(id1, id2)
    if not jogos:
        await update.message.reply_text("Não encontrei confrontos futuros entre esses times.")
        return
    texto = gerar_analise_jogo(jogos[0])
    await update.message.reply_text(texto)

# === MAIN ===

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))
    print("Bot com análise completa v8 rodando...")
    await app.run_polling()

if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(main())
