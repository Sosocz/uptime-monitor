#!/usr/bin/env python3
"""
Script to generate SEO landing pages quickly from templates.

Usage:
    python scripts/generate_seo_page.py --type use-case --slug woocommerce
    python scripts/generate_seo_page.py --type comparison --slug pingdom
"""

import argparse
import os
from pathlib import Path


USE_CASE_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Surveillance 24/7 | TrezApp</title>
    <meta name="description" content="{meta_description}">
    <link rel="canonical" href="https://trezapp.com/use-cases/{slug}">

    <!-- Open Graph -->
    <meta property="og:title" content="{title} - Surveillance 24/7">
    <meta property="og:description" content="{meta_description}">
    <meta property="og:url" content="https://trezapp.com/use-cases/{slug}">
    <meta property="og:type" content="website">

    <link rel="stylesheet" href="/static/css/styles.css">
</head>
<body>
    <header>
        <nav class="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
            <a href="/" class="text-2xl font-bold gradient-text">TrezApp</a>
            <div class="space-x-6">
                <a href="/pricing" class="text-gray-300 hover:text-white">Pricing</a>
                <a href="/login" class="text-gray-300 hover:text-white">Login</a>
                <a href="/register" class="liquid-btn">Start Free</a>
            </div>
        </nav>
    </header>

    <main class="max-w-4xl mx-auto px-4 py-12">
        <div class="text-center mb-12">
            <h1 class="text-5xl font-bold mb-4 gradient-text">{h1}</h1>
            <p class="text-xl text-gray-300">{subtitle}</p>
        </div>

        <section class="mb-12">
            <h2 class="text-3xl font-bold mb-6">Pourquoi surveiller {tech_name} ?</h2>
            <div class="grid md:grid-cols-3 gap-6">
                {why_cards}
            </div>
        </section>

        <section class="mb-12">
            <h2 class="text-3xl font-bold mb-6">TrezApp pour {tech_name}</h2>
            <div class="space-y-4">
                {features}
            </div>
        </section>

        <section class="mb-12 bg-gradient-to-r from-purple-900 to-blue-900 p-8 rounded-xl">
            <h2 class="text-3xl font-bold mb-6 text-center">Comment ça marche ?</h2>
            <div class="grid md:grid-cols-3 gap-6">
                <div class="text-center">
                    <div class="text-4xl mb-4">🔗</div>
                    <h3 class="text-xl font-bold mb-2">1. Ajoutez votre site</h3>
                    <p class="text-gray-300">Entrez l'URL de votre site {tech_name}</p>
                </div>
                <div class="text-center">
                    <div class="text-4xl mb-4">⚡</div>
                    <h3 class="text-xl font-bold mb-2">2. On surveille 24/7</h3>
                    <p class="text-gray-300">Checks toutes les 5 minutes (ou 1 min sur PRO)</p>
                </div>
                <div class="text-center">
                    <div class="text-4xl mb-4">🔔</div>
                    <h3 class="text-xl font-bold mb-2">3. Alertes instantanées</h3>
                    <p class="text-gray-300">Email + Telegram dès qu'un problème survient</p>
                </div>
            </div>
        </section>

        <section class="mb-12">
            <h2 class="text-3xl font-bold mb-6">Pricing</h2>
            <div class="grid md:grid-cols-2 gap-6">
                <div class="bg-gray-800 p-6 rounded-xl">
                    <h3 class="text-2xl font-bold mb-2">FREE</h3>
                    <div class="text-4xl font-bold mb-4">€0<span class="text-lg">/mois</span></div>
                    <ul class="space-y-2 mb-6">
                        <li>✅ 10 monitors</li>
                        <li>✅ Checks 5 minutes</li>
                        <li>✅ Alertes email</li>
                        <li>✅ Status pages publiques</li>
                    </ul>
                    <a href="/register" class="block text-center bg-purple-600 hover:bg-purple-700 text-white py-3 rounded-lg">
                        Commencer gratuitement
                    </a>
                </div>
                <div class="bg-gradient-to-br from-purple-900 to-blue-900 p-6 rounded-xl border-2 border-purple-500">
                    <div class="text-xs bg-purple-500 text-white px-3 py-1 rounded-full inline-block mb-2">POPULAIRE</div>
                    <h3 class="text-2xl font-bold mb-2">PRO</h3>
                    <div class="text-4xl font-bold mb-4">€19<span class="text-lg">/mois</span></div>
                    <ul class="space-y-2 mb-6">
                        <li>✅ Monitors illimités</li>
                        <li>✅ Checks 1 minute</li>
                        <li>✅ Telegram alerts</li>
                        <li>✅ White-label status pages</li>
                        <li>✅ Webhooks</li>
                    </ul>
                    <a href="/register" class="block text-center bg-white text-purple-900 font-bold py-3 rounded-lg hover:bg-gray-100">
                        Démarrer PRO
                    </a>
                </div>
            </div>
        </section>

        <section class="bg-gray-800 p-8 rounded-xl mb-12">
            <h2 class="text-2xl font-bold mb-4">Autres cas d'usage</h2>
            <div class="grid md:grid-cols-4 gap-4">
                <a href="/use-cases/wordpress" class="text-purple-400 hover:text-purple-300">→ WordPress</a>
                <a href="/use-cases/shopify" class="text-purple-400 hover:text-purple-300">→ Shopify</a>
                <a href="/use-cases/saas" class="text-purple-400 hover:text-purple-300">→ SaaS</a>
                <a href="/use-cases/agencies" class="text-purple-400 hover:text-purple-300">→ Agences</a>
            </div>
            <h3 class="text-xl font-bold mt-6 mb-4">Comparer avec d'autres outils</h3>
            <div class="grid md:grid-cols-3 gap-4">
                <a href="/vs/uptimerobot" class="text-purple-400 hover:text-purple-300">TrezApp vs UptimeRobot</a>
                <a href="/vs/betteruptime" class="text-purple-400 hover:text-purple-300">TrezApp vs Better Uptime</a>
                <a href="/vs/pingdom" class="text-purple-400 hover:text-purple-300">TrezApp vs Pingdom</a>
            </div>
        </section>

        <section class="text-center py-12">
            <h2 class="text-4xl font-bold mb-6">Commencez maintenant</h2>
            <p class="text-xl text-gray-300 mb-8">Setup en 30 secondes. Aucune carte bancaire requise.</p>
            <a href="/register" class="liquid-btn text-xl px-12 py-4">
                Créer mon compte gratuit →
            </a>
        </section>
    </main>

    <footer class="bg-gray-900 mt-12 py-8">
        <div class="max-w-7xl mx-auto px-4 text-center text-gray-400">
            <p>&copy; 2026 TrezApp. All rights reserved.</p>
        </div>
    </footer>
