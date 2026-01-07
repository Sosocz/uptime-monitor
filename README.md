# 🚀 TrezApp - Uptime Monitor SaaS

Un service de monitoring uptime complet avec notifications par email et Telegram, paiement Stripe, et interface moderne.

## 📋 Fonctionnalités

- ✅ **Auth**: Register/Login avec JWT
- ✅ **Monitors**: CRUD complet (URL, nom, interval, timeout)
- ✅ **Checks**: Vérification HTTP automatique
- ✅ **Incidents**: Détection up→down et down→up
- ✅ **Notifications**: Email SMTP + Telegram Bot
- ✅ **Plans**:
  - FREE: 1 monitor, interval 10 min
  - PAID: 50 monitors, interval 1 min
- ✅ **Stripe**: Checkout, Portal, Webhooks

---

## 🖥️ DÉPLOIEMENT SUR VPS UBUNTU

### ÉTAPE 1: Configuration DNS (Cloudflare)

1. Connectez-vous à Cloudflare
2. Ajoutez ces enregistrements DNS:

| Type | Nom | Contenu | Proxy |
|------|-----|---------|-------|
| A | @ | 51.68.126.222 | ✅ Orange |
| A | www | 51.68.126.222 | ✅ Orange |

---

### ÉTAPE 2: Connexion au VPS

```bash
ssh root@51.68.126.222
```

---

### ÉTAPE 3: Installation des dépendances

```bash
# Mettre à jour le système
apt update && apt upgrade -y

# Installer Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Installer Docker Compose
apt install -y docker-compose

# Installer Nginx
apt install -y nginx

# Installer Certbot
apt install -y certbot python3-certbot-nginx

# Vérifier installations
docker --version
docker-compose --version
nginx -v
```

---

### ÉTAPE 4: Créer le projet

```bash
# Créer le dossier
mkdir -p /opt/uptime-monitor
cd /opt/uptime-monitor
```

**Option A: Cloner depuis GitHub (si tu as push le code)**
```bash
git clone https://github.com/TON_USERNAME/uptime-monitor.git .
```

**Option B: Copier les fichiers manuellement**
Utilise `scp` depuis ton PC:
```bash
# Depuis ton PC Windows (PowerShell)
scp -r C:\Users\soso\Desktop\uptime-monitor\* root@51.68.126.222:/opt/uptime-monitor/
```

---

### ÉTAPE 5: Configurer l'environnement

```bash
cd /opt/uptime-monitor

# Copier le fichier d'exemple
cp .env.example .env

# Éditer le fichier .env
nano .env
```

**Contenu du .env (remplace les valeurs):**

```env
DATABASE_URL=postgresql://uptime_user:uptime_pass@db:5432/uptime_db
JWT_SECRET=GENERE_UNE_CLE_ALEATOIRE_ICI_64_CARACTERES
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=ton-email@gmail.com
SMTP_PASS=ton-app-password-gmail
SMTP_FROM=ton-email@gmail.com
TELEGRAM_BOT_TOKEN=123456:ABC-ton-token-telegram
STRIPE_SECRET_KEY=sk_live_xxx
STRIPE_PUBLISHABLE_KEY=pk_live_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx
STRIPE_PRICE_ID_MONTHLY=price_xxx
APP_BASE_URL=https://trezapp.fr
```

**Générer JWT_SECRET:**
```bash
openssl rand -hex 32
```

---

### ÉTAPE 6: Build et lancer Docker

```bash
cd /opt/uptime-monitor

# Build et lancer
docker-compose up -d --build

# Vérifier les logs
docker-compose logs -f

# Vérifier que tout tourne
docker-compose ps
```

Tu dois voir 3 containers: `db`, `app`, `worker`

---

### ÉTAPE 7: Configurer Nginx

