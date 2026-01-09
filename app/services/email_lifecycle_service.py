"""
Lifecycle email templates for user retention and expansion MRR.

Beyond onboarding (J0/J1/J3), these emails drive:
- Retention: Monthly reports, incident summaries
- Expansion: Upgrade nudges, annual upsell
- Re-engagement: Inactive user campaigns
"""

from datetime import datetime, timedelta
from typing import Dict, List


def get_monthly_report_email(user_email: str, month_data: Dict) -> str:
    """
    Monthly uptime report email (sent on 1st of each month).

    Args:
        month_data: {
            "month": "January 2026",
            "total_uptime": 99.97,
            "incidents_count": 1,
            "most_reliable_site": "example.com",
            "avg_response_time": 245,
            "total_checks": 12500
        }
    """
    is_perfect = month_data["total_uptime"] == 100.0

    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px; text-align: center; }}
        .stat-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin: 20px 0; }}
        .stat-card {{ background: #f8fafc; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-value {{ font-size: 32px; font-weight: bold; color: #667eea; }}
        .stat-label {{ font-size: 14px; color: #64748b; margin-top: 5px; }}
        .cta-button {{ display: inline-block; background: #667eea; color: white; padding: 15px 30px; border-radius: 8px; text-decoration: none; margin: 20px 0; }}
        .footer {{ text-align: center; color: #94a3b8; font-size: 12px; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{'🎉' if is_perfect else '📊'} Your {month_data["month"]} Uptime Report</h1>
            <p>Here's how your sites performed this month</p>
        </div>

        <div style="padding: 20px 0;">
            {'<p style="background: #dcfce7; color: #166534; padding: 15px; border-radius: 8px; text-align: center;"><strong>Perfect month!</strong> All your sites were up 100% of the time. 🚀</p>' if is_perfect else ''}

            <div class="stat-grid">
                <div class="stat-card">
                    <div class="stat-value">{month_data["total_uptime"]}%</div>
                    <div class="stat-label">Average Uptime</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{month_data["incidents_count"]}</div>
                    <div class="stat-label">Incidents</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{month_data["avg_response_time"]}ms</div>
                    <div class="stat-label">Avg Response Time</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value">{month_data["total_checks"]:,}</div>
                    <div class="stat-label">Total Checks</div>
                </div>
            </div>

            <p style="background: #f1f5f9; padding: 15px; border-radius: 8px;">
                <strong>🏆 Most reliable site:</strong> {month_data["most_reliable_site"]}<br>
                <em>This site had {month_data["total_uptime"]}% uptime this month.</em>
            </p>

            <div style="text-align: center; margin: 30px 0;">
                <a href="https://trezapp.com/dashboard" class="cta-button">
                    View Detailed Stats →
                </a>
            </div>

            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0;">

            <p style="color: #64748b; font-size: 14px;">
                💡 <strong>Tip:</strong> Share your uptime with clients using public status pages.
                <a href="https://trezapp.com/dashboard/status-pages" style="color: #667eea;">Create a status page →</a>
            </p>
        </div>

        <div class="footer">
            <p>TrezApp - Uptime Monitoring<br>
            <a href="https://trezapp.com/dashboard/settings" style="color: #94a3b8;">Manage email preferences</a></p>
        </div>
    </div>
</body>
</html>
"""


def get_incident_summary_email(user_email: str, incident_data: Dict) -> str:
    """
    Email sent after an incident is resolved.

    Args:
        incident_data: {
            "site_name": "example.com",
            "downtime_minutes": 45,
            "detection_time_minutes": 2,
            "notifications_sent": 3,
            "error_message": "Connection timeout"
        }
    """
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #10b981; color: white; padding: 20px; border-radius: 8px; text-align: center; }}
        .incident-details {{ background: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .timeline {{ border-left: 3px solid #667eea; padding-left: 20px; margin: 20px 0; }}
        .timeline-item {{ margin-bottom: 15px; }}
        .cta-button {{ display: inline-block; background: #667eea; color: white; padding: 15px 30px; border-radius: 8px; text-decoration: none; margin: 20px 0; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>✅ {incident_data["site_name"]} is back up!</h1>
            <p>Incident resolved after {incident_data["downtime_minutes"]} minutes</p>
        </div>

        <div style="padding: 20px 0;">
            <h2>What happened?</h2>
            <div class="incident-details">
                <p><strong>Error:</strong> {incident_data["error_message"]}</p>
                <p><strong>Total downtime:</strong> {incident_data["downtime_minutes"]} minutes</p>
                <p><strong>Detection time:</strong> {incident_data["detection_time_minutes"]} minutes after outage</p>
                <p><strong>Notifications sent:</strong> {incident_data["notifications_sent"]} (email + Telegram)</p>
            </div>

            <h3>Timeline</h3>
            <div class="timeline">
                <div class="timeline-item">
                    <strong>Site went down</strong><br>
                    <span style="color: #64748b;">Detected automatically</span>
                </div>
                <div class="timeline-item">
                    <strong>{incident_data["detection_time_minutes"]} min later</strong><br>
                    <span style="color: #64748b;">You were notified via email & Telegram</span>
                </div>
                <div class="timeline-item">
                    <strong>{incident_data["downtime_minutes"]} min total</strong><br>
                    <span style="color: #10b981;">Site recovered ✅</span>
                </div>
            </div>

            <div style="text-align: center; margin: 30px 0;">
                <a href="https://trezapp.com/dashboard/incidents" class="cta-button">
                    View Full Incident Report →
                </a>
            </div>

            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0;">

            <p style="background: #fef3c7; padding: 15px; border-radius: 8px; border-left: 4px solid #f59e0b;">
                💡 <strong>Upgrade to PRO for faster detection</strong><br>
                1-minute checks (vs 5-min on FREE) = detect issues 5x faster.<br>
                <a href="https://trezapp.com/pricing" style="color: #f59e0b;">Upgrade now →</a>
            </p>
        </div>
    </div>
</body>
</html>
"""


def get_upgrade_nudge_email(user_email: str, usage_data: Dict) -> str:
    """
    Upgrade email for engaged FREE users.

    Args:
        usage_data: {
            "monitors_count": 8,
            "months_active": 2,
            "alerts_sent": 15,
            "avg_uptime": 99.9
        }
    """
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 8px; text-align: center; }}
        .comparison-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .comparison-table th {{ background: #f1f5f9; padding: 12px; text-align: left; }}
        .comparison-table td {{ padding: 12px; border-bottom: 1px solid #e2e8f0; }}
        .highlight {{ background: #dcfce7; font-weight: bold; }}
        .cta-button {{ display: inline-block; background: #667eea; color: white; padding: 15px 40px; border-radius: 8px; text-decoration: none; font-size: 18px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 You're getting a lot of value from TrezApp!</h1>
            <p>Ready to unlock the full power?</p>
        </div>

        <div style="padding: 20px 0;">
            <p>Hi there,</p>
            <p>You've been using TrezApp for <strong>{usage_data["months_active"]} months</strong>. Here's what you've accomplished:</p>

            <ul style="background: #f8fafc; padding: 20px 20px 20px 40px; border-radius: 8px;">
                <li>Monitored <strong>{usage_data["monitors_count"]} sites</strong> 24/7</li>
                <li>Received <strong>{usage_data["alerts_sent"]} alerts</strong> (catching issues before your users did)</li>
                <li>Maintained <strong>{usage_data["avg_uptime"]}% uptime</strong> across all your sites</li>
            </ul>

            <h2>You're using {usage_data["monitors_count"]}/10 monitors on the FREE plan</h2>
            <p>Upgrade to <strong>PRO</strong> and get:</p>

            <table class="comparison-table">
                <tr>
                    <th>Feature</th>
                    <th>FREE (current)</th>
                    <th class="highlight">PRO</th>
                </tr>
                <tr>
                    <td>Monitors</td>
                    <td>10 max</td>
                    <td class="highlight">Unlimited</td>
                </tr>
                <tr>
                    <td>Check interval</td>
                    <td>5 minutes</td>
                    <td class="highlight">1 minute (5x faster)</td>
                </tr>
                <tr>
                    <td>Telegram alerts</td>
                    <td>✅</td>
                    <td class="highlight">✅</td>
                </tr>
                <tr>
                    <td>Status pages</td>
                    <td>With "Powered by" badge</td>
                    <td class="highlight">White-label (your brand)</td>
                </tr>
                <tr>
                    <td>Webhooks</td>
                    <td>❌</td>
                    <td class="highlight">✅ 5 webhooks</td>
                </tr>
            </table>

            <div style="text-align: center; margin: 40px 0;">
                <a href="https://trezapp.com/pricing?upgrade=usage" class="cta-button">
                    Upgrade to PRO - €19/month →
                </a>
                <p style="color: #64748b; margin-top: 10px;">Cancel anytime, no questions asked</p>
            </div>

            <div style="background: #fef3c7; padding: 15px; border-radius: 8px; border-left: 4px solid #f59e0b; margin: 20px 0;">
                🎁 <strong>Special offer:</strong> Use code <code style="background: white; padding: 2px 8px; border-radius: 4px;">LOYAL20</code> for 20% off your first 3 months (€15.20/month instead of €19)
            </div>

            <p style="color: #64748b; font-size: 14px;">
                Questions? Just reply to this email - it goes straight to me.<br>
                <em>- Founder, TrezApp</em>
            </p>
        </div>
    </div>
</body>
</html>
"""


def get_annual_upsell_email(user_email: str, months_on_monthly: int) -> str:
    """
    Email to monthly PRO users encouraging annual switch.

    Args:
        months_on_monthly: How many months they've been on monthly billing
    """
    monthly_cost = 19 * 12  # €228/year
    annual_cost = 180  # €180/year
    savings = monthly_cost - annual_cost

    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #10b981; color: white; padding: 30px; border-radius: 8px; text-align: center; }}
        .savings-box {{ background: #dcfce7; border: 2px solid #10b981; padding: 30px; border-radius: 8px; text-align: center; margin: 30px 0; }}
        .savings-amount {{ font-size: 48px; font-weight: bold; color: #10b981; }}
        .cta-button {{ display: inline-block; background: #10b981; color: white; padding: 15px 40px; border-radius: 8px; text-decoration: none; font-size: 18px; }}
        .comparison {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 30px 0; }}
        .plan-card {{ background: #f8fafc; padding: 20px; border-radius: 8px; text-align: center; }}
        .plan-card.annual {{ background: #dcfce7; border: 2px solid #10b981; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>💰 Save €{savings}/year with annual billing</h1>
            <p>You've been on PRO for {months_on_monthly} months - thank you!</p>
        </div>

        <div style="padding: 20px 0;">
            <p>Hi there,</p>
            <p>Loving TrezApp PRO? Switch to <strong>annual billing</strong> and save money:</p>

            <div class="savings-box">
                <div class="savings-amount">€{savings}</div>
                <div style="font-size: 18px; color: #166534; margin-top: 10px;">
                    saved per year (20% off)
                </div>
            </div>

            <div class="comparison">
                <div class="plan-card">
                    <h3>Monthly</h3>
                    <div style="font-size: 14px; color: #64748b;">Current plan</div>
                    <div style="font-size: 32px; font-weight: bold; margin: 10px 0;">€19</div>
                    <div style="font-size: 14px; color: #64748b;">per month</div>
                    <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 15px 0;">
                    <div style="font-weight: bold;">€{monthly_cost}/year</div>
                </div>

                <div class="plan-card annual">
                    <div style="background: #10b981; color: white; padding: 5px; border-radius: 4px; font-size: 12px; margin-bottom: 10px;">
                        SAVE 20%
                    </div>
                    <h3>Annual</h3>
                    <div style="font-size: 14px; color: #166534;">Switch to this</div>
                    <div style="font-size: 32px; font-weight: bold; margin: 10px 0;">€15</div>
                    <div style="font-size: 14px; color: #166534;">per month*</div>
                    <hr style="border: none; border-top: 1px solid #10b981; margin: 15px 0;">
                    <div style="font-weight: bold; color: #10b981;">€{annual_cost}/year</div>
                </div>
            </div>

            <p style="text-align: center; color: #64748b; font-size: 14px;">
                *Billed €{annual_cost} annually
            </p>

            <div style="text-align: center; margin: 40px 0;">
                <a href="https://trezapp.com/dashboard/billing?switch=annual" class="cta-button">
                    Switch to Annual Billing →
                </a>
                <p style="color: #64748b; margin-top: 10px;">
                    ✅ Same features, lower price<br>
                    ✅ Switch instantly, no downtime
                </p>
            </div>

            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0;">

            <p style="color: #64748b; font-size: 14px;">
                <strong>Why annual billing?</strong><br>
                - Save €{savings} per year<br>
                - One less thing to think about (billed once a year)<br>
                - Lock in current pricing (we may increase prices in the future)
            </p>
        </div>
    </div>
</body>
</html>
"""


def get_agency_upsell_email(user_email: str, monitors_count: int) -> str:
    """
    Email to PRO users with many monitors about AGENCY plan.
    """
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #8b5cf6 0%, #ec4899 100%); color: white; padding: 30px; border-radius: 8px; text-align: center; }}
        .feature-list {{ background: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0; }}
        .feature-list li {{ margin: 10px 0; padding-left: 10px; }}
        .cta-button {{ display: inline-block; background: #8b5cf6; color: white; padding: 15px 40px; border-radius: 8px; text-decoration: none; font-size: 18px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Ready to scale? Meet the AGENCY plan</h1>
            <p>Built for teams managing {monitors_count}+ sites</p>
        </div>

        <div style="padding: 20px 0;">
            <p>Hi there,</p>
            <p>You're monitoring <strong>{monitors_count} sites</strong> on PRO - impressive! 🎉</p>
            <p>The <strong>AGENCY plan</strong> is built for teams like yours:</p>

            <div class="feature-list">
                <h3>Everything in PRO, plus:</h3>
                <ul style="list-style: none; padding: 0;">
                    <li>👥 <strong>Team collaboration</strong> - Add 5+ team members</li>
                    <li>🌐 <strong>Custom domains</strong> - status.yourclient.com</li>
                    <li>📁 <strong>Sub-accounts</strong> - Manage each client separately</li>
                    <li>⚡ <strong>Priority support</strong> - &lt;1h response time</li>
                    <li>📄 <strong>White-label reports</strong> - PDF reports with your branding</li>
                    <li>🛡️ <strong>99.9% SLA</strong> - Enterprise-grade reliability</li>
                </ul>
            </div>

            <h3>Perfect for:</h3>
            <ul>
                <li>Web agencies managing 20+ client sites</li>
                <li>Dev teams with multiple projects</li>
                <li>Freelancers with 10+ clients</li>
            </ul>

            <div style="text-align: center; margin: 40px 0;">
                <div style="font-size: 48px; font-weight: bold; color: #8b5cf6; margin-bottom: 10px;">
                    €99<span style="font-size: 24px; color: #64748b;">/month</span>
                </div>
                <p style="color: #64748b; margin-bottom: 20px;">or €950/year (save 20%)</p>

                <a href="https://trezapp.com/pricing?plan=agency" class="cta-button">
                    Upgrade to AGENCY →
                </a>
            </div>

            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0;">

            <p style="color: #64748b; font-size: 14px;">
                Questions about the AGENCY plan? Just reply to this email.<br>
                <em>- Founder, TrezApp</em>
            </p>
        </div>
    </div>
</body>
</html>
"""


def get_reengagement_email(user_email: str, days_inactive: int) -> str:
    """
    Email to inactive users (no login in 30+ days).
    """
    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #f59e0b; color: white; padding: 30px; border-radius: 8px; text-align: center; }}
        .cta-button {{ display: inline-block; background: #667eea; color: white; padding: 15px 40px; border-radius: 8px; text-decoration: none; font-size: 18px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>👋 We miss you!</h1>
            <p>Your account has been inactive for {days_inactive} days</p>
        </div>

        <div style="padding: 20px 0;">
            <p>Hi there,</p>
            <p>It's been a while since you last logged into TrezApp. We wanted to check in and see if everything's okay.</p>

            <h3>What's new since you left:</h3>
            <ul>
                <li>✨ Faster dashboard loading (50% faster)</li>
                <li>📊 New uptime graphs with 90-day history</li>
                <li>🔔 Improved Telegram notifications</li>
                <li>📄 Enhanced status pages with incident timeline</li>
            </ul>

            <p><strong>Quick reminder:</strong> Your FREE account is still active and monitoring your sites 24/7.</p>

            <div style="text-align: center; margin: 40px 0;">
                <a href="https://trezapp.com/dashboard" class="cta-button">
                    Log Back In →
                </a>
            </div>

            <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 30px 0;">

            <p style="color: #64748b; font-size: 14px;">
                If something's not working or you have feedback, just reply to this email - it goes straight to me.<br>
                <em>- Founder, TrezApp</em>
            </p>

            <p style="color: #94a3b8; font-size: 12px; text-align: center; margin-top: 30px;">
                Don't want to receive these emails?
                <a href="https://trezapp.com/dashboard/settings" style="color: #94a3b8;">Manage preferences</a>
            </p>
        </div>
    </div>
</body>
</html>
"""
