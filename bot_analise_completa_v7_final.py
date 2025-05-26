
import asyncio
import nest_asyncio
import logging
import requests
from datetime import datetime, timedelta
from rapidfuzz import process
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Configurações
BOT_TOKEN = "7803447059:AAFctdVYOdFjgBgo_umhxI-JOh90GWloqGk"
API_KEY = "3241e99e70msh46d8894245e36fcp11fa9bjsn53fda60e6ec4"
HEADERS = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
}
logging.getLogger("httpx").setLevel(logging.WARNING)

# Utilidade para dividir texto longo
def enviar_texto_em_partes(texto, update):
    partes = [texto[i:i+4000] for i in range(0, len(texto), 4000)]
    for parte in partes:
        update.message.reply_text(parte)

# Buscar ID do time com fuzzy match
def buscar_id_nome_time(nome_time):
    url = f"https://api-football-v1.p.rapidapi.com/v3/teams?search={nome_time}"
    response = requests.get(url, headers=HEADERS).json()
    nomes = [t["team"]["name"] for t in response["response"]]
    resultado = process.extractOne(nome_time, nomes, score_cutoff=60)
    if resultado is None:
        return None, None
    melhor, score, _ = resultado
    for t in response["response"]:
        if t["team"]["name"] == melhor:
            return t["team"]["id"], t["team"]["name"]
    return None, None

# Detectar temporada atual com base na competição e data
def detectar_temporada():
    hoje = datetime.now()
    if hoje.month >= 7:
        return hoje.year
    return hoje.year - 1

# Buscar confronto real entre dois times
def buscar_proximo_confronto(id1, id2):
    hoje = datetime.utcnow().date()
    datas = [(hoje + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, 20)]
    for data in datas:
        url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures?date={data}"
        jogos = requests.get(url, headers=HEADERS).json().get("response", [])
        for jogo in jogos:
            h = jogo["teams"]["home"]["id"]
            a = jogo["teams"]["away"]["id"]
            if sorted([h, a]) == sorted([id1, id2]):
                return jogo
    return None


# Análise emocional com base na posição na tabela
def analise_emocional(pos, nome):
    if pos is None:
        return f"- {nome}: Sem dados de classificação disponíveis."
    if pos <= 4:
        return f"- {nome}: Disputa pelo G4, alta motivação."
    elif pos <= 8:
        return f"- {nome}: Briga por G8, busca por estabilidade."
    elif pos >= 17:
        return f"- {nome}: Zona de rebaixamento, sob pressão."
    else:
        return f"- {nome}: Zona intermediária, busca por evolução."

# Estatísticas médias
def estatisticas_resumo(stats, nome_time):
    try:
        gols = stats["goals"]["for"]["average"]["total"]
        amarelos = stats["cards"]["yellow"]["average"]["total"]
        vermelhos = stats["cards"]["red"]["average"]["total"]
        cantos = stats["corners"]["total"]
    except:
        gols = amarelos = vermelhos = cantos = "N/D"

    return f"""📊 Estatísticas médias de {nome_time}:
- Gols por jogo: {gols}
- Escanteios por jogo: {cantos}
- Cartões amarelos: {amarelos}
- Cartões vermelhos: {vermelhos}
"""

# Últimos jogos
def formatar_ultimos_jogos(lista, nome):
    texto = f"📈 Últimos jogos de {nome}:"
    for jogo in lista:
        adversario = jogo["teams"]["home"]["name"] if not jogo["teams"]["home"]["name"] == nome else jogo["teams"]["away"]["name"]
        placar = f"{jogo['goals']['home']}x{jogo['goals']['away']}"
        data = jogo["fixture"]["date"][:10]
        local = "Casa" if jogo["teams"]["home"]["name"] == nome else "Fora"
        texto += f"{data} - {local} vs {adversario} ({placar})"
    return texto

# Sugestões de mercado (simplificadas)
def sugerir_mercados(gols, cantos):
    mercados = []
    if gols and gols != "N/D":
        if float(gols) >= 1.5:
            mercados.append("Over 1.5 gols")
        if float(gols) >= 2.5:
            mercados.append("Over 2.5 gols")
    if cantos and cantos != "N/D":
        if float(cantos) >= 8:
            mercados.append("Over 8.5 escanteios")
        if float(cantos) >= 10:
            mercados.append("Over 9.5 escanteios")
    if mercados:
        return "🎯 Sugestões de mercado:
- " + "
- ".join(mercados)
    return "🎯 Nenhuma sugestão clara de mercado com base nos dados disponíveis."


