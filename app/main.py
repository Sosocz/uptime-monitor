from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, monitors, incidents, stripe_routes, dashboard, status_page_routes, seo_pages, intelligence, reports
from app.core.database import engine, Base

# Create database tables
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title="Uptime Monitor",
    description="Monitor your websites and services uptime",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(monitors.router, prefix="/api/monitors", tags=["Monitors"])
app.include_router(incidents.router, prefix="/api/incidents", tags=["Incidents"])
app.include_router(stripe_routes.router, prefix="/api/stripe", tags=["Stripe"])
app.include_router(intelligence.router, prefix="/api/intelligence", tags=["Intelligence"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])
app.include_router(dashboard.router, tags=["Dashboard"])
app.include_router(status_page_routes.router, prefix="/api", tags=["Status Pages"])
app.include_router(seo_pages.router, tags=["SEO Pages"])


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "uptime-monitor"}
