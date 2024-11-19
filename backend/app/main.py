from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.endpoints import router as v1_router


app = FastAPI(title="Document Management API")

origins = [
    "http://localhost:3000",
    "https://snowjass.ru",
    "https://www.snowjass.ru",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["X-Requested-With", "Content-Type"],
)

app.include_router(v1_router, prefix="/v1")
