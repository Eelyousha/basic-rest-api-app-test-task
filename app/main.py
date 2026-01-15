from fastapi import FastAPI
from app.api import organizations, buildings, activities

app = FastAPI(
    title="Organization Directory System",
    description="REST API for managing organizations, buildings, and activities",
    version="1.0.0"
)

app.include_router(organizations.router)
app.include_router(buildings.router)
app.include_router(activities.router)


@app.get("/")
async def root():
    return {
        "message": "Organization Directory System API",
        "docs": "/docs",
        "redoc": "/redoc"
    }
