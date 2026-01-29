from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api import requirements, knowledge, graph, testcases, tasks, testpoints, data_import
from app.models.sql_models import init_db
from app.core.config import settings
from app.core.dependencies import cleanup_services


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Application startup: Initializing database...")
    init_db()
    print("Application startup: Services are ready.")
    yield
    # Shutdown
    print("Application shutdown: Cleaning up services...")
    cleanup_services()
    print("Application shutdown: Complete.")


app = FastAPI(
    title=settings.project_name,
    version=settings.project_version,
    description=settings.project_description,
    lifespan=lifespan
)

app.include_router(requirements.router, prefix="/api/requirements", tags=["Requirements"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["Knowledge"])
app.include_router(graph.router, prefix="/api/graph", tags=["Graph"])
app.include_router(testpoints.router, prefix="/api/testpoints", tags=["Test Points"])
app.include_router(testcases.router, prefix="/api/testcases", tags=["Test Cases"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(defects.router, prefix="/api/defects", tags=["Defects"])
app.include_router(data_import.router, prefix="/api/data", tags=["Data Import"])
app.include_router(statistics.router, prefix="/api/statistics", tags=["Statistics"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Vx-Knowledge-Core API"}


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.project_name,
        "version": settings.project_version
    }

