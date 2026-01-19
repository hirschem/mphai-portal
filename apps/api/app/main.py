from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import transcribe, proposals, history, auth, books

app = FastAPI(
    title="MPH Handwriting API",
    description="Transcribe handwritten proposals to professional documents",
    version="0.1.0"
)

# CORS middleware for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://mphai.app",
        "https://www.mphai.app",
        "https://*.mphai.app",
        "https://*.vercel.app"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(transcribe.router, prefix="/api/transcribe", tags=["transcribe"])
app.include_router(proposals.router, prefix="/api/proposals", tags=["proposals"])
app.include_router(history.router, prefix="/api/history", tags=["history"])
app.include_router(books.router, prefix="/api/book", tags=["book"])


@app.get("/")
async def root():
    return {
        "message": "MPH Handwriting API",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
