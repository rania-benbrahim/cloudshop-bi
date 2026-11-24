# Image de départ : Python 3.12 en version "slim" (légère)
FROM python:3.12-slim

# Dossier de travail à l'intérieur du conteneur
WORKDIR /app

# On copie d'abord la liste des bibliothèques et on les installe
# (Docker garde cette étape en cache tant que requirements.txt ne change pas)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# On copie ensuite le code de la boutique
COPY app.py .

# La boutique écoute sur le port 5000
EXPOSE 5000

# Commande lancée au démarrage du conteneur : le serveur gunicorn
# avec 2 workers, qui sert l'application Flask "app" du fichier app.py
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--access-logfile", "-", "app:app"]
