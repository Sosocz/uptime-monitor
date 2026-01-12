"""
SEO landing pages - use case and comparison pages for organic traffic.
"""
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.web.template_context import apply_template_globals
import os

router = APIRouter()

# Setup Jinja2 templates
templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
templates = Jinja2Templates(directory=templates_dir)
apply_template_globals(templates)


@router.get("/use-cases/wordpress", response_class=HTMLResponse, tags=["seo"])
async def wordpress_monitoring(request: Request):
    """WordPress uptime monitoring landing page."""
    return templates.TemplateResponse("seo/wordpress.html", {
        "request": request,
        "title": "WordPress Uptime Monitoring - Surveillance 24/7 de votre site",
        "description": "Surveillez votre site WordPress 24/7. Alertes instantanées par email et Telegram en cas de panne. Uptime 99.9% garanti."
    })


@router.get("/use-cases/shopify", response_class=HTMLResponse, tags=["seo"])
async def shopify_monitoring(request: Request):
    """Shopify store monitoring landing page."""
    return templates.TemplateResponse("seo/shopify.html", {
        "request": request,
        "title": "Shopify Store Monitoring - Évitez les pertes de ventes",
        "description": "Surveillez votre boutique Shopify 24/7. Détectez les pannes avant vos clients. Évitez les pertes de revenus."
    })


@router.get("/use-cases/saas", response_class=HTMLResponse, tags=["seo"])
async def saas_monitoring(request: Request):
    """SaaS application monitoring landing page."""
    return templates.TemplateResponse("seo/saas.html", {
        "request": request,
        "title": "SaaS Uptime Monitoring - Status Page & Alertes",
        "description": "Monitoring professionnel pour applications SaaS. Status page publique, alertes multi-canal, API checks. Fait pour les startups."
    })


@router.get("/use-cases/agencies", response_class=HTMLResponse, tags=["seo"])
async def agencies_monitoring(request: Request):
    """Web agencies monitoring landing page."""
    return templates.TemplateResponse("seo/agencies.html", {
        "request": request,
        "title": "Monitoring pour Agences Web - Gérez tous vos clients",
        "description": "Solution de monitoring pour agences web. Gérez tous les sites de vos clients depuis un seul dashboard. Branding personnalisé."
    })


@router.get("/vs/uptimerobot", response_class=HTMLResponse, tags=["seo"])
async def vs_uptimerobot(request: Request):
    """TrezApp vs UptimeRobot comparison page."""
    return templates.TemplateResponse("seo/vs-uptimerobot.html", {
        "request": request,
        "title": "TrezApp vs UptimeRobot - Comparaison détaillée 2026",
        "description": "Comparaison complète entre TrezApp et UptimeRobot. Prix, fonctionnalités, limites. Quelle solution choisir en 2026 ?"
    })


@router.get("/vs/betteruptime", response_class=HTMLResponse, tags=["seo"])
async def vs_betteruptime(request: Request):
    """TrezApp vs Better Uptime comparison page."""
    return templates.TemplateResponse("seo/vs-betteruptime.html", {
        "request": request,
        "title": "TrezApp vs Better Uptime - Alternative moins chère",
        "description": "TrezApp comme alternative à Better Uptime. Fonctionnalités similaires à prix réduit. Comparaison complète."
    })


@router.get("/use-cases/woocommerce", response_class=HTMLResponse, tags=["seo"])
async def woocommerce_monitoring(request: Request):
    """WooCommerce store monitoring landing page."""
    return templates.TemplateResponse("seo/woocommerce.html", {
        "request": request,
        "title": "Monitoring WooCommerce - Surveillance 24/7",
        "description": "Surveillez votre boutique WooCommerce 24/7. Alertes instantanées si votre site e-commerce tombe. Uptime 99.9% garanti."
    })


@router.get("/use-cases/prestashop", response_class=HTMLResponse, tags=["seo"])
async def prestashop_monitoring(request: Request):
    """PrestaShop store monitoring landing page."""
    return templates.TemplateResponse("seo/prestashop.html", {
        "request": request,
        "title": "Monitoring PrestaShop - Surveillance 24/7",
        "description": "Surveillez votre boutique PrestaShop 24/7. Alertes instantanées en cas de downtime. Garantissez 99.9% d'uptime."
    })


@router.get("/vs/pingdom", response_class=HTMLResponse, tags=["seo"])
async def vs_pingdom(request: Request):
    """TrezApp vs Pingdom comparison page."""
    return templates.TemplateResponse("seo/vs-pingdom.html", {
        "request": request,
        "title": "TrezApp vs Pingdom - Comparaison 2026",
        "description": "Comparez TrezApp vs Pingdom : fonctionnalités, pricing, facilité d'utilisation. Voyez pourquoi des utilisateurs choisissent TrezApp."
    })
