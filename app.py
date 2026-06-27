from flask import Flask
import threading
import os

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Sandbox AI Aktif 24/7!"

def run_flask():
    # Render otomatis memberikan port lewat environment variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

def start_server():
    server_thread = threading.Thread(target=run_flask)
    server_thread.daemon = True
    server_thread.start()
