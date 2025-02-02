from flask import Flask
from threading import Thread

app = Flask(__name__)

@app.route('/')
def home():
    return "Alive"

def run():
    """Ejecuta el servidor Flask en el puerto 8080."""
    app.run(host='0.0.0.0', port=5000)

def keep_alive():
    """Ejecuta el servidor en un hilo separado para mantener Replit activo."""
    server = Thread(target=run)
    server.start()