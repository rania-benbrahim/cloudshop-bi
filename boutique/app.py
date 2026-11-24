# CloudShop - boutique web (Flask)
# Chaque conteneur "boutique" exécute ce même code.
# Le hostname du conteneur (boutique-1, boutique-2 ou boutique-3) est affiché
# pour voir quel conteneur a servi la page derrière le load balancer.

import os
import random
import socket

import psycopg2
from flask import Flask, render_template_string, url_for

app = Flask(__name__)
HOSTNAME = socket.gethostname()


def get_connexion():
    """Ouvre une connexion à PostgreSQL avec les variables d'environnement."""
    return psycopg2.connect(
        host=os.environ.get("DB_HOST", "postgres"),
        dbname=os.environ.get("DB_NAME", "cloudshop"),
        user=os.environ.get("DB_USER", "cloudshop"),
        password=os.environ.get("DB_PASSWORD", "cloudshop"),
        connect_timeout=5,
    )


def creer_commande(produit_id=None):
    """Insère une commande : client au hasard, quantité 1, boutique = hostname."""
    with get_connexion() as conn, conn.cursor() as cur:
        cur.execute("SELECT id FROM clients ORDER BY random() LIMIT 1")
        client_id = cur.fetchone()[0]
        if produit_id is None:
            cur.execute("SELECT id FROM produits ORDER BY random() LIMIT 1")
            produit_id = cur.fetchone()[0]
        cur.execute(
            """INSERT INTO commandes (client_id, produit_id, quantite, boutique)
               VALUES (%s, %s, 1, %s) RETURNING id""",
            (client_id, produit_id, HOSTNAME),
        )
        commande_id = cur.fetchone()[0]
        cur.execute(
            """SELECT c.nom, c.ville, p.nom, p.prix FROM clients c, produits p
               WHERE c.id = %s AND p.id = %s""",
            (client_id, produit_id),
        )
        client, ville, produit, prix = cur.fetchone()
    return {"id": commande_id, "client": client, "ville": ville,
            "produit": produit, "prix": prix}


PAGE = """<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CloudShop</title>
<style>
  * { box-sizing: border-box; }
  body { margin: 0; font-family: -apple-system, "Segoe UI", Roboto, sans-serif;
         background: #f6f4f1; color: #2b2b2b; }
  header { background: #2f3e46; color: #fff; padding: 24px 32px;
           display: flex; justify-content: space-between; align-items: center;
           flex-wrap: wrap; gap: 12px; }
  header h1 { margin: 0; font-size: 28px; letter-spacing: .5px; }
  header p { margin: 4px 0 0; opacity: .8; }
  .serveur { background: #f4a261; color: #2b2b2b; font-weight: 700;
             padding: 10px 16px; border-radius: 8px; font-size: 18px; }
  main { max-width: 1100px; margin: 0 auto; padding: 32px; }
  .confirmation { background: #e9f5ec; border: 1px solid #8cc9a0; color: #1e5631;
                  padding: 16px 20px; border-radius: 10px; margin-bottom: 24px; }
  .grille { display: grid; gap: 20px;
            grid-template-columns: repeat(auto-fill, minmax(230px, 1fr)); }
  .carte { background: #fff; border-radius: 12px; padding: 20px;
           box-shadow: 0 2px 8px rgba(0,0,0,.06); display: flex;
           flex-direction: column; gap: 8px; }
  .categorie { font-size: 12px; text-transform: uppercase; letter-spacing: 1px;
               color: #84a98c; font-weight: 600; }
  .nom { font-size: 18px; font-weight: 600; }
  .prix { font-size: 20px; color: #2f3e46; margin-top: auto; }
  button { background: #2f3e46; color: #fff; border: 0; border-radius: 8px;
           padding: 10px; font-size: 15px; cursor: pointer; width: 100%; }
  button:hover { background: #52796f; }
  .erreur { background: #fdecea; border: 1px solid #f5a5a0; color: #8a1c13;
            padding: 16px 20px; border-radius: 10px; }
</style>
</head>
<body>
<header>
  <div>
    <h1>CloudShop</h1>
    <p>Mode, accessoires et beauté</p>
  </div>
  <div class="serveur">Page servie par : {{ hostname }}</div>
</header>
<main>
  {% if commande %}
  <div class="confirmation">
    Merci ! Commande n°{{ commande.id }} enregistrée :
    <strong>{{ commande.produit }}</strong> ({{ "%.2f"|format(commande.prix) }} DT)
    pour {{ commande.client }} ({{ commande.ville }}), traitée par <strong>{{ hostname }}</strong>.
  </div>
  {% endif %}
  {% if erreur %}
  <div class="erreur">Base de données indisponible : {{ erreur }}</div>
  {% else %}
  <div class="grille">
    {% for p in produits %}
    <div class="carte">
      <span class="categorie">{{ p[2] }}</span>
      <span class="nom">{{ p[1] }}</span>
      <span class="prix">{{ "%.2f"|format(p[3]) }} DT</span>
      <form method="post" action="{{ url_for('acheter_produit', produit_id=p[0]) }}">
        <button type="submit">Acheter</button>
      </form>
    </div>
    {% endfor %}
  </div>
  {% endif %}
</main>
</body>
</html>"""


def afficher_page(commande=None):
    """Affiche la liste des produits (et la confirmation d'achat s'il y en a une)."""
    produits, erreur = [], None
    try:
        with get_connexion() as conn, conn.cursor() as cur:
            cur.execute("SELECT id, nom, categorie, prix FROM produits ORDER BY id")
            produits = cur.fetchall()
    except psycopg2.Error as e:
        erreur = str(e).strip()
    return render_template_string(PAGE, hostname=HOSTNAME, produits=produits,
                                  commande=commande, erreur=erreur)


@app.route("/")
def accueil():
    return afficher_page()


@app.route("/acheter/<int:produit_id>", methods=["POST"])
def acheter_produit(produit_id):
    """Bouton "Acheter" : crée la commande et affiche la confirmation."""
    return afficher_page(commande=creer_commande(produit_id))


@app.route("/acheter")
def acheter_hasard():
    """Pour le test de charge : une commande au hasard.
    Réponse toujours identique ("OK") : ApacheBench compte comme "échec"
    toute réponse dont la longueur change (ex. commande 999 -> 1000)."""
    creer_commande()
    return "OK\n", 200, {"Content-Type": "text/plain; charset=utf-8"}


@app.route("/qui")
def qui():
    return HOSTNAME + "\n", 200, {"Content-Type": "text/plain; charset=utf-8"}
