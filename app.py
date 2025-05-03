import time
import requests
from flask import Flask, jsonify, request
import datetime

app = Flask(__name__)
session = requests.Session()

def obtener_datos_yahoo(ticker, intervalo, rango, max_attempts=3):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    params = {"interval": intervalo, "range": rango}
    headers = {
        "User-Agent": "Mozilla/5.0 ..."
    }

    delay = 1.0  # segundos inicial
    for attempt in range(1, max_attempts + 1):
        try:
            resp = session.get(url, params=params, headers=headers, timeout=5)
            resp.raise_for_status()
            datos = resp.json()
            result = datos["chart"]["result"][0]
            timestamps = result.get("timestamp", [])
            precios    = result["indicators"]["quote"][0].get("close", [])

            if not timestamps or not precios:
                return {"error": f"No se encontraron datos para {ticker}."}

            historial = [
                {
                    "fecha": datetime.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d"),
                    "valor": precio or 0
                }
                for ts, precio in zip(timestamps, precios)
            ]
            meta = result["meta"]
            exchange = meta.get("exchangeName", "N/A")
            if exchange == "NMS": exchange = "NASDAQ"

            return {
                "FECHA_CONSULTA": historial[-1]["fecha"],
                "HORA": datetime.datetime.utcfromtimestamp(timestamps[-1]).strftime("%H:%M:%S"),
                "STOCK_NAME": meta.get("longName", ticker),
                "STOCK_SYMBOL": meta.get("symbol", ticker),
                "CURRENCY": meta.get("currency", "USD"),
                "EXCHANGE": exchange,
                "HISTORIAL_VALORES": historial,
                "VALUE": historial[-1]["valor"]
            }

        except requests.HTTPError as e:
            status = getattr(e.response, "status_code", None)
            if status == 429 and attempt < max_attempts:
                # back-off exponencial
                time.sleep(delay)
                delay *= 2
                continue
            return {"error": f"Error en la solicitud para {ticker}: {e}"}
        except Exception as e:
            return {"error": f"Error en la solicitud para {ticker}: {e}"}

    # Si agotamos todos los intentos:
    return {"error": f"Demasiados intentos fallidos para {ticker}"}


@app.route("/datos", methods=["GET"])
def obtener_datos():
    tickers   = [t.strip() for t in request.args.get("tickers", "").split(",") if t]
    intervalo = request.args.get("intervalo", "1d")
    rango     = request.args.get("rango", "1mo")

    resultados = []
    for ticker in tickers:
        data = obtener_datos_yahoo(ticker, intervalo, rango)
        if "STOCK_SYMBOL" not in data:
            data["STOCK_SYMBOL"] = ticker
        resultados.append(data)
        time.sleep(0.3)  # pausa de 300 ms entre cada ticker
    return jsonify({"intervalo": intervalo, "rango": rango, "datos": resultados})
