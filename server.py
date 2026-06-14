from flask import Flask, jsonify, request, send_from_directory
from datetime import datetime
import os

app = Flask(__name__)

# Laikas sekundėmis po kurio elektrinė laikoma offline
OFFLINE_RIBA_SEK = 30

nustatymai = {
    1: {
        "id": 1,
        "name": "Elektrine 1",
        "vietove": "Valmantiskiai",
        "jautrumas": 50,
        "uzdelsimasSek": 1,
        "infoRinkimasMin": 1,
        "maxVejas": 15,
        "stabdo": True,
        "rankinis": False,
        "kampas": 0,
        "rytaiKorekcija": 10
    },
    2: {
        "id": 2,
        "name": "Elektrine 2",
        "vietove": "Eugenijaus",
        "jautrumas": 50,
        "uzdelsimasSek": 1,
        "infoRinkimasMin": 1,
        "maxVejas": 20,
        "stabdo": True,
        "rankinis": False,
        "kampas": 0,
        "rytaiKorekcija": 10
    },
    3: {
        "id": 3,
        "name": "Elektrine 3",
        "vietove": "Sadausko",
        "jautrumas": 50,
        "uzdelsimasSek": 1,
        "infoRinkimasMin": 1,
        "maxVejas": 18,
        "stabdo": True,
        "rankinis": False,
        "kampas": 0,
        "rytaiKorekcija": 10
    }
}

busena = {
    1: {"galia": 0, "temp": 0, "hum": 0, "apkrova": 0, "paskCartasOnline": None, "status": "standby"},
    2: {"galia": 0, "temp": 0, "hum": 0, "apkrova": 0, "paskCartasOnline": None, "status": "standby"},
    3: {"galia": 0, "temp": 0, "hum": 0, "apkrova": 0, "paskCartasOnline": None, "status": "standby"},
}

def log(tekstas):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {tekstas}")

def patikrinti_statusa(nr):
    """Patikrina ar elektrinė online pagal paskutinį prisijungimą"""
    b = busena[nr]
    if b["paskCartasOnline"] is None:
        b["status"] = "standby"
        return
    sekundes = (datetime.now() - b["paskCartasOnline"]).total_seconds()
    b["status"] = "online" if sekundes < OFFLINE_RIBA_SEK else "standby"

@app.route("/")
def index():
    if os.path.exists("index.html"):
        return send_from_directory(".", "index.html")
    return "<h2>Serveris veikia!</h2>"

@app.route("/api/settings", methods=["GET"])
def gauti_visus():
    # Prieš grąžinant atnaujinti statusus
    for nr in busena:
        patikrinti_statusa(nr)
    # Sujungti nustatymus su statusu
    rezultatas = []
    for nr, nus in nustatymai.items():
        elem = dict(nus)
        elem["status"] = busena[nr]["status"]
        rezultatas.append(elem)
    return jsonify(rezultatas)

@app.route("/api/settings/<int:nr>", methods=["GET"])
def gauti_viena(nr):
    if nr not in nustatymai:
        return jsonify({"klaida": "Elektrine nerasta"}), 404
    patikrinti_statusa(nr)
    log(f"GET /api/settings/{nr} — {nustatymai[nr]['vietove']}")
    elem = dict(nustatymai[nr])
    elem["status"] = busena[nr]["status"]
    return jsonify(elem)

@app.route("/api/settings/<int:nr>", methods=["POST"])
def atnaujinti(nr):
    if nr not in nustatymai:
        return jsonify({"klaida": "Elektrine nerasta"}), 404
    duomenys = request.get_json()
    if not duomenys:
        return jsonify({"klaida": "Nera duomenu"}), 400
    leistini = [
        "jautrumas", "uzdelsimasSek", "infoRinkimasMin",
        "maxVejas", "stabdo", "rankinis", "kampas", "rytaiKorekcija"
    ]
    for laukas in leistini:
        if laukas in duomenys:
            nustatymai[nr][laukas] = duomenys[laukas]
    log(f"POST /api/settings/{nr} — {duomenys}")
    return jsonify({"ok": True, "nustatymai": nustatymai[nr]})

@app.route("/api/status/<int:nr>", methods=["POST"])
def gauti_busena(nr):
    if nr not in busena:
        return jsonify({"klaida": "Elektrine nerasta"}), 404
    duomenys = request.get_json() or {}
    busena[nr].update(duomenys)
    busena[nr]["paskCartasOnline"] = datetime.now()
    patikrinti_statusa(nr)
    log(f"PING {nr} — {nustatymai[nr]['vietove']} — {busena[nr]['status']}")
    return jsonify({"ok": True})

@app.route("/api/status", methods=["GET"])
def visu_busena():
    for nr in busena:
        patikrinti_statusa(nr)
    # Grąžinti be datetime objekto
    rezultatas = {}
    for nr, b in busena.items():
        elem = dict(b)
        elem["paskCartasOnline"] = b["paskCartasOnline"].strftime("%H:%M:%S") if b["paskCartasOnline"] else None
        rezultatas[nr] = elem
    return jsonify(rezultatas)

if __name__ == "__main__":
    print("=" * 45)
    print("  Elektriniu valdymo serveris")
    print("  http://localhost:5000")
    print(f"  Offline riba: {OFFLINE_RIBA_SEK} sek")
    print("=" * 45)
    app.run(host="0.0.0.0", port=5000, debug=False)