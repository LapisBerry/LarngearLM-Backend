from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import resources, generate
from app.database import create_tables

app = FastAPI()


@app.on_event("startup")
def startup_event():
    create_tables()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(resources.router, prefix="/resources", tags=["Resource Operations"])
app.include_router(generate.router, prefix="/generate", tags=["Generate"])

@app.get("/")
def read_root():
    return {"message": "Welcome to LarngearLM-Backend API"}
