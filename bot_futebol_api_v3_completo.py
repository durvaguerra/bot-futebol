
import asyncio
import httpx
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from datetime import datetime, timedelta, timezone

API_KEY = "bf3c7810eb457a741586bce8885be575"
TELEGRAM_TOKEN = "7803447059:AAFctdVYOdFjgBgo_umhxI-JOh90GWloqGk"
BASE_URL = "https://v3.football.api-sports.io"

headers = {"X-RapidAPI-Key": API_KEY}

def detectar_temporada():
    hoje = datetime.now(timezone.utc).date()
    ano = hoje.year
    if hoje.month >= 7:
        return ano
    return ano - 1

async def buscar_id_time(nome):
    async with httpx.AsyncClient() as client:
        url = f"{BASE_URL}/teams?search={nome}"
        response = await client.get(url, headers=headers)
        data = response.json()
        if data["results"] == 0:
            return None, None
        for item in data["response"]:
            if item["team"]["country"] == "Brazil" and not item["team"]["name"].lower().endswith(("u20", "u23", "w", "se", "pi", "ba", "ac")):
                return item["team"]["id"], item["team"]["name"]
        return data["response"][0]["team"]["id"], data["response"][0]["team"]["name"]

async def buscar_confronto(id1, id2):
    temporada = detectar_temporada()
    async with httpx.AsyncClient() as client:
        url = f"{BASE_URL}/fixtures/headtohead?h2h={id1}-{id2}&season={temporada}"
        r = await client.get(url, headers=headers)
        dados = r.json()
        jogos_futuros = [j for j in dados["response"] if j["fixture"]["status"]["short"] in ["NS", "TBD"]]
        if not jogos_futuros:
            return None
        return sorted(jogos_futuros, key=lambda j: j["fixture"]["date"])[0]

async def buscar_ultimos_jogos(team_id):
    async with httpx.AsyncClient() as client:
        url = f"{BASE_URL}/fixtures?team={team_id}&last=5"
        r = await client.get(url, headers=headers)
        data = r.json()
        jogos = []
        for j in data["response"]:
            date = j["fixture"]["date"][:10]
            home = j["teams"]["home"]["name"]
            away = j["teams"]["away"]["name"]
            sh = j["goals"]["home"]
            sa = j["goals"]["away"]
            jogos.append(f"{date}: {home} {sh}x{sa} {away}")
        return jogos

async def buscar_estatisticas(team_id):
    temporada = detectar_temporada()
    async with httpx.AsyncClient() as client:
        url = f"{BASE_URL}/teams/statistics?team={team_id}&season={temporada}&league=71"
        r = await client.get(url, headers=headers)
        data = r.json()
        try:
            stats = data["response"]
            gols = stats.get("goals", {}).get("for", {}).get("average", {}).get("total", {}).get("home", "N/D")
            esc = stats.get("lineups", [{}])[0].get("statistics", {}).get("corners", "N/D")
            am = stats.get("cards", {}).get("yellow", {}).get("total", {}).get("home", "N/D")
            vm = stats.get("cards", {}).get("red", {}).get("total", {}).get("home", "N/D")
        except:
            gols, esc, am, vm = "N/D", "N/D", "N/D", "N/D"
        return gols, esc, am, vm

async def responder(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    if " x " not in texto.lower():
        await update.message.reply_text("Envie no formato: Time A x Time B")
        return
    t1, t2 = [i.strip() for i in texto.split("x")]

    id1, nome1 = await buscar_id_time(t1)
    id2, nome2 = await buscar_id_time(t2)
    if not id1 or not id2:
        await update.message.reply_text("Não encontrei um dos times.")
        return

    jogo = await buscar_confronto(id1, id2)
    if not jogo:
        await update.message.reply_text("Não encontrei confronto entre os times.")
        return

    data = jogo["fixture"]["date"]
    estadio = jogo["fixture"]["venue"]["name"]
    liga = jogo["league"]["name"]
    mandante = jogo["teams"]["home"]["name"]
    visitante = jogo["teams"]["away"]["name"]
    data_brasilia = datetime.fromisoformat(data.replace("Z", "+00:00")).astimezone(timezone(timedelta(hours=-3)))
    data_formatada = data_brasilia.strftime("%d/%m/%Y %H:%M")

    texto1 = f"📆 Próximo jogo entre {mandante} (mandante) e {visitante} (visitante)\n"
    texto1 += f"🏆 {liga}\n📍 Data: {data_brasilia}\n"
    texto1 += f"\n{mandante}: ![]({escudo1})\n{visitante}: ![]({escudo2})"

    ult1 = await buscar_ultimos_jogos(jogo["teams"]["home"]["id"])
    ult2 = await buscar_ultimos_jogos(jogo["teams"]["away"]["id"])

    texto2 = f"📈 Últimos jogos de {mandante}:
" + "
".join(ult1) + f"

📈 Últimos jogos de {visitante}:
" + "
".join(ult2)

    gols1, esc1, am1, vm1 = await buscar_estatisticas(jogo["teams"]["home"]["id"])
    gols2, esc2, am2, vm2 = await buscar_estatisticas(jogo["teams"]["away"]["id"])

    texto3 = f"📊 Estatísticas médias:
- {mandante}: Gols: {gols1} | Escanteios: {esc1} | CA: {am1} | CV: {vm1}
- {visitante}: Gols: {gols2} | Escanteios: {esc2} | CA: {am2} | CV: {vm2}"

    mercados = "🎯 Sugestões de mercado:
- Over 1.5 gols
- Ambas marcam: Sim
- Escanteios acima de 9.5"

    await update.message.reply_text(texto1)
    await update.message.reply_text(texto2)
    await update.message.reply_text(texto3)
    await update.message.reply_text(mercados)

async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder))
    print("Bot com API v3 rodando...")
    await app.run_polling()

if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
