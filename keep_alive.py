from flask import Flask
from threading import Thread

app = Flask(__name__)  # Il est recommandé d'utiliser __name__ pour l'initialisation de Flask.


@app.route('/')
def home():
    return "I'm alive"


def run():
    """
    Fonction pour démarrer l'application Flask.
    """
    app.run(host='0.0.0.0', port=8080)  # Le port peut être modifié selon le besoin.


def keep_alive():
    """
    Fonction pour démarrer l'application Flask dans un thread séparé.
    """
    t = Thread(target=run)  # Création d'un thread pour exécuter la fonction run() en arrière-plan
    t.daemon = True  # Définir le thread comme daemon pour qu'il s'arrête lorsque le programme principal se termine.
    t.start()  # Lancement du thread.
