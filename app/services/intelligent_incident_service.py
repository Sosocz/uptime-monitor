"""
Intelligent incident analysis service - "Why it went down"

Provides advanced incident detection and analysis:
- Smart cause detection (SSL, DNS, timeout, server overload, etc.)
- Flapping detection (rapid UP/DOWN)
- Progressive degradation detection (slowdown before crash)
- Health score calculation (0-100)
- Predictive patterns
"""
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc
from app.models.monitor import Monitor
from app.models.check import Check
from app.models.incident import Incident


def analyze_why_it_went_down(db: Session, monitor: Monitor, current_check: Check) -> Dict:
    """
    Advanced analysis to determine WHY a site went down.

    Returns:
        {
            "cause": "Probable cause: Server overloaded (latency x3 before crash)",
            "severity": "critical",  # critical, warning, info
            "details": {...},
            "recommendations": ["Check server resources", "Review traffic spike"]
        }
    """
    result = {
        "cause": "Unknown",
        "severity": "warning",
        "details": {},
        "recommendations": []
    }

    # 1. SSL Certificate expired
    if current_check.ssl_expires_at:
        if current_check.ssl_expires_at < datetime.utcnow():
            result["cause"] = "SSL Certificate Expired"
            result["severity"] = "critical"
            result["details"]["ssl_expired"] = True
            result["details"]["expired_since"] = str(datetime.utcnow() - current_check.ssl_expires_at)
            result["recommendations"].append("Renew SSL certificate immediately")
            return result
        # SSL expiring soon
        days_until_expiry = (current_check.ssl_expires_at - datetime.utcnow()).days
        if days_until_expiry < 7:
            result["details"]["ssl_expiring_soon"] = True
            result["details"]["days_left"] = days_until_expiry
            result["recommendations"].append(f"SSL expires in {days_until_expiry} days")

    # 2. DNS failure
    if current_check.error_message:
        error_lower = current_check.error_message.lower()
        if "dns" in error_lower or "name resolution" in error_lower or "getaddrinfo" in error_lower:
            result["cause"] = "DNS Resolution Failed - Domain not found or DNS servers down"
            result["severity"] = "critical"
            result["details"]["dns_failure"] = True
            result["recommendations"].append("Check domain DNS settings")
            result["recommendations"].append("Verify nameservers are responding")
            return result

    # 3. Timeout - check for progressive slowdown
    if current_check.error_message and "timeout" in current_check.error_message.lower():
        # Get recent checks to see if there was a slowdown pattern
        recent_checks = db.query(Check).filter(
            Check.monitor_id == monitor.id,
            Check.id < current_check.id,
            Check.status == "up"
        ).order_by(Check.id.desc()).limit(10).all()

        if recent_checks and len(recent_checks) >= 3:
            avg_response_time = sum(c.response_time for c in recent_checks[:5] if c.response_time) / 5
            if avg_response_time > 3000:  # > 3 seconds
                result["cause"] = f"Server overloaded - Response time degraded to {int(avg_response_time)}ms before timeout"
                result["severity"] = "critical"
                result["details"]["progressive_degradation"] = True
                result["details"]["avg_response_before_crash"] = int(avg_response_time)
                result["recommendations"].append("Server appears saturated")
                result["recommendations"].append("Check CPU/RAM usage")
                result["recommendations"].append("Review recent traffic spike")
                return result

        result["cause"] = "Request Timeout - Server too slow to respond"
        result["severity"] = "critical"
        result["details"]["timeout"] = True
        result["recommendations"].append("Check server response time")
        result["recommendations"].append("Verify server is not under heavy load")
        return result

    # 4. Connection refused / failed
    if current_check.error_message:
        error_lower = current_check.error_message.lower()
        if "connection refused" in error_lower or "connection reset" in error_lower:
            result["cause"] = "Connection Refused - Server not accepting connections"
            result["severity"] = "critical"
            result["details"]["connection_refused"] = True
            result["recommendations"].append("Server may be down or firewall blocking")
            result["recommendations"].append("Check if server process is running")
            return result

        if "ssl" in error_lower or "certificate" in error_lower:
            result["cause"] = "SSL/TLS Error - Certificate validation failed"
            result["severity"] = "critical"
            result["details"]["ssl_error"] = True
            result["recommendations"].append("Check SSL certificate configuration")
            return result

    # 5. HTTP Status codes
    if current_check.status_code:
        if current_check.status_code == 500:
            result["cause"] = "Internal Server Error (500) - Application crash or bug"
            result["severity"] = "critical"
            result["recommendations"].append("Check application logs")
            result["recommendations"].append("Recent deployment may have introduced a bug")
        elif current_check.status_code == 502:
            result["cause"] = "Bad Gateway (502) - Reverse proxy cannot reach backend"
            result["severity"] = "critical"
            result["recommendations"].append("Backend server may be down")
            result["recommendations"].append("Check nginx/apache proxy configuration")
        elif current_check.status_code == 503:
            result["cause"] = "Service Unavailable (503) - Server temporarily overloaded"
            result["severity"] = "critical"
            result["recommendations"].append("Server under maintenance or overloaded")
            result["recommendations"].append("May recover automatically")
        elif current_check.status_code == 504:
            result["cause"] = "Gateway Timeout (504) - Backend server too slow"
            result["severity"] = "critical"
            result["recommendations"].append("Backend application not responding")
            result["recommendations"].append("Check database performance")
        elif current_check.status_code >= 400:
            result["cause"] = f"HTTP {current_check.status_code} Error"
            result["severity"] = "warning"

        result["details"]["status_code"] = current_check.status_code
        return result

    # 6. Generic network error
    if current_check.error_message:
        result["cause"] = f"Network Error: {current_check.error_message[:100]}"
        result["severity"] = "warning"
        result["recommendations"].append("Check network connectivity")

    return result


