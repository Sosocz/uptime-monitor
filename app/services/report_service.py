"""
Report generation service for CEO/Client-ready reports.

Generates monthly uptime reports with:
- Uptime percentage
- Incident summary
- Downtime breakdown
- Comparison with previous month
- Health score
- Money lost estimate
"""
from datetime import datetime, timedelta
from typing import Dict, List
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.monitor import Monitor
from app.models.incident import Incident
from app.models.check import Check


def generate_monthly_report(db: Session, monitor: Monitor, month: int = None, year: int = None) -> Dict:
    """
    Generate a comprehensive monthly report for a monitor.

    Args:
        db: Database session
        monitor: Monitor to generate report for
        month: Month (1-12), defaults to previous month
        year: Year, defaults to current year

    Returns:
        Dict with all report data ready for PDF/email
    """
    # Default to previous month
    if not month or not year:
        today = datetime.utcnow()
        if today.month == 1:
            month = 12
            year = today.year - 1
        else:
            month = today.month - 1
            year = today.year

    # Calculate date range for report month
    report_start = datetime(year, month, 1)
    if month == 12:
        report_end = datetime(year + 1, 1, 1)
    else:
        report_end = datetime(year, month + 1, 1)

    # Previous month for comparison
    if month == 1:
        prev_month = 12
        prev_year = year - 1
    else:
        prev_month = month - 1
        prev_year = year

    prev_start = datetime(prev_year, prev_month, 1)
    prev_end = report_start

    # === CURRENT MONTH STATS ===

    # Total checks
    total_checks = db.query(func.count(Check.id)).filter(
        Check.monitor_id == monitor.id,
        Check.checked_at >= report_start,
        Check.checked_at < report_end
    ).scalar() or 0

    # UP checks
    up_checks = db.query(func.count(Check.id)).filter(
        Check.monitor_id == monitor.id,
        Check.status == "up",
        Check.checked_at >= report_start,
        Check.checked_at < report_end
    ).scalar() or 0

    # Uptime percentage
    uptime_pct = (up_checks / total_checks * 100) if total_checks > 0 else 100

    # Average response time
    avg_response = db.query(func.avg(Check.response_time)).filter(
        Check.monitor_id == monitor.id,
        Check.status == "up",
        Check.response_time.isnot(None),
        Check.checked_at >= report_start,
        Check.checked_at < report_end
    ).scalar() or 0

    # Incidents
    incidents = db.query(Incident).filter(
        Incident.monitor_id == monitor.id,
        Incident.started_at >= report_start,
        Incident.started_at < report_end
    ).order_by(Incident.started_at.desc()).all()

    # Total downtime
    total_downtime_minutes = sum(
        (i.duration_seconds or 0) // 60 for i in incidents if i.incident_type == "down"
    )

    # Money lost
    total_money_lost = sum(i.money_lost for i in incidents if i.money_lost)

    # === PREVIOUS MONTH FOR COMPARISON ===

    prev_total_checks = db.query(func.count(Check.id)).filter(
        Check.monitor_id == monitor.id,
        Check.checked_at >= prev_start,
        Check.checked_at < prev_end
    ).scalar() or 0

    prev_up_checks = db.query(func.count(Check.id)).filter(
        Check.monitor_id == monitor.id,
        Check.status == "up",
        Check.checked_at >= prev_start,
        Check.checked_at < prev_end
    ).scalar() or 0

    prev_uptime_pct = (prev_up_checks / prev_total_checks * 100) if prev_total_checks > 0 else 100

    prev_incidents_count = db.query(func.count(Incident.id)).filter(
        Incident.monitor_id == monitor.id,
        Incident.started_at >= prev_start,
        Incident.started_at < prev_end
    ).scalar() or 0

    # === COMPARISON ===

    uptime_change = uptime_pct - prev_uptime_pct
    incidents_change = len(incidents) - prev_incidents_count

    # === FORMAT INCIDENTS FOR REPORT ===

    formatted_incidents = []
    for incident in incidents:
        formatted_incidents.append({
            "date": incident.started_at.strftime("%Y-%m-%d %H:%M"),
            "duration": f"{incident.duration_seconds // 60} minutes" if incident.duration_seconds else "Ongoing",
            "cause": incident.intelligent_cause or incident.cause or "Unknown",
            "severity": incident.severity,
            "resolved": incident.resolved_at is not None
        })

    # === GENERATE SUMMARY TEXT ===

    if uptime_pct >= 99.9:
        summary = "Excellent performance this month!"
    elif uptime_pct >= 99:
        summary = "Good performance with minor incidents."
    elif uptime_pct >= 95:
        summary = "Several incidents detected, review recommended."
    else:
        summary = "Multiple incidents - action required."

    # Trend
    if uptime_change > 0:
        trend = f"Improvement of {uptime_change:.2f}% vs last month"
    elif uptime_change < 0:
        trend = f"Decline of {abs(uptime_change):.2f}% vs last month"
    else:
        trend = "Stable compared to last month"

    return {
        "monitor": {
            "name": monitor.name,
            "url": monitor.url,
            "health_score": monitor.health_score,
            "health_grade": monitor.health_grade
        },
        "report_period": {
            "month": report_start.strftime("%B %Y"),
            "start": report_start.strftime("%Y-%m-%d"),
            "end": (report_end - timedelta(days=1)).strftime("%Y-%m-%d")
        },
        "metrics": {
            "uptime_pct": round(uptime_pct, 2),
            "avg_response_time_ms": int(avg_response),
            "total_checks": total_checks,
            "incidents_count": len(incidents),
            "total_downtime_minutes": total_downtime_minutes,
            "money_lost": total_money_lost
        },
        "comparison": {
            "previous_month": prev_start.strftime("%B %Y"),
            "previous_uptime_pct": round(prev_uptime_pct, 2),
            "uptime_change": round(uptime_change, 2),
            "previous_incidents": prev_incidents_count,
            "incidents_change": incidents_change
        },
        "incidents": formatted_incidents,
        "summary": summary,
        "trend": trend,
        "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    }


def generate_html_report(report_data: Dict) -> str:
    """
    Generate clean HTML report from report data.
    Can be sent via email or converted to PDF.
    """
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            background: #f5f5f5;
            color: #333;
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            border-bottom: 3px solid #3b82f6;
            padding-bottom: 20px;
        }}
        .header h1 {{
            margin: 0;
            color: #1e40af;
            font-size: 28px;
        }}
        .header p {{
            margin: 10px 0 0;
            color: #666;
            font-size: 14px;
        }}
        .section {{
            margin: 30px 0;
        }}
        .section h2 {{
            color: #1e40af;
            border-left: 4px solid #3b82f6;
            padding-left: 12px;
            font-size: 20px;
            margin-bottom: 20px;
        }}
        .metrics {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin: 20px 0;
        }}
        .metric {{
            background: #f8fafc;
            padding: 20px;
            border-radius: 6px;
            border-left: 4px solid #3b82f6;
        }}
        .metric-label {{
            color: #666;
            font-size: 12px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .metric-value {{
            font-size: 32px;
            font-weight: bold;
            color: #1e40af;
            margin: 10px 0;
        }}
        .metric-change {{
            font-size: 14px;
            color: #059669;
        }}
        .metric-change.negative {{
            color: #dc2626;
        }}
        .health-score {{
            text-align: center;
            background: linear-gradient(135deg, #3b82f6, #1e40af);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .health-score .score {{
            font-size: 64px;
            font-weight: bold;
        }}
        .health-score .grade {{
            font-size: 24px;
            opacity: 0.9;
        }}
        .incidents {{
            margin: 20px 0;
        }}
        .incident {{
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            padding: 15px;
            margin: 10px 0;
            border-radius: 4px;
        }}
        .incident.critical {{
            background: #fee2e2;
            border-left-color: #dc2626;
        }}
        .incident-date {{
            font-weight: bold;
            color: #333;
        }}
        .incident-cause {{
            margin: 8px 0;
            color: #666;
        }}
        .summary {{
            background: #f0f9ff;
            border: 2px solid #3b82f6;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .summary h3 {{
            margin: 0 0 10px;
            color: #1e40af;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e5e7eb;
            color: #666;
            font-size: 12px;
        }}
        .footer a {{
            color: #3b82f6;
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{report_data['monitor']['name']}</h1>
            <p>Monthly Uptime Report - {report_data['report_period']['month']}</p>
            <p style="font-size: 12px; color: #999;">Generated on {report_data['generated_at']}</p>
        </div>

        <div class="health-score">
            <div class="score">{report_data['monitor']['health_score']}</div>
            <div class="grade">Grade: {report_data['monitor']['health_grade']}</div>
            <div style="margin-top: 10px; font-size: 14px;">Health Score</div>
        </div>

        <div class="summary">
            <h3>📊 Monthly Summary</h3>
            <p><strong>{report_data['summary']}</strong></p>
            <p>{report_data['trend']}</p>
        </div>

        <div class="section">
            <h2>📈 Key Metrics</h2>
            <div class="metrics">
                <div class="metric">
                    <div class="metric-label">Uptime</div>
                    <div class="metric-value">{report_data['metrics']['uptime_pct']}%</div>
                    <div class="metric-change {'negative' if report_data['comparison']['uptime_change'] < 0 else ''}">
                        {'+' if report_data['comparison']['uptime_change'] >= 0 else ''}{report_data['comparison']['uptime_change']}% vs last month
                    </div>
                </div>
                <div class="metric">
                    <div class="metric-label">Avg Response Time</div>
                    <div class="metric-value">{report_data['metrics']['avg_response_time_ms']}ms</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Total Incidents</div>
                    <div class="metric-value">{report_data['metrics']['incidents_count']}</div>
                    <div class="metric-change {'negative' if report_data['comparison']['incidents_change'] > 0 else ''}">
                        {'+' if report_data['comparison']['incidents_change'] >= 0 else ''}{report_data['comparison']['incidents_change']} vs last month
                    </div>
                </div>
                <div class="metric">
                    <div class="metric-label">Total Downtime</div>
                    <div class="metric-value">{report_data['metrics']['total_downtime_minutes']}</div>
                    <div style="font-size: 12px; color: #666; margin-top: 5px;">minutes</div>
                </div>
            </div>
        </div>
"""

    # Add incidents if any
    if report_data['incidents']:
        html += """
        <div class="section">
            <h2>⚠️ Incidents</h2>
            <div class="incidents">
"""
        for incident in report_data['incidents']:
            severity_class = 'critical' if incident['severity'] == 'critical' else ''
            html += f"""
                <div class="incident {severity_class}">
                    <div class="incident-date">{incident['date']}</div>
                    <div class="incident-cause"><strong>Cause:</strong> {incident['cause']}</div>
                    <div><strong>Duration:</strong> {incident['duration']}</div>
                </div>
"""
        html += """
            </div>
        </div>
"""
    else:
        html += """
        <div class="section">
            <h2>✅ Perfect Month</h2>
            <p style="color: #059669; font-weight: bold;">No incidents detected this month!</p>
        </div>
"""

    # Money lost section
    if report_data['metrics']['money_lost'] > 0:
        html += f"""
        <div class="section">
            <h2>💰 Estimated Impact</h2>
            <div class="metric" style="border-left-color: #dc2626;">
                <div class="metric-label">Estimated Revenue Lost</div>
                <div class="metric-value" style="color: #dc2626;">{report_data['metrics']['money_lost']}€</div>
                <div style="font-size: 12px; color: #666; margin-top: 5px;">Based on {report_data['metrics']['total_downtime_minutes']} minutes downtime</div>
            </div>
        </div>
"""

    html += f"""
        <div class="footer">
            <p><strong>Monitor URL:</strong> <a href="{report_data['monitor']['url']}" target="_blank">{report_data['monitor']['url']}</a></p>
            <p>Report period: {report_data['report_period']['start']} to {report_data['report_period']['end']}</p>
            <p style="margin-top: 20px;">Powered by <a href="https://trezapp.com" target="_blank">TrezApp</a> - Professional Uptime Monitoring</p>
        </div>
    </div>
</body>
</html>
"""

    return html


def generate_client_ready_summary(report_data: Dict) -> str:
    """
    Generate a short client-ready summary text (for email body).
    """
    return f"""
📊 {report_data['monitor']['name']} - Monthly Report

Period: {report_data['report_period']['month']}

✅ Uptime: {report_data['metrics']['uptime_pct']}%
⚡ Avg Response Time: {report_data['metrics']['avg_response_time_ms']}ms
⚠️ Total Incidents: {report_data['metrics']['incidents_count']}
⏱️ Total Downtime: {report_data['metrics']['total_downtime_minutes']} minutes

📈 {report_data['trend']}

{report_data['summary']}

--
Generated by TrezApp - Professional Uptime Monitoring
"""
