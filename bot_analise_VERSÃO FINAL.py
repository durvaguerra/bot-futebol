import asyncio
import requests
from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from rapidfuzz import process
from dateutil import parser
import json
import difflib
import traceback
git
BOT_TOKEN = "7803447059:AAFctdVYOdFjgBgo_umhxI-JOh90GWloqGk"
url_base = "https://api-football-v1.p.rapidapi.com/v3"

headers = {
    "X-RapidAPI-Key": "3241e99e70msh46d8894245e36fcp11fa9bjsn53fda60e6ec4",
    "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
}

LISTA_DE_TIMES = [
    # Série A (Brasil)
    "flamengo", "palmeiras", "gremio", "atletico mineiro", "bahia", "sao paulo", "bragantino", "botafogo", "cruzeiro",
    "internacional", "fortaleza", "athletico paranaense", "cuiaba", "corinthians", "vitoria", "juventude", "atletico goianiense", "vasco", "ec bahia", "americamineiro",

    # Série B (Brasil)
    "avai", "chapecoense", "ceara", "goias", "ponte preta", "mirassol", "ituano", "novorizontino", "vila nova", "sport recife", "guarani", "sampaio correa", "londrina", "tombense","coritiba","criciuma",

    # La Liga (Espanha)
    "real madrid", "barcelona", "atletico madrid", "sevilla", "real sociedad", "athletic bilbao","athletic club", "valencia", "villarreal", "real betis", "getafe", "granada", "osasuna", "alaves", "rayo vallecano", "mallorca", "cadiz", "celta vigo", "las palmas",

    # Serie A (Itália)
    "internazionale", "ac milan", "juventus", "roma", "napoli", "lazio", "atalanta", "fiorentina", "bologna", "torino", "udinese", "lecce", "cagliari", "sassuolo", "empoli", "genoa", "verona", "salernitana",

    # Bundesliga (Alemanha)
    "bayern munich", "borussia dortmund", "leipzig", "bayer leverkusen", "eintracht frankfurt", "wolfsburg", "mainz", "union berlin", "freiburg", "augsburg", "hoffenheim", "stuttgart", "bochum", "koln", "werder bremen", "darmstadt", "heidenheim",

    # Ligue 1 (França)
    "paris saint germain","paris saint germain", "psg", "monaco", "lyon", "marseille", "lille", "nice", "rennes", "montpellier", "nantes", "toulouse", "strasbourg", "reims", "lens", "metz", "clermont", "le havre",

    # Premier League (Inglaterra)
    "manchester city", "arsenal", "liverpool", "manchester united", "chelsea", "tottenham", "aston villa", "newcastle", "west ham", "brighton", "crystal palace", "wolves", "brentford", "fulham", "everton", "bournemouth", "nottingham forest", "burnley", "luton", "sheffield united",

    # MLS (EUA)
    "inter miami", "la galaxy", "new york city", "atlanta united", "los angeles fc", "seattle sounders", "chicago fire", "columbus crew", "houston dynamo", "orlando city", "dc united", "toronto fc",

    # Argentina
    "boca juniors", "river plate", "racing", "independiente", "san lorenzo", "rosario central", "newell's old boys", "argentinos juniors", "estudiantes", "huracan",

    # Uruguai
    "penarol", "nacional", "defensor sporting", "liverpool montevideo", "cerro largo", "danubio",

    # Colômbia
    "atletico nacional", "deportivo cali", "america de cali", "independiente medellin", "santa fe", "junior barranquilla", "millionarios",

    # Arábia Saudita
    "al hilal", "al nassr", "al ittihad", "al ahli", "al fateh", "al ettifaq", "al qadsiah",
]

def normalizar_nome_time(nome, lista_de_times):
    nome = nome.lower().strip()
    melhor_match = difflib.get_close_matches(nome, lista_de_times, n=1, cutoff=0.6)
    if melhor_match:
        return melhor_match[0]
    return nome

def parse_float(valor):
    try:
        return round(float(valor), 2)
    except (ValueError, TypeError):
        return "N/D"


def normalizar_nome_time(nome_digitado: str, lista_de_times: list) -> str:
    nome = nome_digitado.lower()
    correspondencias = difflib.get_close_matches(nome, lista_de_times, n=1, cutoff=0.6)
    return correspondencias[0] if correspondencias else nome