```bash
# Copier la config
cp /opt/uptime-monitor/nginx/trezapp.conf /etc/nginx/sites-available/trezapp.conf

# Créer le lien symbolique
ln -s /etc/nginx/sites-available/trezapp.conf /etc/nginx/sites-enabled/

# Supprimer la config par défaut
rm /etc/nginx/sites-enabled/default

# Tester la config (va échouer pour SSL, c'est normal)
nginx -t
```

**Créer une config temporaire sans SSL:**

```bash
cat > /etc/nginx/sites-available/trezapp.conf << 'EOF'
server {
    listen 80;
    server_name trezapp.fr www.trezapp.fr;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
EOF
```

```bash
# Créer le dossier pour Certbot
mkdir -p /var/www/certbot

# Redémarrer Nginx
systemctl restart nginx
```

---

### ÉTAPE 8: Obtenir le certificat SSL

```bash
# Obtenir le certificat
certbot --nginx -d trezapp.fr -d www.trezapp.fr

# Suivre les instructions:
# - Entrer ton email
# - Accepter les conditions
# - Choisir de rediriger HTTP vers HTTPS
```

---

### ÉTAPE 9: Configurer Stripe Webhook

1. Va sur https://dashboard.stripe.com/webhooks
2. Clique "Add endpoint"
3. URL: `https://trezapp.fr/api/stripe/webhook`
4. Événements à sélectionner:
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
5. Copie le "Signing secret" (whsec_xxx)
6. Mets-le dans ton `.env` sur le VPS:

```bash
nano /opt/uptime-monitor/.env
# Remplace STRIPE_WEBHOOK_SECRET=whsec_xxx
```

7. Redémarre l'app:
```bash
cd /opt/uptime-monitor
docker-compose restart app
```

---

### ÉTAPE 10: Créer le produit Stripe

1. Va sur https://dashboard.stripe.com/products
2. Clique "Add product"
3. Nom: "Pro Plan"
4. Prix: 9,99€/mois (ou ce que tu veux)
5. Copie le `price_xxx`
6. Mets-le dans `.env`: `STRIPE_PRICE_ID_MONTHLY=price_xxx`
7. Redémarre: `docker-compose restart app`

---

## ✅ TESTS

### Test 1: API Health
```bash
curl https://trezapp.fr/health
# Attendu: {"status":"healthy","service":"uptime-monitor"}
```

### Test 2: Page Login
Ouvre dans ton navigateur: https://trezapp.fr/login

### Test 3: Register
1. Va sur https://trezapp.fr/register
2. Crée un compte
3. Connecte-toi
4. Crée un monitor

### Test 4: Vérifier les logs
```bash
docker-compose logs -f worker
# Tu dois voir "Checking monitor: xxx"
```

---

## 🔧 COMMANDES UTILES

```bash
# Voir les logs
docker-compose logs -f

# Redémarrer
docker-compose restart

# Arrêter
docker-compose down

# Reconstruire
docker-compose up -d --build

# Voir l'état
docker-compose ps

# Accéder à la DB
docker-compose exec db psql -U uptime_user -d uptime_db
```

---

## 📱 Configuration Telegram (optionnel)

1. Crée un bot avec @BotFather sur Telegram
2. Copie le token
3. Mets-le dans `.env`: `TELEGRAM_BOT_TOKEN=xxx`
4. Pour obtenir ton chat_id:
   - Envoie un message à ton bot
   - Va sur: `https://api.telegram.org/botTON_TOKEN/getUpdates`
   - Copie le `chat.id`

---

## 🔐 Sécurité

- ⚠️ Ne partage JAMAIS tes clés API
- ⚠️ Utilise des mots de passe forts
- ⚠️ Le fichier `.env` ne doit JAMAIS être commit sur Git
- ✅ Le firewall UFW est recommandé:

```bash
ufw allow 22
ufw allow 80
ufw allow 443
ufw enable
```

---

## 📞 Support

En cas de problème:
1. Vérifie les logs: `docker-compose logs -f`
2. Vérifie que tous les containers tournent: `docker-compose ps`
3. Vérifie Nginx: `nginx -t` et `systemctl status nginx`