def detect_flapping(db: Session, monitor: Monitor, lookback_minutes: int = 30) -> Optional[Dict]:
    """
    Detect if a site is "flapping" (going UP/DOWN rapidly).

    Returns flapping info if detected, None otherwise.
    """
    since = datetime.utcnow() - timedelta(minutes=lookback_minutes)

    # Get recent checks
    recent_checks = db.query(Check).filter(
        Check.monitor_id == monitor.id,
        Check.checked_at >= since
    ).order_by(Check.checked_at.asc()).all()

    if len(recent_checks) < 6:
        return None

    # Count status transitions
    transitions = 0
    for i in range(1, len(recent_checks)):
        if recent_checks[i].status != recent_checks[i-1].status:
            transitions += 1

    # If more than 3 transitions in 30 minutes = flapping
    if transitions >= 3:
        return {
            "is_flapping": True,
            "transitions": transitions,
            "period_minutes": lookback_minutes,
            "severity": "warning",
            "message": f"Site is unstable: {transitions} UP/DOWN transitions in {lookback_minutes} minutes"
        }

    return None


def detect_progressive_degradation(db: Session, monitor: Monitor, current_check: Check) -> Optional[Dict]:
    """
    Detect if site is slowing down (may crash soon).

    Returns degradation warning if detected.
    """
    if current_check.status != "up" or not current_check.response_time:
        return None

    # Get baseline (last 50 successful checks)
    baseline_checks = db.query(Check).filter(
        Check.monitor_id == monitor.id,
        Check.status == "up",
        Check.response_time.isnot(None),
        Check.id < current_check.id
    ).order_by(Check.id.desc()).limit(50).all()

    if len(baseline_checks) < 10:
        return None

    # Calculate baseline average
    baseline_avg = sum(c.response_time for c in baseline_checks) / len(baseline_checks)

    # Get recent average (last 5 checks)
    recent_checks = baseline_checks[:5]
    recent_avg = sum(c.response_time for c in recent_checks) / len(recent_checks)

    # If recent avg is 2x+ higher than baseline
    if recent_avg > baseline_avg * 2 and recent_avg > 2000:  # > 2s
        increase_pct = int(((recent_avg - baseline_avg) / baseline_avg) * 100)
        return {
            "degrading": True,
            "baseline_ms": int(baseline_avg),
            "current_ms": int(recent_avg),
            "increase_pct": increase_pct,
            "severity": "warning",
            "message": f"Site still UP but response time increased +{increase_pct}% (crash probable soon)"
        }

    return None