APELIDOS_TIMES = {
    "galo": "atletico mineiro",
    "atletico-mg": "atletico mineiro",
    "sao paulo": "sao paulo",
    "spfc": "sao paulo",
    "mirassol": "mirassol",
    "palmeiras": "palmeiras",
    "verdao": "palmeiras",
    "corinthians": "corinthians",
    "timão": "corinthians",
    "ferroviaria": "ferroviaria",
    "goias": "goias",
"galo": "atlético-mg",
"atletico mineiro": "atlético-mg",
"atletico mg": "atlético-mg",
"atlético mineiro": "atlético-mg",
"atlético mg": "atlético-mg",
    "spfc": "sao paulo",
    "tricolor paulista": "sao paulo",
    "mengao": "flamengo",
    "mengão": "flamengo",
    "fla": "flamengo",
    "timao": "corinthians",
    "timão": "corinthians",
    "verdao": "palmeiras",
    "verdão": "palmeiras",
    "palmeira": "palmeiras",
    "goias": "goias",
    "goiás": "goias",
    "goiás": "goias",
    "são paulo": "sao paulo",
    "gremio": "gremio",
    "grêmio": "gremio",
    "flamengo": "flamengo",
    "mengao": "flamengo",
    "mengão": "flamengo",
    "paris saint germain": "paris saint germain",
    "psg": "paris saint germain",
    "psg": "Paris Saint Germain",
    "athletic bilbao": "athletic club",
    "athletic": "athletic club",
    "bilbao": "athletic club",
    "athletic bilbao": "athletic club",
    "real sociedad": "real sociedad",
    "psg": "paris saint germain",
    "man united": "manchester united",
    "man city": "manchester city",
}


# adicione outros apelidos aqui conforme necessário

def obter_temporada_atual(league_id, country="Brazil"):
    url = f"https://api-football-v1.p.rapidapi.com/v3/leagues"
    params = {"id": league_id, "country": country}
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    try:
        for temporada in reversed(data["response"][0]["seasons"]):
            if temporada.get("current"):
                return temporada["year"]
        return data["response"][0]["seasons"][-1]["year"]
    except (KeyError, IndexError):
        return 2024  # fallback

async def enviar_texto_em_partes(texto, update):
    partes = [texto[i:i+4000] for i in range(0, len(texto), 4000)]
    for parte in partes:
        await update.message.reply_text(parte)


def buscar_id_nome_time(nome_time):
    url = f"https://api-football-v1.p.rapidapi.com/v3/teams?search={nome_time}"
    response = requests.get(url, headers=headers).json()

    nomes = [t["team"]["name"] for t in response.get("response", [])]

    # Verifica se é uma lista válida de strings
    nomes = [n for n in nomes if isinstance(n, str)]
    print(f"Nomes extraídos para comparação: {nomes}")

    if not nomes:
        return None, None

    resultado = process.extractOne(nome_time, nomes, score_cutoff=60)
    if not resultado:
        return None, None

    melhor, _, _ = resultado
    for t in response["response"]:
        if t["team"]["name"] == melhor:
            return t["team"]["id"], t["team"]["name"]

    return None, None

def buscar_confronto_em_agenda(id1, id2):
    import requests
    from datetime import datetime
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    headers = {
        "X-RapidAPI-Key": "3241e99e70msh46d8894245e36fcp11fa9bjsn53fda60e6ec4",  # Substitua pela sua variável
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }

    agora = datetime.now(timezone.utc).timestamp()

    try:
        # Buscar próximos jogos do time 1
        response1 = requests.get(url, headers=headers, params={"team": id1, "next": 10})
        jogos1 = response1.json().get("response", [])

        for jogo in jogos1:
            id_home = jogo["teams"]["home"]["id"]
            id_away = jogo["teams"]["away"]["id"]
            timestamp = jogo["fixture"]["timestamp"]

            if (id_home == id1 and id_away == id2) or (id_home == id2 and id_away == id1):
                if timestamp > agora:
                    return jogo

        print("[ERRO] Nenhum confronto futuro encontrado na agenda dos times.")
        return None

    except Exception as e:
        print(f"[ERRO] na verificação de agenda de jogos: {e}")
        return None

