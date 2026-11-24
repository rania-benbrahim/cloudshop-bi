#!/bin/sh
# Test de charge CloudShop : 300 achats envoyés au load balancer, 10 à la fois.
# ApacheBench (ab) tourne dans un conteneur httpd:alpine branché sur le réseau du projet.
cd "$(dirname "$0")"

echo "=== Test de charge : 300 requêtes, 10 en parallèle ==="
docker run --rm --network cloudshop_default httpd:alpine \
  ab -n 300 -c 10 http://load-balancer/acheter

echo
echo "=== Commandes par boutique (hors historique) ==="
docker compose exec -T postgres psql -U cloudshop -d cloudshop -c \
  "SELECT boutique, count(*) AS nb_commandes FROM commandes WHERE boutique <> 'historique' GROUP BY boutique ORDER BY boutique;"
