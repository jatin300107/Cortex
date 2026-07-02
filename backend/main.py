from fastapi import FastAPI
from .agent.endpoints import chat 

app = FastAPI()


app.include_router(chat)