async def buscar_proximo_confronto(id_time1, id_time2):
    if not id_time1 or not id_time2:
        print("[ERRO] IDs dos times são inválidos.")
        return None

    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures/headtohead"
    params = {
        "h2h": f"{id_time1}-{id_time2}"
    }

    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    print("== RESPOSTA HEAD2HEAD ==")
    print(json.dumps(data, indent=2, ensure_ascii=False))

    jogos = data.get("response", [])
    if not jogos:
        print("[ERRO] Nenhum confronto encontrado.")
        return None

    agora = datetime.now(timezone.utc).timestamp()
    futuros = [j for j in jogos if j["fixture"]["timestamp"] > agora]
    if not futuros:
        print("[ERRO] Nenhum confronto futuro encontrado.")
        return None

    proximo_jogo = sorted(futuros, key=lambda x: x["fixture"]["timestamp"])[0]

    return {
        "mandante": proximo_jogo["teams"]["home"]["name"],
        "visitante": proximo_jogo["teams"]["away"]["name"],
        "id_mandante": proximo_jogo["teams"]["home"]["id"],
        "id_visitante": proximo_jogo["teams"]["away"]["id"],
        "liga_id": proximo_jogo["league"]["id"],
        "temporada": proximo_jogo["league"]["season"],
        "data": proximo_jogo["fixture"]["date"][:10],
        "hora": proximo_jogo["fixture"]["date"][11:16],
        "nome_liga": proximo_jogo["league"]["name"]
    }
def buscar_proximo_confronto_seguro(id1, id2):
    import requests
    from datetime import datetime

    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures/headtohead"
    headers = {
        "X-RapidAPI-Key": "3241e99e70msh46d8894245e36fcp11fa9bjsn53fda60e6ec4",  # Substitua pela sua variável ou string
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }
    params = {
        "h2h": f"{id1}-{id2}"
    }

    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        confrontos = data.get("response", [])
        agora = datetime.utcnow().timestamp()

        # Filtra apenas os jogos futuros
        jogos_futuros = [j for j in confrontos if j["fixture"]["timestamp"] > agora]

        if not jogos_futuros:
            print("[ERRO] Nenhum confronto futuro encontrado.")
            return None

        # Ordena e retorna o mais próximo
        proximo = sorted(jogos_futuros, key=lambda x: x["fixture"]["timestamp"])[0]
        return proximo

    except Exception as e:
        print(f"[ERRO] ao buscar confronto futuro: {e}")
        return None

def encontrar_proximo_jogo(confrontos):
    agora = datetime.now(timezone.utc).timestamp()

    proximos = [j for j in confrontos if j.get("fixture", {}).get("timestamp", 0) > agora]

    if not proximos:
        return None

    proximos_ordenados = sorted(proximos, key=lambda x: x["fixture"]["timestamp"])
    return proximos_ordenados[0]

def buscar_posicao_time(id_liga, id_time):
    url = f"https://api-football-v1.p.rapidapi.com/v3/standings?league={id_liga}&season={temporada}"
    response = requests.get(url, headers=headers).json()
    for grupo in response.get("response", []):
        for time in grupo.get("league", {}).get("standings", [[]])[0]:
            if time.get("team", {}).get("id") == id_time:
                return time.get("rank")
    return None


def buscar_estatisticas(id_time, id_liga, temporada):
    url = "https://api-football-v1.p.rapidapi.com/v3/teams/statistics"
    params = {"team": id_time, "league": id_liga, "season": temporada}
    response = requests.get(url, headers=headers, params=params).json()

    raw = response.get("response", {})
    goals = raw.get("goals", {}).get("for", {}).get("average", {}).get("total")
    corners = raw.get("corners", {}).get("total") or raw.get("corners", {}).get("average", {}).get("total")

    amarelos = raw.get("cards", {}).get("yellow", {})
    vermelhos = raw.get("cards", {}).get("red", {})

    def media_cartoes(dic):
        totais = [x.get("total", 0) for x in dic.values() if isinstance(x, dict) and x.get("total") is not None]
        return round(sum(totais) / len(totais), 2) if totais else None

    stats = {
        "gols": float(goals) if goals else None,
        "escanteios": float(corners) if corners else None,
        "ama": media_cartoes(amarelos),
        "ver": media_cartoes(vermelhos)
    }

    return stats

async def buscar_ultimos_jogos(id_time, temporada):
    url = f"https://api-football-v1.p.rapidapi.com/v3/fixtures"
    params = {
        "team": id_time,
        "season": temporada,
        "status": "FT",
        "last": 5
    }
    headers = {
        "X-RapidAPI-Key": "3241e99e70msh46d8894245e36fcp11fa9bjsn53fda60e6ec4"
    }

    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    jogos = []

    for item in data.get("response", []):
        fixture = item.get("fixture", {})
        teams = item.get("teams", {})
        goals = item.get("goals", {})
        jogo = {
            "data": fixture.get("date", "")[:10],
            "casa": teams.get("home", {}).get("name", "N/D"),
            "fora": teams.get("away", {}).get("name", "N/D"),
            "gols_casa": goals.get("home", "N/D"),
            "gols_fora": goals.get("away", "N/D")
        }
        jogos.append(jogo)

    return jogos
""

