# PostHog Reverse Proxy (trezapp.fr)

## Sous-domaine choisi
- `ph.trezapp.fr`

Options possibles (neutres):
- `ph.trezapp.fr`
- `e.trezapp.fr`
- `px.trezapp.fr`

## Region PostHog detectee
- US (POSTHOG_HOST = `https://app.posthog.com`)

Si votre projet est en EU, remplacez `app.posthog.com` par `eu.posthog.com`.

## Methode retenue
- Self-hosted via Nginx (config presente dans le repo)

## DNS
### Self-hosted (Nginx)
- Enregistrement A/AAAA existant pour `ph.trezapp.fr` pointant vers le serveur web.

### Managed PostHog (si active dans l'org)
- PostHog: Organization → Proxy settings → New managed proxy.
- Recuperer le domaine genere (ex: `xxxxx.proxy-us.posthog.com`).
- DNS:
  - Type: CNAME
  - Name: `ph`
  - Target: `xxxxx.proxy-us.posthog.com`
- Si Cloudflare: mettre le CNAME en `DNS only` (sinon SSL PostHog echoue).
- Attendre statut `live`.

## Config proxy (Nginx)
Fichier: `nginx/trezapp.conf`
- Nouveau vhost `ph.trezapp.fr` avec proxy vers `https://app.posthog.com`.
- Si EU, remplacez `app.posthog.com` par `eu.posthog.com`.
- Requis pour TLS: certificat incluant `ph.trezapp.fr` (LetsEncrypt).

## Config SDK (PostHog)
Fichier: `app/templates/partials/analytics_scripts.html`
```js
posthog.init('PROJECT_API_KEY', {
  api_host: 'https://ph.trezapp.fr',
  ui_host: 'https://app.posthog.com',
  capture_pageview: true,
  autocapture: true
});
```

## Checklist de tests
- DevTools → Network: declencher un event → requete vers `https://ph.trezapp.fr` → 200 OK.
- Verifier les events dans PostHog (Live Events).
- Verifier toolbar/features UI (ui_host = domaine PostHog).

## Troubleshooting
- SSL fail: cert LetsEncrypt doit inclure `ph.trezapp.fr`.
- 4xx/CORS: verifier CSP `connect-src` et `script-src` (autoriser `https://ph.trezapp.fr`).
- Managed proxy + Cloudflare: CNAME doit etre en `DNS only`.
