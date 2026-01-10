#!/bin/bash
set -e

echo "🔧 FIX 504 GATEWAY TIMEOUT"
echo "=========================="

cd /opt/uptime-monitor

echo "🛑 Arrêt des containers..."
docker-compose down 2>/dev/null || true
docker rm -f observability_backend observability_nginx observability_postgres observability_redis 2>/dev/null || true
sleep 2

echo "🔨 Rebuild backend..."
docker-compose build --no-cache backend

echo "🚀 Démarrage des services..."
docker-compose up -d

echo "⏳ Attente PostgreSQL..."
timeout 60 bash -c 'until docker exec observability_postgres pg_isready -U postgres 2>/dev/null; do sleep 2; done'

echo "⏳ Attente backend (30s)..."
sleep 30

echo "🔍 Test backend direct..."
for i in {1..10}; do
    if curl -f http://localhost:8000/health 2>/dev/null; then
        echo "✅ Backend répond!"
        break
    fi
    echo "Tentative $i/10..."
    sleep 3
done

echo "🔍 Test via nginx..."
sleep 5
if curl -f http://localhost/health 2>/dev/null; then
    echo "✅✅✅ SUCCÈS!"
    echo "🌐 URL: http://localhost"
    curl http://localhost/health | jq .
else
    echo "❌ Échec - Logs:"
    docker-compose ps
    echo -e "\n📝 Backend:"
    docker logs observability_backend --tail=50
    echo -e "\n📝 Nginx:"
    docker logs observability_nginx --tail=50
    exit 1
fi

echo -e "\n📊 État final:"
docker-compose ps
