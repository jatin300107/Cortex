from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .agent.endpoints import chat

app = FastAPI()

# Allow frontend dev server origin(s)
origins = [
	"http://localhost:5173",
	"http://127.0.0.1:5173",
	"http://localhost:5174",
	"http://127.0.0.1:5174",
]

app.add_middleware(
	CORSMiddleware,
	allow_origins=origins,
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"],
)


app.include_router(chat, prefix="/chat")