# CloudShop — projet Docker (Introduction au Cloud)

Une petite boutique en ligne découpée en conteneurs Docker : trois copies de la
boutique derrière un load balancer, une base PostgreSQL partagée et Metabase
pour l'analyse BI des commandes.

## Architecture

```
Navigateur ──► localhost:8080
                   │
            ┌──────▼───────┐
            │ load-balancer│  Nginx, round robin
            └──┬────┬────┬─┘
               │    │    │
     boutique-1  boutique-2  boutique-3     (Flask + gunicorn, port 5000, 0,1 CPU chacune)
               │    │    │
            ┌──▼────▼────▼─┐
            │   postgres   │  base "cloudshop", port 5432  ◄── volume pgdata
            └──────▲───────┘
                   │
            ┌──────┴───────┐
            │   metabase   │  tableaux de bord BI, localhost:3000  ◄── volume mbdata
            └──────────────┘
```

Tous les conteneurs sont sur le même réseau Docker (`cloudshop_default`) et se
trouvent par leur nom de service (`postgres`, `boutique-1`, `load-balancer`…).

## Les fichiers

| Fichier | Rôle |
|---|---|
| `init/init.sql` | Crée les tables `produits`, `clients`, `commandes` et insère les données de départ (8 produits, 10 clients, 500 commandes « historique »). Exécuté automatiquement par PostgreSQL au tout premier démarrage. |
| `boutique/app.py` | L'application web Flask : liste des produits, bouton « Acheter », routes `/acheter` (achat au hasard) et `/qui` (nom du conteneur). |
| `boutique/requirements.txt` | Les bibliothèques Python à installer : flask, psycopg2-binary, gunicorn. |
| `boutique/Dockerfile` | La recette pour construire l'image `raniette/cloudshop-boutique:1.0` (publiée sur Docker Hub). |
| `lb/default.conf` | La configuration Nginx du load balancer (round robin sur les 3 boutiques, bascule si l'une tombe). Grâce à `resolver` + `resolve`, Nginx retrouve tout seul la nouvelle IP d'une boutique recréée. Si tu modifies ce fichier, recrée le load balancer : `docker compose up -d --force-recreate load-balancer`. |
| `docker-compose.yml` | Décrit tous les services, leurs ports, variables, volumes et dépendances. |
| `test-charge.sh` | Envoie 300 achats (10 en parallèle) avec ApacheBench puis compte les commandes par boutique. |

## Commandes utiles

```bash
# (Facultatif) Reconstruire l'image de la boutique à partir du code
docker build -t raniette/cloudshop-boutique:1.0 ./boutique

# Republier l'image sur Docker Hub (Mac M1/M2 + PC Intel), après docker login
docker buildx build --platform linux/arm64,linux/amd64 -t raniette/cloudshop-boutique:1.0 --push ./boutique

# Démarrer tout le projet en arrière-plan
docker compose up -d

# Voir l'état des conteneurs
docker compose ps

# Voir les logs (ex. d'une boutique)
docker compose logs -f boutique-1

# Quel conteneur répond ? (relancer plusieurs fois)
curl http://localhost:8080/qui

# Test de charge
./test-charge.sh

# Ouvrir psql dans la base
docker compose exec postgres psql -U cloudshop -d cloudshop

# Simuler une panne : arrêter une boutique, puis la relancer
docker compose stop boutique-2
docker compose start boutique-2

# Tout arrêter (les données sont conservées dans les volumes)
docker compose down

# Tout arrêter ET effacer les données (init.sql sera rejoué au prochain démarrage)
docker compose down -v
```

## Adresses

- Boutique : http://localhost:8080
- Metabase : http://localhost:3000 — pour ajouter la base : type PostgreSQL,
  hôte `postgres`, port `5432`, base `cloudshop`, utilisateur et mot de passe `cloudshop`.

## Lancer le projet sur un autre ordinateur

Il suffit d'avoir **Docker Desktop** installé et démarré (Mac, Windows ou Linux).
L'image de la boutique est publique sur Docker Hub
(`raniette/cloudshop-boutique:1.0`, pour processeurs Intel/AMD et Apple Silicon) :
pas besoin de la reconstruire.

1. Aller sur https://github.com/rania-benbrahim/cloudshop-bi
2. Cliquer sur le bouton vert **Code**, puis **Download ZIP**.
3. Décompresser le ZIP (on obtient un dossier `cloudshop-bi-main`).
4. Ouvrir un terminal dans ce dossier et lancer :

```bash
docker compose up -d
```

Docker télécharge alors automatiquement toutes les images (PostgreSQL, Metabase,
Nginx et notre boutique depuis Docker Hub), crée la base avec `init/init.sql`
et démarre les 6 conteneurs. Après une à deux minutes :

- Boutique : http://localhost:8080
- Metabase : http://localhost:3000

Les ports 8080, 3000 et 5432 doivent être libres sur l'ordinateur.
Sous Windows, `test-charge.sh` se lance depuis Git Bash ou WSL.

Les mots de passe (`cloudshop`) sont des valeurs de démonstration pour ce projet
de cours : ne pas les réutiliser pour un vrai service.
