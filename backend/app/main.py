from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

from app.api.v1.decision import router

# Allow localhost in dev and any Vercel deployment domain in production.
# CORS_ORIGIN env var can override both (comma-separated list).
_raw = os.getenv("CORS_ORIGIN", "http://localhost:3000")
origins = [o.strip() for o in _raw.split(",") if o.strip()]

app = FastAPI(
    title="COMET Decision API",
    version="1.0.0",
    description="API para análise multicritério de LEDs"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    router,
    prefix="/api/v1",
    tags=["decision"]
)