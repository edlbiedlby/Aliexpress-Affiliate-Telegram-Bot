from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/')
def home():
    return "Je suis vivant !"

def run():
    app.run(host='0.0.0.0', port=5000)  # Change le port à 5000, ou un autre port non utilisé.

def keep_alive():
    t = Thread(target=run)
    t.start()
