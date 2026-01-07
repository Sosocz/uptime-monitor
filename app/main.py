from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, monitors, incidents, stripe_routes, dashboard
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
app.include_router(dashboard.router, tags=["Dashboard"])


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "uptime-monitor"}