def gerar_texto_stats(nome, stats, ultimos):
    def formatar(valor, sufixo=""):
        return f"{valor}{sufixo}" if valor is not None else "N/D"

    texto = f"\n📈 Últimos jogos de {nome}:\n"
    if isinstance(ultimos, list) and ultimos:
        for jogo in ultimos:
            data = jogo.get("data", "N/D")
            casa = jogo.get("casa", "N/D")
            fora = jogo.get("fora", "N/D")
            gols_casa = jogo.get("gols_casa", "N/D")
            gols_fora = jogo.get("gols_fora", "N/D")
            texto += f"{data}: {casa} {gols_casa}x{gols_fora} {fora}\n"
    else:
        texto += "Sem dados dos últimos jogos.\n"

    texto += "\n📊 Estatísticas médias:\n"
    texto += f"- Gols por jogo: {formatar(stats.get('gols'))}\n"
    texto += f"- Escanteios por jogo: {formatar(stats.get('escanteios'))}\n"
    texto += f"- Cartões amarelos (média): {formatar(stats.get('ama'))}\n"
    texto += f"- Cartões vermelhos (média): {formatar(stats.get('ver'))}\n"

    return texto

def contexto_emocional(pos):
    if not pos:
        return "Sem dados disponíveis."
    if pos <= 4:
        return "Disputa por G4."
    elif pos >= 17:
        return "Luta contra o rebaixamento."
    else:
        return "Zona intermediária."

def sugerir_mercados(stats1, stats2):
    mercados = []

    # Sugestões com base em gols
    if isinstance(stats1.get("gols"), (int, float)) and isinstance(stats2.get("gols"), (int, float)):
        media_gols = (stats1["gols"] + stats2["gols"]) / 2
        if media_gols >= 3:
            mercados.append("Over 2.5 gols")
        elif media_gols >= 2.5:
            mercados.append("Mais de 2 gols pode ser interessante")
        elif media_gols >= 2:
            mercados.append("Ambas marcam pode ser uma boa opção")
        else:
            mercados.append("Tendência de jogo com poucos gols (Under 2.5)")

    # Sugestões com base em escanteios
    if isinstance(stats1.get("escanteios"), (int, float)) and isinstance(stats2.get("escanteios"), (int, float)):
        media_escanteios = (stats1["escanteios"] + stats2["escanteios"]) / 2
        if media_escanteios >= 9:
            mercados.append("Mais de 8.5 escanteios no jogo")
        elif media_escanteios >= 7:
            mercados.append("Escanteios no jogo podem passar de 6.5")
        else:
            mercados.append("Baixa média de escanteios")

    # Sugestões com base em cartões amarelos
    if isinstance(stats1.get("ama"), (int, float)) and isinstance(stats2.get("ama"), (int, float)):
        media_ama = (stats1["ama"] + stats2["ama"]) / 2
        if media_ama >= 4:
            mercados.append("Jogo com alta tendência de cartões amarelos (Over 3.5)")
        elif media_ama >= 3:
            mercados.append("Mais de 2.5 cartões amarelos é provável")

    return mercados

async def analisar_cenario_emocional(id_time, id_liga, temporada, headers):
    try:
        url = "https://api-football-v1.p.rapidapi.com/v3/standings"
        params = {"league": id_liga, "season": temporada}
        response = requests.get(url, headers=headers, params=params).json()

        # Verificação robusta
        if (
            not response.get("response") or
            "league" not in response["response"][0] or
            "standings" not in response["response"][0]["league"]
        ):
            return "Sem dados disponíveis."

        tabela = response["response"][0]["league"]["standings"][0]

        for time in tabela:
            if time["team"]["id"] == id_time:
                posicao = time["rank"]
                total = len(tabela)
                if posicao <= 4:
                    return "Disputa por G4."
                elif posicao >= total - 3:
                    return "Luta contra o rebaixamento."
                else:
                    return "Busca por estabilidade no meio da tabela."

        return "Time não encontrado na classificação."

    except Exception as e:
        print("Erro ao analisar cenário emocional:", e)
        return "Erro na análise."