# Função principal de análise
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    if " x " not in texto.lower():
        await update.message.reply_text("Envie no formato: Time1 x Time2")
        return

    time1, time2 = map(str.strip, texto.lower().split(" x "))
    id1, nome1 = buscar_id_nome_time(time1)
    id2, nome2 = buscar_id_nome_time(time2)

    if not id1 or not id2:
        await update.message.reply_text("Não encontrei um dos times.")
        return

    jogo = buscar_proximo_confronto(id1, id2)
    if not jogo:
        await update.message.reply_text("Não encontrei confronto futuro entre esses times.")
        return

    mandante = jogo["teams"]["home"]["name"]
    visitante = jogo["teams"]["away"]["name"]
    campeonato = jogo["league"]["name"]
    data = jogo["fixture"]["date"][:10]
    id_liga = jogo["league"]["id"]

    temporada = detectar_temporada()

    # Estatísticas e últimos jogos
    stats1 = requests.get(f"https://api-football-v1.p.rapidapi.com/v3/teams/statistics?team={id1}&league={id_liga}&season={temporada}", headers=HEADERS).json().get("response", {})
    stats2 = requests.get(f"https://api-football-v1.p.rapidapi.com/v3/teams/statistics?team={id2}&league={id_liga}&season={temporada}", headers=HEADERS).json().get("response", {})

    ultimos1 = stats1.get("fixtures", {}).get("last", {}).get("fixtures", [])
    ultimos2 = stats2.get("fixtures", {}).get("last", {}).get("fixtures", [])

    gols1 = stats1.get("goals", {}).get("for", {}).get("average", {}).get("total", "N/D")
    cantos1 = stats1.get("corners", {}).get("total", "N/D")

    # Classificação
    tabela = requests.get(f"https://api-football-v1.p.rapidapi.com/v3/standings?league={id_liga}&season={temporada}", headers=HEADERS).json()
    pos1 = pos2 = None
    for grupo in tabela.get("response", []):
        for team in grupo["league"]["standings"][0]:
            if team["team"]["id"] == id1:
                pos1 = team["rank"]
            if team["team"]["id"] == id2:
                pos2 = team["rank"]

    texto = f"""📆 Próximo jogo entre {mandante} (mandante) e {visitante} (visitante)
🏆 {campeonato}
📍 Data: {data}

🧠 Cenário emocional:
{analise_emocional(pos1, nome1)}
{analise_emocional(pos2, nome2)}

{estatisticas_resumo(stats1, nome1)}
{estatisticas_resumo(stats2, nome2)}

{formatar_ultimos_jogos(stats1.get("fixtures", {}).get("last", {}).get("fixtures", [])[:5], nome1)}

{formatar_ultimos_jogos(stats2.get("fixtures", {}).get("last", {}).get("fixtures", [])[:5], nome2)}

{sugerir_mercados(gols1, cantos1)}
"""

    enviar_texto_em_partes(texto, update)

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Olá! Envie dois times no formato:
flamengo x vasco")

# Main
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("Bot com análise tática completa rodando.")
    await app.run_polling()

if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())

    import requests
    import datetime

    # Substitua pela sua chave
    RAPIDAPI_KEY = "SUA_CHAVE_RAPIDAPI"

    headers = {
        "X-RapidAPI-Key": RAPIDAPI_KEY,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }

    async def buscar_proximo_confronto(nome_time1, nome_time2):
        url_id = "https://api-football-v1.p.rapidapi.com/v3/teams"

        # Buscar ID do time 1
        response1 = requests.get(url_id, headers=headers, params={"search": nome_time1})
        data1 = response1.json()
        if "response" not in data1 or not data1["response"]:
            print(f"[ERRO] Time '{nome_time1}' não encontrado na API.")
            return None
        id1 = data1["response"][0]["team"]["id"]

        # Buscar ID do time 2
        response2 = requests.get(url_id, headers=headers, params={"search": nome_time2})
        data2 = response2.json()
        if "response" not in data2 or not data2["response"]:
            print(f"[ERRO] Time '{nome_time2}' não encontrado na API.")
            return None
        id2 = data2["response"][0]["team"]["id"]

        # Buscar confrontos diretos
        url_h2h = "https://api-football-v1.p.rapidapi.com/v3/fixtures/headtohead"
        response = requests.get(url_h2h, headers=headers, params={
            "h2h": f"{id1}-{id2}",
            "season": "2024"  # Temporada atual ainda é 2024
        })
        data = response.json()
        print("== RESPOSTA HEAD2HEAD ==")
        print(data)

        if "response" not in data or not data["response"]:
            print("[ERRO] Nenhum confronto encontrado.")
            return None

        agora = datetime.datetime.utcnow().timestamp()
        proximos = [
            jogo for jogo in data["response"]
            if jogo["fixture"]["timestamp"] > agora
        ]

        if not proximos:
            print("[INFO] Nenhum confronto futuro encontrado.")
            return None

        # Ordenar por data mais próxima
        proximos.sort(key=lambda x: x["fixture"]["timestamp"])
        return proximos[0]