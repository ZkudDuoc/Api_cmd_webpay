from flask import Flask, redirect, request
import requests
import os
from dotenv import load_dotenv

# Cargar las variables de entorno
load_dotenv()

app = Flask(__name__)

# === CONFIGURACIÓN ===
COMMERCE_CODE = os.getenv('COMMERCE_CODE')
API_KEY_SECRET = os.getenv('API_KEY_SECRET')
RETURN_URL = os.getenv('RETURN_URL')

TRANSBANK_API_URL = "https://webpay3gint.transbank.cl/rswebpaytransaction/api/webpay/v1.3/transactions"


@app.route('/')
def home():
    return '''
        <h2>Proyecto Transbank + CMF</h2>
        <ul>
            <li><a href="/dolar">Ver valor del dólar</a></li>
            <li><a href="/pagar">Iniciar pago</a></li>
        </ul>
    '''


@app.route('/dolar')
def obtener_dolar():
    url = f'https://api.cmfchile.cl/api-sbifv3/recursos_api/dolar?apikey={os.getenv("CMF_API_KEY")}&formato=json'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        valor = data['Dolares'][0]['Valor']
        return f'Valor del dólar hoy: {valor} CLP'
    else:
        return 'Error al obtener el valor del dólar.'


@app.route('/pagar')
def pagar():
    headers = {
        "Tbk-Api-Key-Id": COMMERCE_CODE,
        "Tbk-Api-Key-Secret": API_KEY_SECRET,
        "Content-Type": "application/json"
    }

    # Aquí debes modificar el cuerpo de la solicitud
    body = {
        "buy_order": "orden123456",  # El identificador único de la compra
        "session_id": "sesion123456",  # El identificador único de la sesión
        "amount": 1000,  # El monto de la transacción en CLP
        "return_url": RETURN_URL  # La URL a la que Webpay redirige después del pago
    }

    # Hacemos la solicitud a la API de Webpay
    response = requests.post(TRANSBANK_API_URL, json=body, headers=headers)

    if response.status_code == 200:
        data = response.json()  # Parseamos la respuesta
        token = data["token"]  # Token generado por Webpay
        url = data["url"]  # URL donde el usuario debe completar el pago

        # Redirigimos al usuario a la URL de Webpay
        return redirect(f"{url}?token_ws={token}")
    else:
        return f"Error iniciando transacción: {response.text}"

@app.route('/retorno')
def retorno():
    token = request.args.get("token_ws")  # Obtenemos el token desde la URL

    headers = {
        "Tbk-Api-Key-Id": COMMERCE_CODE,
        "Tbk-Api-Key-Secret": API_KEY_SECRET,
        "Content-Type": "application/json"
    }

    # Confirmamos la transacción con el token recibido
    response = requests.put(f"{TRANSBANK_API_URL}/{token}", headers=headers)

    if response.status_code == 200:
        data = response.json()
        # Aquí podrías guardar el estado de la transacción en tu base de datos
        return f"<h2>Pago exitoso</h2><pre>{data}</pre>"
    else:
        return f"<h2>Error al confirmar pago</h2><pre>{response.text}</pre>"