</body>
</html>
"""


COMPARISON_TEMPLATE = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TrezApp vs {competitor} - Comparaison 2026 | TrezApp</title>
    <meta name="description" content="{meta_description}">
    <link rel="canonical" href="https://trezapp.com/vs/{slug}">

    <!-- Open Graph -->
    <meta property="og:title" content="TrezApp vs {competitor} - Comparaison">
    <meta property="og:description" content="{meta_description}">
    <meta property="og:url" content="https://trezapp.com/vs/{slug}">
    <meta property="og:type" content="website">

    <link rel="stylesheet" href="/static/css/styles.css">
</head>
<body>
    <header>
        <nav class="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
            <a href="/" class="text-2xl font-bold gradient-text">TrezApp</a>
            <div class="space-x-6">
                <a href="/pricing" class="text-gray-300 hover:text-white">Pricing</a>
                <a href="/login" class="text-gray-300 hover:text-white">Login</a>
                <a href="/register" class="liquid-btn">Start Free</a>
            </div>
        </nav>
    </header>

    <main class="max-w-6xl mx-auto px-4 py-12">
        <div class="text-center mb-12">
            <h1 class="text-5xl font-bold mb-4 gradient-text">TrezApp vs {competitor}</h1>
            <p class="text-xl text-gray-300">{subtitle}</p>
        </div>

        <section class="mb-12">
            <h2 class="text-3xl font-bold mb-6">Comparaison des fonctionnalités</h2>
            <div class="overflow-x-auto">
                <table class="w-full bg-gray-800 rounded-xl">
                    <thead>
                        <tr class="border-b border-gray-700">
                            <th class="p-4 text-left">Fonctionnalité</th>
                            <th class="p-4 text-center bg-purple-900">TrezApp</th>
                            <th class="p-4 text-center">{competitor}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {comparison_rows}
                    </tbody>
                </table>
            </div>
        </section>

        <section class="mb-12">
            <h2 class="text-3xl font-bold mb-6">Pricing</h2>
            <div class="grid md:grid-cols-2 gap-6">
                <div class="bg-gradient-to-br from-purple-900 to-blue-900 p-6 rounded-xl border-2 border-purple-500">
                    <h3 class="text-2xl font-bold mb-2">TrezApp FREE</h3>
                    <div class="text-4xl font-bold mb-4">€0<span class="text-lg">/mois</span></div>
                    <ul class="space-y-2">
                        <li>✅ 10 monitors</li>
                        <li>✅ 5-min checks</li>
                        <li>✅ Status pages</li>
                    </ul>
                </div>
                <div class="bg-gray-800 p-6 rounded-xl">
                    <h3 class="text-2xl font-bold mb-2">{competitor} FREE</h3>
                    <div class="text-4xl font-bold mb-4">{competitor_free_price}</div>
                    <ul class="space-y-2 text-gray-400">
                        {competitor_free_features}
                    </ul>
                </div>
            </div>
        </section>

        <section class="bg-gradient-to-r from-purple-900 to-blue-900 p-8 rounded-xl mb-12">
            <h2 class="text-3xl font-bold mb-6">Pourquoi choisir TrezApp ?</h2>
            <div class="grid md:grid-cols-3 gap-6">
                {why_trezapp}
            </div>
        </section>

        <section class="text-center py-12">
            <h2 class="text-4xl font-bold mb-6">Essayez TrezApp gratuitement</h2>
            <p class="text-xl text-gray-300 mb-8">Setup en 30 secondes. Aucune carte bancaire requise.</p>
            <a href="/register" class="liquid-btn text-xl px-12 py-4">
                Créer mon compte gratuit →
            </a>
        </section>
    </main>

    <footer class="bg-gray-900 mt-12 py-8">
        <div class="max-w-7xl mx-auto px-4 text-center text-gray-400">
            <p>&copy; 2026 TrezApp. All rights reserved.</p>
        </div>
    </footer>
</body>
</html>
"""


