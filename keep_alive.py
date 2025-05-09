from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Je suis vivant !"

def run():
    app.run(host='0.0.0.0', port=0)  # port=0 dit à Flask de choisir automatiquement un port libre

def keep_alive():
    t = Thread(target=run)
    t.start()
