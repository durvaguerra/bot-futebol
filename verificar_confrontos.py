import requests
from datetime import datetime

API_KEY = "bf3c7810eb457a741586bce8885be575"
BASE_URL = "https://v3.football.api-sports.io"
HEADERS = {"x-apisports-key": API_KEY}

def buscar_id_time(nome_time):
    url = f"{BASE_URL}/teams"
    params = {"search": nome_time}
    r = requests.get(url, headers=HEADERS, params=params)
    data = r.json()
    for team in data.get("response", []):
        if team["team"]["name"].lower().startswith(nome_time.lower()):
            return team["team"]["id"]
    return None

def buscar_confrontos(id1, id2):
    url = f"{BASE_URL}/fixtures/headtohead"
    params = {
        "h2h": f"{id1}-{id2}"
    }
    r = requests.get(url, headers=HEADERS, params=params)
    return r.json().get("response", [])

# ==== TESTE ====
time1 = "Flamengo"
time2 = "Palmeiras"

id1 = buscar_id_time(time1)
id2 = buscar_id_time(time2)

if not id1 or not id2:
    print("ID de time não encontrado.")
else:
    jogos = buscar_confrontos(id1, id2)
    if not jogos:
        print("Nenhum confronto encontrado.")
    else:
        print(f"{len(jogos)} confrontos entre {time1} e {time2}:")
        for j in jogos:
            data = j["fixture"]["date"][:10]
            home = j["teams"]["home"]["name"]
            away = j["teams"]["away"]["name"]
            liga = j["league"]["name"]
            status = j["fixture"]["status"]["short"]
            print(f"{data} - {home} x {away} ({liga}) - Status: {status}")