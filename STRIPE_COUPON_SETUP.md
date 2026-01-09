# 🎟️ Setup Stripe Coupon PRODUCTHUNT30

## 1. Créer le coupon dans Stripe Dashboard

1. Aller sur https://dashboard.stripe.com/coupons
2. Cliquer "Create coupon"
3. Remplir :

```
Coupon ID: PRODUCTHUNT30
Type: Percentage discount
Discount: 30% off
Duration: Forever (applies to all invoices)
Currency: EUR
Max redemptions: 200 (optionnel)
```

4. Cliquer "Create coupon"

## 2. Tester le coupon

Le code backend est déjà prêt. Pour tester :

```bash
# Test avec coupon
curl -X POST http://localhost:8000/api/stripe/create-checkout \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"coupon_code": "PRODUCTHUNT30"}'
```

## 3. Ajouter dans le frontend

Dans votre page pricing/dashboard, ajouter un champ coupon :

```javascript
async function buyPro() {
    const token = localStorage.getItem('token');
    const coupon = document.getElementById('coupon-input')?.value || null;

    const response = await fetch('/api/stripe/create-checkout', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer ' + token
        },
        body: JSON.stringify({ coupon_code: coupon })
    });

    const data = await response.json();
    if (data.checkout_url) window.location.href = data.checkout_url;
}
```

## 4. Landing page Product Hunt

Ajouter sur la landing :

```html
<div class="ph-banner">
  🎉 Product Hunt Special: Get PRO at €13/month forever with code <strong>PRODUCTHUNT30</strong>
  <a href="/register?coupon=PRODUCTHUNT30">Claim offer →</a>
</div>
```

## 5. Vérification

Une fois le coupon créé dans Stripe, vérifier :
- [ ] Coupon ID = "PRODUCTHUNT30"
- [ ] 30% off forever
- [ ] Appliqué au plan PRO (€19 → €13.30/mois)
- [ ] Frontend a le champ coupon
- [ ] Banner PH sur landing page

✅ **Le backend est prêt. Il suffit de créer le coupon dans Stripe Dashboard.**
