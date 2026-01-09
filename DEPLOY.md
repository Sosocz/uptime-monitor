# 🚀 Guide de déploiement TrezApp

## Avant la mise en prod

### ✅ Checklist complétée

1. ✅ Email onboarding (J0/J1/J3) avec logique contextuelle
2. ✅ Badge "Powered by TrezApp" (désactivable en PAID)
3. ✅ Badges SVG intégrables avec sécurité (rate limit + public check)
4. ✅ Structure webhooks documentée (events futurs)
5. ✅ Pages SEO (use cases + comparatifs + meta tags)
6. ✅ Tracking minimal (inscription, monitors, Telegram, status pages)

### 🔧 Déploiement

```bash
# 1. Lancer les services
docker-compose up -d

# 2. Attendre 10s que Postgres démarre
sleep 10

# 3. Lancer les migrations
docker-compose exec web python migrations/run_all_migrations.py

# 4. Redémarrer les services
docker-compose restart

# 5. Vérifier les logs
docker-compose logs -f
```

**OU utilisez le script automatique :**

```bash
./deploy.sh
```

### 📊 Vérifications post-déploiement

1. **API Health Check**
   ```bash
   curl http://localhost:8000/health
   ```

2. **Pages SEO accessibles**
   - http://localhost:8000/use-cases/wordpress
   - http://localhost:8000/use-cases/shopify
   - http://localhost:8000/vs/uptimerobot

3. **Badges SVG fonctionnent**
   - Créer un monitor sur une status page publique
   - Tester : http://localhost:8000/api/badge/{monitor_id}/uptime.svg

4. **Tracking fonctionne**
   ```sql
   SELECT event_type, COUNT(*)
   FROM tracking_events
   GROUP BY event_type;
   ```

### 🔍 Monitoring

**Vérifier les emails onboarding :**
```sql
-- Voir les users éligibles J+1
SELECT id, email, created_at
FROM users
WHERE onboarding_email_j1_sent = FALSE
  AND created_at >= NOW() - INTERVAL '25 hours'
  AND created_at <= NOW() - INTERVAL '24 hours';
```

**Voir les événements trackés :**
```sql
SELECT * FROM tracking_events ORDER BY created_at DESC LIMIT 50;
```

### ⚠️ Points critiques

1. **Worker ARQ** : Doit tourner 24/7 pour les emails onboarding
   ```bash
   docker-compose logs arq-worker
   ```

2. **Cron onboarding** : S'exécute toutes les 6h (0h, 6h, 12h, 18h)

3. **Rate limiting badges** : 100 req/min par IP (in-memory, reset au restart)

### 🎯 Prochaines étapes

1. **Ajouter analytics** (Plausible, Simple Analytics, ou custom)
2. **Sitemap.xml** pour SEO
3. **Tests A/B** sur CTAs
4. **Product Hunt launch** (landing dédiée)
5. **Outreach agences/freelances**

### 📝 Notes

- **Plan FREE** : 10 monitors, checks 5min
- **Plan PRO** : Illimité, checks 1min, 19€/mois
- **Badge Powered by** : Forcé en FREE, optionnel en PAID
- **Badges SVG** : Uniquement monitors sur status pages publiques
