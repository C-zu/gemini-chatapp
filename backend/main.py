from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import chat, sessions, ai

app = FastAPI(title="Chat Backend API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501", "http://127.0.0.1:8501"],  # Streamlit
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat.router, prefix="/api/v1")
app.include_router(sessions.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Chat Backend API is running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)