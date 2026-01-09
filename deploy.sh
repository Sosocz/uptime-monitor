#!/bin/bash
# Deployment script for TrezApp

echo "🚀 Déploiement TrezApp..."

# Run migrations
echo "📦 Migration de la base de données..."
docker-compose exec -T web python migrations/run_all_migrations.py || {
    echo "⚠️  Migrations échouées (normal si première fois)"
}

# Restart services
echo "🔄 Redémarrage des services..."
docker-compose restart

echo "✅ Déploiement terminé !"
echo ""
echo "Services disponibles :"
echo "  - API: http://localhost:8000"
echo "  - Docs: http://localhost:8000/docs"
echo "  - ARQ Worker: En arrière-plan"
echo ""
echo "Pour voir les logs : docker-compose logs -f"
