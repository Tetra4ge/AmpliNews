from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = FastAPI(
    title="AmpliNews API",
    description="Backend API for the AmpliNews Personalized News Digest Agent.",
    version="1.0.0"
)

# CORS configuration to allow the API Gateway to talk to this service
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to the API gateway URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from api.routes import auth, user, admin, articles, agent

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(user.router, prefix="/api/user", tags=["User Profile"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin"])
app.include_router(articles.router, prefix="/api/articles", tags=["Articles"])
app.include_router(agent.router, prefix="/api/agent", tags=["Agent"])

@app.get("/health", tags=["Health"])
async def health_check():
    """Simple health check endpoint."""
    return {
        "success": True,
        "service": "ai-analysis-service",
        "status": "up"
    }

if __name__ == "__main__":
    import uvicorn
    # When running directly, start the uvicorn server
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
