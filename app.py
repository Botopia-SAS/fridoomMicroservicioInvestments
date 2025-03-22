import requests
from flask import Flask, jsonify, request
import datetime

app = Flask(__name__)
session = requests.Session()

# Función para obtener datos de Yahoo Finance
def obtener_datos_yahoo(ticker, intervalo, rango):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
    params = {"interval": intervalo, "range": rango}
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        respuesta = session.get(url, params=params, headers=headers, timeout=5)
        respuesta.raise_for_status()
        datos = respuesta.json()

        # Extraer información clave
        result = datos.get("chart", {}).get("result", [])[0]
        meta = result.get("meta", {})
        timestamps = result.get("timestamp", [])
        quote = result.get("indicators", {}).get("quote", [])[0]
        precios = quote.get("close", [])

        if not timestamps or not precios:
            return {"error": f"No se encontraron datos para {ticker}."}

        # Convertir timestamps a fechas legibles
        historial_valores = [
            {
                "fecha": datetime.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d"),
                "valor": precio,
            }
            for ts, precio in zip(timestamps, precios)
        ]

        # Tomar el último valor como "actual"
        fecha_consulta = historial_valores[-1]["fecha"]
        hora_consulta = datetime.datetime.utcfromtimestamp(timestamps[-1]).strftime("%H:%M:%S")

        # Corregir el nombre del exchange si es "NMS"
        exchange = meta.get("exchangeName", "N/A")
        if exchange == "NMS":
            exchange = "NASDAQ"

        stock_info = {
            "FECHA_CONSULTA": fecha_consulta,
            "HORA": hora_consulta,
            "STOCK_NAME": meta.get("longName", "Desconocido"),
            "STOCK_SYMBOL": meta.get("symbol", ticker),
            "CURRENCY": meta.get("currency", "USD"),
            "EXCHANGE": exchange,
            "HISTORIAL_VALORES": historial_valores,
            "VALUE": historial_valores[-1]["valor"],  # Último valor como actual
        }

        return stock_info

    except requests.RequestException as e:
        return {"error": f"Error en la solicitud para {ticker}: {str(e)}"}

# Endpoint optimizado para múltiples tickers
@app.route("/datos", methods=["GET"])
def obtener_datos():
    tickers = request.args.get("tickers", "").split(",")  # Permite múltiples tickers separados por coma
    intervalo = request.args.get("intervalo", "1d")
    rango = request.args.get("rango", "1mo")

    if not tickers or tickers == [""]:
        return jsonify({"error": "Debe proporcionar al menos un ticker"}), 400

    resultados = []
    for ticker in tickers:
        ticker = ticker.strip()
        data = obtener_datos_yahoo(ticker, intervalo, rango)
        if "STOCK_SYMBOL" not in data:
            data["STOCK_SYMBOL"] = ticker
        resultados.append(data)

    return jsonify({"intervalo": intervalo, "rango": rango, "datos": resultados})

if __name__ == "__main__":
    app.run(debug=True, threaded=True)