def calculate_health_score(db: Session, monitor: Monitor, days: int = 30) -> Dict:
    """
    Calculate health score 0-100 for a monitor.

    Factors:
    - Uptime percentage (60%)
    - Incident frequency (20%)
    - Response time stability (20%)
    """
    since = datetime.utcnow() - timedelta(days=days)

    # 1. Uptime percentage (60 points)
    total_checks = db.query(func.count(Check.id)).filter(
        Check.monitor_id == monitor.id,
        Check.checked_at >= since
    ).scalar() or 0

    if total_checks == 0:
        return {
            "score": 100,
            "uptime_pct": 100,
            "incidents_count": 0,
            "avg_response_time": 0,
            "grade": "A+"
        }

    up_checks = db.query(func.count(Check.id)).filter(
        Check.monitor_id == monitor.id,
        Check.status == "up",
        Check.checked_at >= since
    ).scalar() or 0

    uptime_pct = (up_checks / total_checks) * 100
    uptime_score = (uptime_pct / 100) * 60

    # 2. Incident frequency (20 points)
    incidents_count = db.query(func.count(Incident.id)).filter(
        Incident.monitor_id == monitor.id,
        Incident.started_at >= since
    ).scalar() or 0

    # Penalize based on incident count
    if incidents_count == 0:
        incident_score = 20
    elif incidents_count <= 2:
        incident_score = 15
    elif incidents_count <= 5:
        incident_score = 10
    else:
        incident_score = max(0, 20 - incidents_count)

    # 3. Response time stability (20 points)
    recent_checks = db.query(Check).filter(
        Check.monitor_id == monitor.id,
        Check.status == "up",
        Check.response_time.isnot(None),
        Check.checked_at >= since
    ).limit(100).all()

    if recent_checks:
        avg_response = sum(c.response_time for c in recent_checks) / len(recent_checks)
        # Fast sites (< 500ms) get full 20 points
        # Slow sites (> 5s) get 0 points
        if avg_response < 500:
            response_score = 20
        elif avg_response > 5000:
            response_score = 0
        else:
            response_score = 20 - ((avg_response - 500) / 4500) * 20
    else:
        response_score = 20

    # Total score
    total_score = int(uptime_score + incident_score + response_score)

    # Grade
    if total_score >= 95:
        grade = "A+"
    elif total_score >= 90:
        grade = "A"
    elif total_score >= 85:
        grade = "B+"
    elif total_score >= 80:
        grade = "B"
    elif total_score >= 70:
        grade = "C"
    else:
        grade = "D"

    avg_response_time = int(sum(c.response_time for c in recent_checks) / len(recent_checks)) if recent_checks else 0

    return {
        "score": total_score,
        "grade": grade,
        "uptime_pct": round(uptime_pct, 2),
        "incidents_count": incidents_count,
        "avg_response_time": avg_response_time,
        "days_analyzed": days
    }


def detect_patterns(db: Session, monitor: Monitor) -> Dict:
    """
    Detect patterns in incidents (for "Site DNA").

    Returns:
        - High-risk hours
        - Day of week patterns
        - Stability trend
    """
    # Get all incidents
    incidents = db.query(Incident).filter(
        Incident.monitor_id == monitor.id
    ).all()

    if not incidents:
        return {
            "high_risk_hours": [],
            "high_risk_days": [],
            "total_incidents": 0,
            "stability_trend": "stable"
        }

    # Analyze hours
    hour_incidents = {}
    day_incidents = {}

    for incident in incidents:
        hour = incident.started_at.hour
        day = incident.started_at.strftime("%A")

        hour_incidents[hour] = hour_incidents.get(hour, 0) + 1
        day_incidents[day] = day_incidents.get(day, 0) + 1

    # Find high-risk hours (top 3)
    sorted_hours = sorted(hour_incidents.items(), key=lambda x: x[1], reverse=True)
    high_risk_hours = [f"{h:02d}:00-{h:02d}:59" for h, _ in sorted_hours[:3]] if sorted_hours else []

    # Find high-risk days
    sorted_days = sorted(day_incidents.items(), key=lambda x: x[1], reverse=True)
    high_risk_days = [day for day, _ in sorted_days[:2]] if sorted_days else []

    # Stability trend (recent 30 days vs previous 30 days)
    now = datetime.utcnow()
    recent_incidents = [i for i in incidents if i.started_at >= now - timedelta(days=30)]
    previous_incidents = [i for i in incidents if now - timedelta(days=60) <= i.started_at < now - timedelta(days=30)]

    if len(previous_incidents) == 0:
        stability_trend = "stable"
    elif len(recent_incidents) > len(previous_incidents):
        stability_trend = "degrading"
    elif len(recent_incidents) < len(previous_incidents):
        stability_trend = "improving"
    else:
        stability_trend = "stable"

    return {
        "high_risk_hours": high_risk_hours,
        "high_risk_days": high_risk_days,
        "total_incidents": len(incidents),
        "stability_trend": stability_trend
    }


def calculate_time_and_money_lost(incident: Incident, estimated_revenue_per_hour: float = 0) -> Dict:
    """
    Calculate time lost and estimated money lost during an incident.

    Args:
        incident: The incident
        estimated_revenue_per_hour: User's estimated revenue per hour (optional)

    Returns:
        {
            "minutes_lost": 45,
            "hours_lost": 0.75,
            "money_lost_eur": 150.0,
            "formatted": "45 minutes lost (~150€)"
        }
    """
    if not incident.duration_seconds:
        # Incident still ongoing
        duration_seconds = (datetime.utcnow() - incident.started_at).total_seconds()
    else:
        duration_seconds = incident.duration_seconds

    minutes_lost = int(duration_seconds / 60)
    hours_lost = duration_seconds / 3600

    # Calculate money lost if revenue provided
    money_lost = 0
    if estimated_revenue_per_hour > 0:
        money_lost = hours_lost * estimated_revenue_per_hour

    formatted = f"{minutes_lost} minutes lost"
    if money_lost > 0:
        formatted += f" (~{int(money_lost)}€)"

    return {
        "minutes_lost": minutes_lost,
        "hours_lost": round(hours_lost, 2),
        "money_lost_eur": round(money_lost, 2),
        "formatted": formatted
    }
