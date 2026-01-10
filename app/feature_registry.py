"""
Feature Registry - Central source of truth for all application features/pages
This registry is used to generate navigation, permissions, and feature discovery
"""

from enum import Enum
from typing import List, Optional
from dataclasses import dataclass


class FeatureCategory(Enum):
    MAIN = "main"
    ANALYTICS = "analytics"
    INTELLIGENCE = "intelligence"
    MANAGEMENT = "management"
    REPORTS = "reports"
    ACCOUNT = "account"
    ADMIN = "admin"


class UserPlan(Enum):
    FREE = "free"
    PAID = "paid"
    ALL = "all"  # Available to all plans


@dataclass
class Feature:
    """Feature definition"""
    id: str  # Unique identifier
    name: str  # Display name
    route: str  # URL route
    icon: str  # Icon emoji or SVG class
    category: FeatureCategory
    description: str
    min_plan: UserPlan = UserPlan.ALL  # Minimum plan required
    enabled: bool = True  # Feature flag
    badge: Optional[str] = None  # Badge text (e.g., "NEW", "PRO")
    order: int = 0  # Display order within category


# ============================================================================
# FEATURE REGISTRY - SOURCE OF TRUTH
# ============================================================================

FEATURES: List[Feature] = [
    # MAIN FEATURES
    Feature(
        id="dashboard",
        name="Dashboard",
        route="/dashboard",
        icon="🏠",
        category=FeatureCategory.MAIN,
        description="Monitor overview and quick actions",
        order=1
    ),
    Feature(
        id="incidents",
        name="Incidents",
        route="/incidents",
        icon="🚨",
        category=FeatureCategory.MAIN,
        description="View and manage all incidents",
        order=2
    ),

    # ANALYTICS FEATURES
    Feature(
        id="incident_analytics",
        name="MTTA/MTTR Analytics",
        route="/incident-analytics",
        icon="📊",
        category=FeatureCategory.ANALYTICS,
        description="Track incident response performance metrics",
        order=1
    ),

    # INTELLIGENCE FEATURES (AI-powered insights)
    Feature(
        id="intelligence_dashboard",
        name="Intelligence Dashboard",
        route="/intelligence",
        icon="🧠",
        category=FeatureCategory.INTELLIGENCE,
        description="AI-powered insights, health scores, and pattern detection",
        min_plan=UserPlan.PAID,
        badge="PRO",
        order=1
    ),
    Feature(
        id="health_scores",
        name="Health Scores",
        route="/intelligence/health",
        icon="🎯",
        category=FeatureCategory.INTELLIGENCE,
        description="Monitor health grades (A+ to D) and scoring",
        min_plan=UserPlan.PAID,
        badge="PRO",
        order=2
    ),
    Feature(
        id="site_dna",
        name="Site DNA",
        route="/intelligence/dna",
        icon="🧬",
        category=FeatureCategory.INTELLIGENCE,
        description="Pattern detection and site behavior analysis",
        min_plan=UserPlan.PAID,
        badge="PRO",
        order=3
    ),
    Feature(
        id="smart_views",
        name="Smart Views",
        route="/intelligence/views",
        icon="👁️",
        category=FeatureCategory.INTELLIGENCE,
        description="Critical, Unstable, and Stable monitor groupings",
        min_plan=UserPlan.PAID,
        badge="PRO",
        order=4
    ),

    # MANAGEMENT FEATURES
    Feature(
        id="oncall",
        name="On-Call",
        route="/oncall",
        icon="🔔",
        category=FeatureCategory.MANAGEMENT,
        description="On-call schedules and rotation management",
        order=1
    ),
    Feature(
        id="status_pages",
        name="Status Pages",
        route="/status-pages",
        icon="📄",
        category=FeatureCategory.MANAGEMENT,
        description="Create and manage public status pages",
        order=2
    ),
    Feature(
        id="subscribers",
        name="Subscribers",
        route="/status-page-subscribers",
        icon="📧",
        category=FeatureCategory.MANAGEMENT,
        description="Manage status page email subscribers",
        order=3
    ),

    # REPORTS FEATURES
    Feature(
        id="reports",
        name="Reports",
        route="/reports",
        icon="📑",
        category=FeatureCategory.REPORTS,
        description="Generate monthly PDF reports for clients",
        min_plan=UserPlan.PAID,
        badge="PRO",
        order=1
    ),

    # ACCOUNT FEATURES
    Feature(
        id="upgrade",
        name="Upgrade Plan",
        route="/upgrade",
        icon="⚡",
        category=FeatureCategory.ACCOUNT,
        description="Compare plans and upgrade to PRO",
        order=1
    ),
]


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def get_all_features() -> List[Feature]:
    """Get all features"""
    return FEATURES


def get_features_by_category(category: FeatureCategory) -> List[Feature]:
    """Get all features in a category, sorted by order"""
    return sorted(
        [f for f in FEATURES if f.category == category],
        key=lambda f: f.order
    )


def get_enabled_features() -> List[Feature]:
    """Get all enabled features"""
    return [f for f in FEATURES if f.enabled]


def get_features_for_plan(plan: UserPlan) -> List[Feature]:
    """Get features available for a user plan"""
    return [
        f for f in FEATURES
        if f.enabled and (f.min_plan == UserPlan.ALL or f.min_plan == plan or plan == UserPlan.PAID)
    ]


def get_feature_by_id(feature_id: str) -> Optional[Feature]:
    """Get feature by ID"""
    return next((f for f in FEATURES if f.id == feature_id), None)


def get_feature_by_route(route: str) -> Optional[Feature]:
    """Get feature by route"""
    return next((f for f in FEATURES if f.route == route), None)


def get_categories_with_features(plan: UserPlan = UserPlan.ALL) -> dict:
    """Get all categories with their features for a plan"""
    available_features = get_features_for_plan(plan)
    result = {}

    for category in FeatureCategory:
        features = [f for f in available_features if f.category == category]
        if features:
            result[category] = sorted(features, key=lambda f: f.order)

    return result


# ============================================================================
# NAVIGATION HELPERS
# ============================================================================

def get_sidebar_navigation(user_plan: str = "free") -> dict:
    """Generate sidebar navigation structure for templates"""
    plan = UserPlan.PAID if user_plan.lower() == "paid" else UserPlan.FREE
    categories = get_categories_with_features(plan)

    navigation = {}
    for category, features in categories.items():
        # Convert category enum to display name
        category_name = category.value.upper() if category != FeatureCategory.MAIN else "MAIN"
        navigation[category_name] = [
            {
                "name": f.name,
                "route": f.route,
                "icon": f.icon,
                "badge": f.badge,
                "description": f.description
            }
            for f in features
        ]

    return navigation


def get_dashboard_modules(user_plan: str = "free") -> List[dict]:
    """Get all feature modules for dashboard display"""
    plan = UserPlan.PAID if user_plan.lower() == "paid" else UserPlan.FREE
    features = get_features_for_plan(plan)

    return [
        {
            "id": f.id,
            "name": f.name,
            "route": f.route,
            "icon": f.icon,
            "category": f.category.value,
            "description": f.description,
            "badge": f.badge,
            "locked": f.min_plan == UserPlan.PAID and plan == UserPlan.FREE
        }
        for f in sorted(features, key=lambda x: (x.category.value, x.order))
    ]
