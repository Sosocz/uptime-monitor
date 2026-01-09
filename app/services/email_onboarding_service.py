"""
Email onboarding service - J0, J1, J3 automated emails.
"""
from app.core.config import settings


def get_welcome_email_html(user_email: str) -> str:
    """
    J0 email - Welcome email sent immediately after registration.
    """
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ text-align: center; margin-bottom: 30px; }}
        .cta {{ display: inline-block; padding: 14px 28px; background: #2563eb; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: 600; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; font-size: 14px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 Bienvenue sur TrezApp</h1>
        </div>

        <p>Salut,</p>

        <p>Ton compte est créé ! Tu peux maintenant surveiller tes sites 24/7.</p>

        <p><strong>Prochaine étape : ajoute ton premier monitor</strong></p>
        <p>Il te faut moins de 30 secondes :</p>
        <ol>
            <li>Entre l'URL de ton site</li>
            <li>Choisis la fréquence (toutes les 5 min par défaut)</li>
            <li>C'est tout ! On te prévient si ton site tombe.</li>
        </ol>

        <a href="{settings.APP_BASE_URL}/dashboard" class="cta">Ajouter mon premier monitor</a>

        <p>Tu recevras une alerte email dès qu'on détecte un problème.</p>

        <div class="footer">
            <p>Des questions ? Réponds à cet email.<br>
            — L'équipe TrezApp</p>
        </div>
    </div>
</body>
</html>
"""


def get_j1_reminder_email_html(user_email: str, has_monitors: bool) -> str:
    """
    J+1 email - Reminder to activate notifications.
    """
    if not has_monitors:
        # User hasn't added monitors yet
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .cta {{ display: inline-block; padding: 14px 28px; background: #2563eb; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: 600; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; font-size: 14px; color: #666; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Tu n'as pas encore ajouté de monitor 🤔</h2>

        <p>Pas de souci, on te relance juste au cas où.</p>

        <p>Pourquoi créer un monitor ?</p>
        <ul>
            <li>Détection automatique si ton site tombe</li>
            <li>Alertes immédiates par email/Telegram</li>
            <li>Stats uptime & historique</li>
        </ul>

        <a href="{settings.APP_BASE_URL}/dashboard" class="cta">Ajouter mon premier monitor (30s)</a>

        <div class="footer">
            <p>Besoin d'aide ? Réponds à cet email.<br>
            — L'équipe TrezApp</p>
        </div>
    </div>
</body>
</html>
"""
    else:
        # User has monitors, encourage notifications
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .cta {{ display: inline-block; padding: 14px 28px; background: #2563eb; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: 600; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; font-size: 14px; color: #666; }}
        .tip {{ background: #f0f9ff; padding: 15px; border-radius: 6px; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>👍 Ton monitor est en place</h2>

        <p>Super ! Ton site est maintenant surveillé 24/7.</p>

        <div class="tip">
            <strong>💡 Astuce : Active Telegram pour des alertes instantanées</strong>
            <p>Tu reçois déjà des emails, mais Telegram c'est plus rapide (notification mobile immédiate).</p>
        </div>

        <p><strong>Comment activer Telegram ?</strong></p>
        <ol>
            <li>Ouvre Telegram et cherche <code>@TrezAppBot</code></li>
            <li>Envoie <code>/start</code></li>
            <li>Copie ton Chat ID et colle-le dans tes paramètres TrezApp</li>
        </ol>

        <a href="{settings.APP_BASE_URL}/settings" class="cta">Configurer Telegram</a>

        <div class="footer">
            <p>Des questions ? Réponds à cet email.<br>
            — L'équipe TrezApp</p>
        </div>
    </div>
</body>
</html>
"""


def get_j3_reminder_email_html(user_email: str, has_status_page: bool) -> str:
    """
    J+3 email - Reminder to create a status page.
    """
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .cta {{ display: inline-block; padding: 14px 28px; background: #2563eb; color: white; text-decoration: none; border-radius: 6px; margin: 20px 0; font-weight: 600; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; font-size: 14px; color: #666; }}
        .benefit {{ background: #f0fdf4; padding: 15px; border-radius: 6px; margin: 15px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>📊 Crée une status page publique</h2>

        <p>Tu surveilles tes sites. Et si tu partageais l'uptime avec tes clients ?</p>

        <div class="benefit">
            <strong>Pourquoi créer une status page ?</strong>
            <ul>
                <li>Transparence totale avec tes clients/users</li>
                <li>Réduis les tickets support ("Le site marche ?")</li>
                <li>Affiche ton uptime 99.9%+ (preuve de fiabilité)</li>
            </ul>
        </div>

        <p><strong>Création en 2 clics :</strong></p>
        <ol>
            <li>Choisis les monitors à afficher</li>
            <li>Personnalise le titre</li>
            <li>Partage l'URL publique</li>
        </ol>

        <a href="{settings.APP_BASE_URL}/status-pages" class="cta">Créer ma status page</a>

        <p style="font-size: 14px; color: #666;">Exemple : <a href="{settings.APP_BASE_URL}/status/demo">status.tonsite.com</a></p>

        <div class="footer">
            <p>Des questions ? Réponds à cet email.<br>
            — L'équipe TrezApp</p>
        </div>
    </div>
</body>
</html>
"""
