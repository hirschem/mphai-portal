import logging
# --- Redact Authorization header in logs (minimal filter) ---
class RedactAuthFilter(logging.Filter):
    def filter(self, record):
        # Redact Authorization in args dict
        if hasattr(record, 'args') and isinstance(record.args, dict):
            args = dict(record.args)
            if 'authorization' in args:
                args['authorization'] = '[REDACTED]'
            record.args = args
        # Redact Authorization in msg string
        if hasattr(record, 'msg') and isinstance(record.msg, str) and 'authorization' in record.msg.lower():
            record.msg = record.msg.replace('Authorization', 'Authorization[REDACTED]')
        return True
for handler in logging.getLogger().handlers:
    handler.addFilter(RedactAuthFilter())
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
        "http://localhost:3001",
        "http://localhost:3002",
        "https://mphai.app",
        "https://www.mphai.app"
    ],
    allow_origin_regex=r"^https://.*\.vercel\.app$",
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

# --- DEBUG: confirm which auth module/router is loaded in Railway ---
print("=== AUTH MODULE DEBUG ===")
print("auth module file:", getattr(auth, "__file__", "NO __file__"))
print("auth.router.prefix:", getattr(auth.router, "prefix", "NO prefix attr"))
print("auth.router.routes:", [getattr(r, "path", str(r)) for r in getattr(auth.router, "routes", [])])

print("=== ROUTES DUMP (contains '/auth') ===")
for r in app.routes:
    p = getattr(r, "path", "")
    if "/auth" in p:
        print("ROUTE:", p, sorted(getattr(r, "methods", [])))
print("=== END ROUTES DUMP ===")


@app.get("/")
async def root():
    return {
        "message": "MPH Handwriting API",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    return {"status": "ok"}
