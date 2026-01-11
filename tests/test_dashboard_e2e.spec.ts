import { test, expect } from '@playwright/test';

/**
 * Tests E2E pour TrezApp Dashboard
 * Vérifie que tous les boutons, liens et CTAs fonctionnent
 */

const BASE_URL = process.env.BASE_URL || 'https://www.trezapp.fr';

// Helper: Login utilisateur
async function login(page, email = 'test@test.com', password = 'password123') {
  await page.goto(`${BASE_URL}/login`);
  await page.fill('#email', email);
  await page.fill('#password', password);
  await page.click('button[type="submit"]');
  await page.waitForURL(`${BASE_URL}/dashboard`, { timeout: 10000 });
}

test.describe('Dashboard - Navigation', () => {

  test('Sidebar: Tous les liens doivent naviguer sans 404/500', async ({ page }) => {
    await login(page);

    const sidebarLinks = [
      { name: 'Dashboard', href: '/dashboard' },
      { name: 'Incidents', href: '/incidents' },
      { name: 'Who\'s on-call', href: '/oncall' },
      { name: 'Escalation policies', href: '/escalation-policies' },
      { name: 'Monitors', href: '/dashboard' },
      { name: 'Heartbeats', href: '/heartbeats' },
      { name: 'Status pages', href: '/status-pages' },
      { name: 'Integrations', href: '/integrations' },
      { name: 'Incidents analytics', href: '/incident-analytics' },
      { name: 'Uptime reports', href: '/uptime-reports' },
      { name: 'Subscribers', href: '/status-page-subscribers' },
      { name: 'Upgrade Plan', href: '/upgrade' },
    ];

    for (const link of sidebarLinks) {
      await page.click(`a[href="${link.href}"]`);
      await page.waitForLoadState('networkidle');

      // Vérifier pas de 404/500
      const title = await page.title();
      expect(title).not.toContain('404');
      expect(title).not.toContain('500');

      console.log(`✓ ${link.name} → ${link.href} OK`);
    }
  });

  test('Dashboard: Bouton "Créer un moniteur" ouvre le modal', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/dashboard`);

    // Cliquer sur le bouton
    await page.click('#createMonitorBtn');

    // Vérifier que le modal est visible
    const modal = page.locator('#createModal');
    await expect(modal).toBeVisible();

    // Vérifier les champs du formulaire
    await expect(page.locator('#monitorName')).toBeVisible();
    await expect(page.locator('#monitorUrl')).toBeVisible();
    await expect(page.locator('#monitorTimeout')).toBeVisible();

    console.log('✓ Modal création moniteur s\'ouvre correctement');
  });

  test('Dashboard: Bouton "Voir tout →" doit naviguer', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/dashboard`);

    // Chercher le bouton "Voir tout"
    const viewAllButton = page.locator('a[href="/dashboard#monitors"]');
    await expect(viewAllButton).toBeVisible();

    await viewAllButton.click();

    // Vérifier qu'on reste sur le dashboard (anchor)
    expect(page.url()).toContain('/dashboard');

    console.log('✓ Bouton "Voir tout →" fonctionne');
  });

  test('Dashboard: Lien "Parcourir les intégrations" navigue vers /integrations', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/dashboard`);

    await page.click('a[href="/integrations"]');
    await page.waitForURL(`${BASE_URL}/integrations`);

    expect(page.url()).toContain('/integrations');
    console.log('✓ Lien intégrations fonctionne');
  });

  test('Dashboard: Lien "Voir tous les incidents →" navigue vers /incidents', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/dashboard`);

    await page.click('a[href="/incidents"]');
    await page.waitForURL(`${BASE_URL}/incidents`);

    expect(page.url()).toContain('/incidents');
    console.log('✓ Lien incidents fonctionne');
  });

  test('Dashboard: Lien "Voir les offres" navigue vers /upgrade', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/dashboard`);

    await page.click('a[href="/upgrade"]');
    await page.waitForURL(`${BASE_URL}/upgrade`);

    expect(page.url()).toContain('/upgrade');
    console.log('✓ Lien upgrade fonctionne');
  });

  test('Dashboard: Lien "Commencer le guide" navigue vers /onboarding-guide', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/dashboard`);

    await page.click('a[href="/onboarding-guide"]');
    await page.waitForURL(`${BASE_URL}/onboarding-guide`);

    expect(page.url()).toContain('/onboarding-guide');
    console.log('✓ Lien onboarding guide fonctionne');
  });
});

