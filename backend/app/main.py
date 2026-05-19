from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.config import CORS_ORIGINS
from app.routers import auth, historico, jugadores, reuniones, temporadas
from app.security.rate_limit import limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Placeholder for future startup logic (e.g., Cloudinary config in PR3).
    yield


app = FastAPI(
    title="duDapp API",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan,
)

# Wire slowapi limiter
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def _rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {exc.detail}"},
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(temporadas.router)
app.include_router(reuniones.router)
app.include_router(jugadores.router)
app.include_router(historico.router)


@app.get("/health")
def health():
    return {"status": "ok"}
