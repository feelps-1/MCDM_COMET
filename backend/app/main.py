from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.v1.decision import router

origins = [
    "http://localhost:3000",
]

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