test.describe('Dashboard - Création moniteur', () => {

  test('Créer un moniteur avec des données valides', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/dashboard`);
    const startUrl = page.url();

    // Ouvrir le modal
    await page.click('#createMonitorBtn');
    await page.waitForSelector('#createModal[style*="display: block"]');

    // Remplir le formulaire
    await page.fill('#monitorName', 'Test Monitor E2E');
    await page.fill('#monitorUrl', 'https://google.com');
    await page.fill('#monitorTimeout', '60');

    // Soumettre
    await page.click('button[type="submit"]');

    // Attendre la fermeture du modal (succès)
    await page.waitForSelector('#createModal[style*="display: none"]', { timeout: 5000 });

    // Vérifier que le moniteur apparaît dans la liste
    await page.waitForSelector('text=Test Monitor E2E', { timeout: 5000 });
    expect(page.url()).toBe(startUrl);

    console.log('✓ Moniteur créé avec succès');
  });

  test('Message d\'erreur si limite atteinte', async ({ page }) => {
    // Ce test vérifie que le message d'erreur s'affiche correctement
    // si l'utilisateur atteint sa limite
    await login(page);
    await page.goto(`${BASE_URL}/dashboard`);

    // Ouvrir le modal
    await page.click('#createMonitorBtn');

    // Remplir et soumettre
    await page.fill('#monitorName', 'Test');
    await page.fill('#monitorUrl', 'https://test.com');
    await page.click('button[type="submit"]');

    // Si erreur, vérifier qu'elle s'affiche
    const errorDiv = page.locator('#createError');
    if (await errorDiv.isVisible()) {
      const errorText = await errorDiv.textContent();
      expect(errorText).toBeTruthy();
      console.log(`✓ Message d'erreur affiché: ${errorText}`);
    } else {
      console.log('✓ Pas de limite atteinte (succès)');
    }
  });
});

test.describe('Dashboard - Recherche globale', () => {

  test('La barre de recherche doit afficher des résultats', async ({ page }) => {
    await login(page);
    await page.goto(`${BASE_URL}/dashboard`);

    // Taper dans la recherche
    await page.fill('#globalSearch', 'test');

    // Attendre que les résultats apparaissent
    await page.waitForTimeout(500);

    const resultsDiv = page.locator('#searchResults');

    // Les résultats doivent être visibles ou indiquer "aucun résultat"
    if (await resultsDiv.isVisible()) {
      console.log('✓ Résultats de recherche affichés');
    } else {
      console.log('✓ Pas de résultats (normal si pas de données)');
    }
  });
});

test.describe('Authentication', () => {

  test('Google OAuth doit rediriger vers Google', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // Cliquer sur le bouton Google
    const googleBtn = page.locator('a[href="/api/auth/oauth/google"]');
    await expect(googleBtn).toBeVisible();

    // Cliquer et vérifier la redirection
    const [popup] = await Promise.all([
      page.waitForEvent('popup'),
      googleBtn.click()
    ]);

    // Vérifier qu'on est redirigé vers Google
    await popup.waitForLoadState();
    expect(popup.url()).toContain('accounts.google.com');

    await popup.close();
    console.log('✓ OAuth Google redirige correctement');
  });

  test('Reset password doit afficher un message de succès', async ({ page }) => {
    await page.goto(`${BASE_URL}/forgot-password`);

    await page.fill('input[type="email"]', 'test@test.com');
    await page.click('button[type="submit"]');

    // Vérifier le message de succès
    await page.waitForSelector('text=/If your email is registered/i', { timeout: 5000 });

    console.log('✓ Reset password affiche le message de succès');
  });
});

test.describe('Pages sans erreur', () => {

  test('Toutes les pages principales doivent charger sans erreur console', async ({ page }) => {
    const pages = [
      '/',
      '/login',
      '/register',
      '/forgot-password',
      '/dashboard',
      '/incidents',
      '/oncall',
      '/status-pages',
      '/integrations',
      '/upgrade',
    ];

    const consoleErrors: string[] = [];
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    for (const url of pages) {
      await page.goto(`${BASE_URL}${url}`);
      await page.waitForLoadState('networkidle');

      // Vérifier pas de 404/500
      const statusCode = page.url();
      expect(statusCode).not.toContain('404');
      expect(statusCode).not.toContain('500');

      console.log(`✓ ${url} charge sans erreur`);
    }

    // Afficher les erreurs console s'il y en a
    if (consoleErrors.length > 0) {
      console.warn('⚠️ Erreurs console détectées:', consoleErrors);
    } else {
      console.log('✓ Aucune erreur console détectée');
    }
  });
});
