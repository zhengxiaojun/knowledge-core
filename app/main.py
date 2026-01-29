from fastapi import FastAPI
from app.api import requirements, knowledge, graph, testcases, tasks
from app.models.sql_models import init_db
from app.core.config import settings

app = FastAPI(
    title=settings.project_name,
    version=settings.project_version,
    description=settings.project_description
)

@app.on_event("startup")
async def startup_event():
    print("Application startup: Initializing database...")
    init_db()
    print("Application startup: Services are ready.")

app.include_router(requirements.router, prefix="/api/requirements", tags=["Requirements"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["Knowledge"])
app.include_router(graph.router, prefix="/api/graph", tags=["Graph"])
app.include_router(testcases.router, prefix="/api/testcases", tags=["Test Cases"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["Tasks"])

@app.get("/")
def read_root():
    return {"message": "Welcome to the Vx-Knowledge-Core API"}