def generate_use_case_page(slug: str, data: dict):
    """Generate a use case page from template."""
    # Build why cards
    why_cards = "\n".join([
        f"""<div class="bg-gray-800 p-6 rounded-xl">
                    <h3 class="text-xl font-bold mb-2">{card['title']}</h3>
                    <p class="text-gray-300">{card['description']}</p>
                </div>"""
        for card in data['why_cards']
    ])

    # Build features
    features = "\n".join([
        f"""<div class="bg-gray-800 p-4 rounded-lg">
                    <h3 class="text-lg font-bold mb-2">✅ {feature['title']}</h3>
                    <p class="text-gray-300">{feature['description']}</p>
                </div>"""
        for feature in data['features']
    ])

    html = USE_CASE_TEMPLATE.format(
        slug=slug,
        title=data['title'],
        meta_description=data['meta_description'],
        h1=data['h1'],
        subtitle=data['subtitle'],
        tech_name=data['tech_name'],
        why_cards=why_cards,
        features=features
    )

    return html


def generate_comparison_page(slug: str, data: dict):
    """Generate a comparison page from template."""
    # Build comparison rows
    comparison_rows = "\n".join([
        f"""<tr class="border-b border-gray-700">
                            <td class="p-4">{row['feature']}</td>
                            <td class="p-4 text-center bg-purple-900">{row['trezapp']}</td>
                            <td class="p-4 text-center text-gray-400">{row['competitor']}</td>
                        </tr>"""
        for row in data['comparison_rows']
    ])

    # Build why TrezApp cards
    why_trezapp = "\n".join([
        f"""<div class="text-center">
                    <div class="text-4xl mb-4">{card['icon']}</div>
                    <h3 class="text-xl font-bold mb-2">{card['title']}</h3>
                    <p class="text-gray-300">{card['description']}</p>
                </div>"""
        for card in data['why_trezapp']
    ])

    html = COMPARISON_TEMPLATE.format(
        slug=slug,
        competitor=data['competitor'],
        meta_description=data['meta_description'],
        subtitle=data['subtitle'],
        comparison_rows=comparison_rows,
        competitor_free_price=data['competitor_free_price'],
        competitor_free_features=data['competitor_free_features'],
        why_trezapp=why_trezapp
    )

    return html


