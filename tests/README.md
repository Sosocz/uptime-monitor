# Tests E2E Playwright - TrezApp

## Installation

```bash
npm install
npx playwright install chromium
```

## Exécution des tests

### Tous les tests
```bash
npm test
```

### Tests en mode interactif (UI)
```bash
npm run test:ui
```

### Tests avec navigateur visible
```bash
npm run test:headed
```

### Debug un test spécifique
```bash
npm run test:debug tests/test_dashboard_e2e.spec.ts
```

## Rapport HTML
```bash
npm run report
```

## Variables d'environnement

- `BASE_URL`: URL de l'application à tester (défaut: https://www.trezapp.fr)

```bash
BASE_URL=http://localhost:8000 npm test
```

## Couverture des tests

### ✅ Navigation
- Tous les liens de la sidebar
- Boutons CTA du dashboard
- Links "Voir tout →", "Parcourir les intégrations", etc.

### ✅ Fonctionnalités
- Création de moniteur (modal + soumission)
- Recherche globale
- Google OAuth (redirection)
- Reset password (message succès)

### ✅ Qualité
- Pas d'erreurs 404/500
- Pas d'erreurs console JavaScript
- Tous les boutons/liens fonctionnels

## Résultats attendus

**TOUS LES TESTS DOIVENT PASSER (0 fail)** avant de livrer en production.

Si un test échoue:
1. Vérifier les logs Playwright
2. Consulter le screenshot dans `test-results/`
3. Corriger le bug
4. Relancer les tests
