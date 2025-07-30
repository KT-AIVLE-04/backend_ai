# main.py
from fastapi import FastAPI
from routers.agent_router import router as agent_router

app = FastAPI()

app.include_router(agent_router)
