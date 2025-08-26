# main.py
from fastapi import FastAPI
from routers.shorts_router import router as shorts_router
from routers.sns_post_router import router as sns_post_router
from routers.comments_analysis_router import router as comments_analysis_router
from routers.report_generation_router import router as report_generation_router


app = FastAPI(title = "Backend AI")

app.include_router(shorts_router)
app.include_router(sns_post_router)
app.include_router(comments_analysis_router)
app.include_router(report_generation_router)


@app.get("/")
async def root():
    return {"message": "Chaos Backend AI API"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "services": ["agent", "sns_post", "comments_analysis", "report_generation"]}
