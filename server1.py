from flask import Flask, jsonify, request, send_from_directory
from datetime import datetime
import os
 
app = Flask(__name__)
 
OFFLINE_RIBA_SEK = 30
 
nustatymai = {
    1: {
        "id": 1, "name": "Elektrine 1", "vietove": "Valmantiskiai",
        "sukimoStartSkirtumas": 12, "sukimoStopPaklaida": 10,
        "uzdelsimasSek": 1, "infoRinkimasMin": 1,
        "rytaiKorekcija": 10, "vakaraiKorekcija": 0,
        "maxVejas": 15, "stabdo": True, "rankinis": False, "kampas": 0,
    },
    2: {
        "id": 2, "name": "Elektrine 2", "vietove": "Eugenijaus",
        "sukimoStartSkirtumas": 12, "sukimoStopPaklaida": 10,
        "uzdelsimasSek": 1, "infoRinkimasMin": 1,
        "rytaiKorekcija": 10, "vakaraiKorekcija": 0,
        "maxVejas": 20, "stabdo": True, "rankinis": False, "kampas": 0,
    },
    3: {
        "id": 3, "name": "Elektrine 3", "vietove": "Sadausko",
        "sukimoStartSkirtumas": 12, "sukimoStopPaklaida": 10,
        "uzdelsimasSek": 1, "infoRinkimasMin": 1,
        "rytaiKorekcija": 10, "vakaraiKorekcija": 0,
        "maxVejas": 18, "stabdo": True, "rankinis": False, "kampas": 0,
    }
}
 
busena = {
    1: {"galia": 0, "temp": 0, "hum": 0, "apkrova": 0, "paskCartasOnline": None, "status": "standby"},
    2: {"galia": 0, "temp": 0, "hum": 0, "apkrova": 0, "paskCartasOnline": None, "status": "standby"},
    3: {"galia": 0, "temp": 0, "hum": 0, "apkrova": 0, "paskCartasOnline": None, "status": "standby"},
}
 
oro_stotelė = {
    "status": "standby",
    "temp": 0, "hum": 0, "vejas": 0,
    "paskCartasOnline": None
}
 
def log(t):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {t}")
 
def patikrinti_statusa(nr):
    b = busena[nr]
    if b["paskCartasOnline"] is None:
        b["status"] = "standby"; return
    sek = (datetime.now() - b["paskCartasOnline"]).total_seconds()
    b["status"] = "online" if sek < OFFLINE_RIBA_SEK else "standby"
 
def patikrinti_oro_statusa():
    if oro_stotelė["paskCartasOnline"] is None:
        oro_stotelė["status"] = "standby"; return
    sek = (datetime.now() - oro_stotelė["paskCartasOnline"]).total_seconds()
    oro_stotelė["status"] = "online" if sek < OFFLINE_RIBA_SEK else "standby"
 
@app.route("/")
def index():
    if os.path.exists("index.html"):
        return send_from_directory(".", "index.html")
    return "<h2>Serveris veikia!</h2>"
 
@app.route("/api/settings", methods=["GET"])
def gauti_visus():
    for nr in busena: patikrinti_statusa(nr)
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
        "sukimoStartSkirtumas", "sukimoStopPaklaida",
        "uzdelsimasSek", "infoRinkimasMin",
        "rytaiKorekcija", "vakaraiKorekcija",
        "maxVejas", "stabdo", "rankinis", "kampas"
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
    busena[nr].update({k: duomenys[k] for k in ["galia","temp","hum","apkrova"] if k in duomenys})
    busena[nr]["paskCartasOnline"] = datetime.now()
    patikrinti_statusa(nr)
    log(f"PING {nr} — {nustatymai[nr]['vietove']} — {busena[nr]['status']}")
    return jsonify({"ok": True})
 
@app.route("/api/status", methods=["GET"])
def visu_busena():
    for nr in busena: patikrinti_statusa(nr)
    rezultatas = {}
    for nr, b in busena.items():
        elem = dict(b)
        elem["paskCartasOnline"] = b["paskCartasOnline"].strftime("%H:%M:%S") if b["paskCartasOnline"] else None
        rezultatas[nr] = elem
    return jsonify(rezultatas)
 
@app.route("/api/oro-stotelė", methods=["GET"])
@app.route("/api/weather", methods=["GET"])
def gauti_oro():
    patikrinti_oro_statusa()
    elem = dict(oro_stotelė)
    elem["paskCartasOnline"] = oro_stotelė["paskCartasOnline"].strftime("%H:%M:%S") if oro_stotelė["paskCartasOnline"] else None
    return jsonify(elem)
 
@app.route("/api/oro-stotelė", methods=["POST"])
@app.route("/api/weather", methods=["POST"])
def atnaujinti_oro():
    duomenys = request.get_json() or {}
    for k in ["temp", "hum", "vejas"]:
        if k in duomenys:
            oro_stotelė[k] = duomenys[k]
    oro_stotelė["paskCartasOnline"] = datetime.now()
    patikrinti_oro_statusa()
    log(f"ORO STOTELĖ <- temp:{oro_stotelė['temp']} hum:{oro_stotelė['hum']} vejas:{oro_stotelė['vejas']}")
    return jsonify({"ok": True})
 
if __name__ == "__main__":
    print("=" * 50)
    print("  Elektriniu valdymo serveris v3.2")
    print("  http://localhost:5000")
    print(f"  Offline riba: {OFFLINE_RIBA_SEK} sek")
    print("  Endpointai:")
    print("    GET/POST /api/settings/<nr>")
    print("    GET/POST /api/status/<nr>")
    print("    GET/POST /api/oro-stotelė  (UI)")
    print("    GET/POST /api/weather       (ESP32)")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=False)