# Predefined data for common pages
USE_CASE_DATA = {
    "woocommerce": {
        "title": "Monitoring WooCommerce",
        "meta_description": "Surveillez votre boutique WooCommerce 24/7. Alertes instantanées si votre site e-commerce tombe. Uptime 99.9% garanti.",
        "h1": "Monitoring Uptime WooCommerce",
        "subtitle": "Surveillez votre boutique e-commerce 24/7 et ne perdez plus jamais de ventes",
        "tech_name": "WooCommerce",
        "why_cards": [
            {"title": "🛒 Évitez les ventes perdues", "description": "1h de downtime = centaines d'€ perdus. Soyez alerté instantanément."},
            {"title": "⚡ Détection rapide", "description": "Checks toutes les 5 minutes (1 min sur PRO) pour détecter les problèmes avant vos clients."},
            {"title": "📊 Status page publique", "description": "Rassurez vos clients avec une page publique affichant votre uptime 99.9%."}
        ],
        "features": [
            {"title": "Surveillance 24/7", "description": "TrezApp vérifie votre boutique WooCommerce toutes les 5 minutes, jour et nuit."},
            {"title": "Alertes Telegram", "description": "Recevez des notifications instantanées sur votre mobile si votre site tombe."},
            {"title": "Status page brandée", "description": "Partagez votre uptime avec vos clients via une page publique à vos couleurs."},
            {"title": "Historique 90 jours", "description": "Consultez l'historique complet de votre uptime et temps de réponse."}
        ]
    },
    "prestashop": {
        "title": "Monitoring PrestaShop",
        "meta_description": "Surveillez votre boutique PrestaShop 24/7. Alertes instantanées en cas de downtime. Garantissez 99.9% d'uptime.",
        "h1": "Monitoring Uptime PrestaShop",
        "subtitle": "Ne perdez plus de ventes à cause de downtime non détecté",
        "tech_name": "PrestaShop",
        "why_cards": [
            {"title": "💰 Protégez votre CA", "description": "Chaque minute de downtime = ventes perdues. Détectez les problèmes en 1 minute."},
            {"title": "🔔 Alertes multi-canaux", "description": "Email + Telegram pour être sûr de ne jamais manquer une alerte."},
            {"title": "📈 Uptime 99.9%", "description": "Trackez votre uptime et prouvez votre fiabilité à vos clients."}
        ],
        "features": [
            {"title": "Checks 1 minute", "description": "Plan PRO avec vérifications toutes les 60 secondes pour détecter tout problème instantanément."},
            {"title": "Multi-sites", "description": "Surveillez plusieurs boutiques PrestaShop depuis un seul dashboard."},
            {"title": "Incidents automatiques", "description": "Créez automatiquement des rapports d'incidents avec durée et cause."},
            {"title": "Intégration facile", "description": "Aucun plugin à installer. Juste l'URL de votre boutique."}
        ]
    }
}

COMPARISON_DATA = {
    "pingdom": {
        "competitor": "Pingdom",
        "meta_description": "Comparez TrezApp vs Pingdom : fonctionnalités, pricing, facilité d'utilisation. Voyez pourquoi des utilisateurs choisissent TrezApp.",
        "subtitle": "Alternative simple et abordable à Pingdom",
        "comparison_rows": [
            {"feature": "FREE Plan", "trezapp": "✅ 10 monitors", "competitor": "❌ No free plan"},
            {"feature": "Check interval", "trezapp": "1 min (PRO)", "competitor": "1 min (from $15/month)"},
            {"feature": "Status pages", "trezapp": "✅ FREE", "competitor": "❌ Not included"},
            {"feature": "Telegram alerts", "trezapp": "✅ Built-in", "competitor": "❌ Only email/SMS"},
            {"feature": "Pricing", "trezapp": "€19/month PRO", "competitor": "From $15/month"},
        ],
        "competitor_free_price": "From $15/mo",
        "competitor_free_features": "<li>❌ No free plan</li><li>❌ Expensive</li>",
        "why_trezapp": [
            {"icon": "🎁", "title": "FREE plan généreux", "description": "10 monitors gratuits vs 0 chez Pingdom"},
            {"icon": "💰", "title": "Plus abordable", "description": "€19/mois vs $15+ chez Pingdom"},
            {"icon": "⚡", "title": "Setup instant", "description": "30 secondes vs configuration complexe"}
        ]
    }
}


def main():
    parser = argparse.ArgumentParser(description="Generate SEO landing pages")
    parser.add_argument("--type", choices=["use-case", "comparison"], required=True)
    parser.add_argument("--slug", required=True, help="URL slug (e.g., woocommerce, pingdom)")

    args = parser.parse_args()

    # Get template data
    if args.type == "use-case":
        if args.slug not in USE_CASE_DATA:
            print(f"❌ No data for use-case '{args.slug}'")
            print(f"Available: {', '.join(USE_CASE_DATA.keys())}")
            return

        html = generate_use_case_page(args.slug, USE_CASE_DATA[args.slug])
        output_dir = Path("app/templates/seo")
        output_file = output_dir / f"{args.slug}.html"

    else:  # comparison
        if args.slug not in COMPARISON_DATA:
            print(f"❌ No data for comparison '{args.slug}'")
            print(f"Available: {', '.join(COMPARISON_DATA.keys())}")
            return

        html = generate_comparison_page(args.slug, COMPARISON_DATA[args.slug])
        output_dir = Path("app/templates/seo")
        output_file = output_dir / f"vs-{args.slug}.html"

    # Create directory if not exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"✅ Generated: {output_file}")
    print(f"📝 Add route in app/api/seo_pages.py:")
    if args.type == "use-case":
        print(f'@router.get("/use-cases/{args.slug}")')
        print(f'async def {args.slug.replace("-", "_")}():')
        print(f'    return templates.TemplateResponse("{args.slug}.html", {{"request": Request}})')
    else:
        print(f'@router.get("/vs/{args.slug}")')
        print(f'async def vs_{args.slug.replace("-", "_")}():')
        print(f'    return templates.TemplateResponse("vs-{args.slug}.html", {{"request": Request}})')


if __name__ == "__main__":
    main()
