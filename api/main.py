from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
import sys

# Ensure proper path for imports when running directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import routes
from api.routes.chat_route import router as chat_router

# Create FastAPI app
app = FastAPI(
    title="VA Expenses API",
    description="API for VA Expenses financial assistant",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router, prefix="/api")

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "VA Expenses Financial Assistant API",
        "version": "1.0.0",
        "endpoints": {
            "chat": "/api/chat"
        }
    }

# Allow running the app directly with python api/main.py
if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )