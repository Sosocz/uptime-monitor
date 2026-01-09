# ⚡ Checklist Launch 48h - TrezApp

## 🎯 Objectif : Lancer Product Hunt + 20 emails agences cette semaine

---

## ✅ TODAY (Jour 0)

### 1. Screenshots Product Hunt (2h max)
Besoin de 5 images HD :

1. **Dashboard** - Vue d'ensemble monitors
   - Créer 3-4 monitors avec vrais sites
   - Screenshot du dashboard avec graphs

2. **Incident Alert** - Notification Telegram
   - Déclencher une alerte test
   - Screenshot du message Telegram mobile

3. **Status Page** - Page publique
   - Créer une status page avec 2-3 monitors
   - Screenshot de la page publique clean

4. **Badge Uptime** - Badge intégrable
   - Screenshot d'un badge 99.9% dans un README.md

5. **Pricing** - Page pricing
   - Screenshot de la page avec FREE/PRO

**Tool :** CleanShot X / Flameshot / Browser screenshot
**Format :** PNG, 1200x800px min

---

### 2. Code promo Stripe (30 min)

Créer coupon dans Stripe Dashboard :
```
Code: PRODUCTHUNT30
Type: Percentage discount
Amount: 30% off
Duration: Forever
Applies to: PRO plan (price_xxx)
Max redemptions: 200
```

Tester sur environnement staging.

---

### 3. Pricing annuel Stripe (1h)

```python
# Dans .env
STRIPE_PRICE_ID_PRO_MONTHLY=price_xxx
STRIPE_PRICE_ID_PRO_YEARLY=price_yyy  # €180/an (€15/mois)

# Créer dans Stripe Dashboard
Product: TrezApp PRO
Price: €180/year
Billing period: Yearly
```

Update UI pricing page :
```html
<div class="toggle">
  [Monthly] [Yearly - Save 20%]
</div>
```

**Skip si ça prend > 1h. Faire après PH.**

---

## ✅ TOMORROW (Jour 1)

### 4. Draft Product Hunt (1h)

Aller sur producthunt.com/posts/new

**Remplir :**
- Nom : TrezApp
- Tagline : Monitor your websites 24/7. Get instant alerts.
- Description : (copier depuis PRODUCT_HUNT_LAUNCH.md)
- Upload screenshots (5 images)
- Upload logo
- Tags : monitoring, devtools, saas, productivity
- Pricing : Free, Paid ($19/month)

**Sauvegarder en DRAFT. Ne pas publier encore.**

---

### 5. Choisir jour de launch (5 min)

**Meilleurs jours :**
- Mardi 14 janvier
- Mercredi 15 janvier
- Jeudi 16 janvier

**Éviter :**
- Lundi (traffic faible)
- Vendredi (weekend)
- Weekend (quasi mort)

**Action :** Mettre alarme 00h01 PST du jour choisi.

---

### 6. Outreach agences - 20 emails (2h)

**Liste de prospection :**
- Chercher sur LinkedIn : "agence web france"
- Chercher sur Google : "agence wordpress [ville]"
- Prendre email sur leur site

**Template (copier depuis OUTREACH_AGENCIES.md) :**
```
Subject : Monitoring gratuit pour vos sites clients ?

Bonjour [Prénom],

Je lance TrezApp, monitoring uptime pour agences web.

Proposition simple :
→ Je configure gratuitement 5-10 de vos sites clients
→ Alertes email/Telegram si un site tombe
→ Status page publique pour chaque client

Setup en 15 min. Intéressé pour un essai ?

[Ton prénom]
TrezApp - trezapp.com
```

**Tracker dans Google Sheets :**
| Agence | Email | Date | Statut |
|--------|-------|------|--------|
| Agence A | jean@.. | 09/01 | Envoyé |

**Objectif : 3 réponses positives = succès.**

---

## 🚀 LAUNCH DAY (Jour choisi)

### 00h01 PST (09h01 Paris) - Lancer PH

1. Ouvrir draft Product Hunt
2. Cliquer "Publish"
3. Poster first comment (copier depuis PRODUCT_HUNT_LAUNCH.md)

### 09h-18h - Répondre aux commentaires

- Check PH toutes les 30 min
- Répondre < 30 min à TOUS les commentaires
- Être présent, humain, humble

### 18h PST (03h Paris +1) - Fin de journée

- Screenshot classement final
- Email remerciement aux nouveaux users
- Dormir

---

## 📊 Métriques à tracker (dès J+1)

Dashboard simple (Google Sheet suffit) :

| Date | Visitors | Signups | 1er monitor | Notif activée | PRO |
|------|----------|---------|-------------|---------------|-----|
| 09/01 | 500 | 50 | 30 (60%) | 10 (20%) | 2 (4%) |

**Ratios importants :**
- Signup rate : 5-15% (bon)
- Activation (1er monitor) : 50%+ (bon)
- Notif activée : 20%+ (bon)
- Conversion PRO : 2-5% (bon)

**Si un ratio est mauvais :**
- < 40% activation → onboarding pas clair
- < 10% notif → pas assez pushé
- < 1% PRO → pricing trop cher ou valeur pas claire

---

## ❌ À NE PAS FAIRE

1. **Toucher au code avant PH**
   → Risque de casser quelque chose

2. **Envoyer 100 emails agences**
   → 20 max. Test le message d'abord.

3. **Ajouter features "au cas où"**
   → Lance avec ce que tu as. Itère après.

4. **Optimiser le moindre pixel**
   → Good enough > Perfect but late

5. **Tweaker pricing avant d'avoir des données**
   → Lance à €19/mois. Ajuste après 50 users.

---

## ✅ Success criteria (fin de semaine)

**Product Hunt :**
- [ ] 100+ upvotes
- [ ] Top 10 de la journée
- [ ] 50+ signups depuis PH

**Agences :**
- [ ] 20 emails envoyés
- [ ] 3+ réponses positives
- [ ] 1+ call booké

**Produit :**
- [ ] Code promo PH fonctionnel
- [ ] Aucun bug critique remonté
- [ ] Serveurs stables (pas de downtime)

---

## 🔥 Mindset

> "Launched is better than perfect."

Tu es à 90% ready. Les 10% restants, tu les feras APRÈS avoir eu du feedback réel.

👉 **Ship now. Optimize later.**

---

## 📞 Besoin d'aide ?

Si bug critique pendant PH :
1. Check logs : `docker-compose logs -f app`
2. Rollback si nécessaire : `git revert HEAD`
3. Communique sur PH : "We're fixing X, back in 10min"

Sinon : **Tu as tout ce qu'il faut. Go launch.**
