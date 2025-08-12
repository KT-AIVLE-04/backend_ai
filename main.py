# main.py
from fastapi import FastAPI
from routers.agent_router import router as agent_router
from routers.sns_post_router import router as sns_post_router

app = FastAPI(title="Chaos Backend AI")

app.include_router(agent_router)
app.include_router(sns_post_router)

@app.get("/")
async def root():
    return {"message": "Chaos Backend AI API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "services": ["agent", "sns_post"]}