async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        mensagem = update.message.text
        times = mensagem.split("x")

        if len(times) != 2:
            await update.message.reply_text("Por favor, envie a mensagem no formato: Time1 x Time2")
            return

        nome_time1 = times[0].strip()
        nome_time2 = times[1].strip()

        nome_time1 = normalizar_nome_time(nome_time1, LISTA_DE_TIMES)
        nome_time2 = normalizar_nome_time(nome_time2, LISTA_DE_TIMES)

        print(f"Nome normalizado 1: {nome_time1}")
        print(f"Nome normalizado 2: {nome_time2}")

        id1, nome1 = buscar_id_nome_time(nome_time1)
        id2, nome2 = buscar_id_nome_time(nome_time2)

        print(f"ID do time 1 ({nome_time1}): {id1} - Nome completo: {nome1}")
        print(f"ID do time 2 ({nome_time2}): {id2} - Nome completo: {nome2}")
        if not id1 or not id2:
            print("[ERRO] Não foi possível encontrar os IDs dos times.")
            await update.message.reply_text("Não foi possível encontrar os times informados.")
            return

        # Tenta buscar confronto via método assíncrono
        confronto = await buscar_proximo_confronto(id1, id2)

        # Se falhar, tenta a versão segura (síncrona)
        if not confronto:
            confronto = buscar_proximo_confronto_seguro(id1, id2)

        # Se ainda assim não encontrar, tenta na agenda dos times
        if not confronto:
            confronto = buscar_confronto_em_agenda(id1, id2)

        if not confronto:
            await update.message.reply_text("Não foi possível encontrar um confronto futuro entre os times.")
            return

        # Extrair dados do confronto com base no dicionário personalizado retornado
        nome1 = confronto["mandante"]
        nome2 = confronto["visitante"]
        id1 = confronto["id_mandante"]
        id2 = confronto["id_visitante"]
        id_liga = confronto["liga_id"]
        temporada = confronto["temporada"]
        nome_liga = confronto["nome_liga"]
        data_jogo = confronto["data"]
        hora_jogo = confronto["hora"]

        texto_final = f"📆 Próximo jogo entre {nome1} (mandante) e {nome2} (visitante)"
        texto_final += f"\n🏆 {nome_liga}"
        texto_final += f"\n📍 Data: {data_jogo} às {hora_jogo}"

        # Cenário emocional
        emocional1 = await analisar_cenario_emocional(id1, id_liga, temporada, headers)
        emocional2 = await analisar_cenario_emocional(id2, id_liga, temporada, headers)
        texto_final += "\n\n🧠 Cenário emocional:"
        texto_final += f"\n- {nome1}: {emocional1}"
        texto_final += f"\n- {nome2}: {emocional2}"

        # Últimos jogos e estatísticas
        ult1 = await buscar_ultimos_jogos(id1, temporada)
        ult2 = await buscar_ultimos_jogos(id2, temporada)
        stats1 = buscar_estatisticas(id1, id_liga, temporada)
        stats2 = buscar_estatisticas(id2, id_liga, temporada)

        texto_final += "\n\n" + gerar_texto_stats(nome1, stats1, ult1)
        texto_final += "\n\n" + gerar_texto_stats(nome2, stats2, ult2)

        # Sugestões de mercado
        texto_final += "⚽ Sugestões de mercado:\n"

        gols_1 = stats1.get("gols")
        gols_2 = stats2.get("gols")
        escanteios_1 = stats1.get("escanteios")
        escanteios_2 = stats2.get("escanteios")

        # Verificar se é possível calcular a média de gols
        if isinstance(gols_1, (int, float)) and isinstance(gols_2, (int, float)):
            media_gols = (gols_1 + gols_2) / 2
        else:
            media_gols = None

        # Verificar se é possível calcular a média de escanteios
        if isinstance(escanteios_1, (int, float)) and isinstance(escanteios_2, (int, float)):
            media_escanteios = (escanteios_1 + escanteios_2) / 2
        else:
            media_escanteios = None

        # Sugestões simples com base nas médias
        sugestoes = []

        if media_gols:
            if media_gols >= 2.5:
                sugestoes.append("Mais de 2.5 gols na partida")
            elif media_gols >= 1.5:
                sugestoes.append("Mais de 1.5 gols na partida")

        if media_escanteios:
            if media_escanteios >= 9:
                sugestoes.append("Mais de 8.5 escanteios totais")
            elif media_escanteios >= 7:
                sugestoes.append("Mais de 6.5 escanteios totais")

        if sugestoes:
            for s in sugestoes:
                texto_final += f"- {s}\n"
        else:
            texto_final += "Sem sugestões com os dados disponíveis"

        await enviar_texto_em_partes(texto_final, update)

    except Exception as e:
        print("Erro ao processar mensagem:")

        traceback.print_exc()  # isso mostra a linha exata onde o erro ocorreu

        await update.message.reply_text("Ocorreu um erro ao processar sua solicitação.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bem-vindo! Envie dois times no formato: flamengo x vasco")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))
    print("Bot com análise tática completa rodando.")
    await app.run_polling()



if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()  # Permite reentrância no loop já existente

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())
    except Exception as e:
        print(f"Erro ao iniciar o bot: {e}")
