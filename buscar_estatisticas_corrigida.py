
def buscar_estatisticas(id_time, id_liga):
    url = f"https://api-football-v1.p.rapidapi.com/v3/teams/statistics?team={id_time}&league={id_liga}&season=2024"
    response = requests.get(url, headers=HEADERS).json().get("response", {})

    def safe_float(value):
        try:
            return round(float(value), 2)
        except (TypeError, ValueError):
            return "N/D"

    def somar_cartoes(tipo):
        total = 0
        for faixa in response.get("cards", {}).get(tipo, {}).values():
            if faixa and faixa.get("total") is not None:
                total += faixa["total"]
        return total if total > 0 else "N/D"

    gols = response.get("goals", {}).get("for", {})
    media_gols = safe_float((gols.get("home", 0) + gols.get("away", 0)) / 2)

    return {
        "gols": media_gols,
        "escanteios": "N/D",  # Não disponível no JSON atual
        "amarelos": somar_cartoes("yellow"),
        "vermelhos": somar_cartoes("red")
    }
