from backend.main import app
from pydantic import BaseModel
from .function_calling import agent_loop
from fastapi import HTTPException
from backend.logger.logger_setup import  logger
class Chat(BaseModel):
    message : str
    path : str
    repo_type : str

@app.post('/chat')
def chat(chat:Chat):
    logger.info(f"User Request: {chat.message}")
    logger.info(f"Repo path: {chat.path}")
    if not chat.repo_type.upper() in ['GITHUB' , 'LOCAL']:
        raise HTTPException(status_code=404 , detail = f"repo type should be  GITHUB or LOCAL" )
    try:
        response = agent_loop(user_input = chat.message , repo = chat.path)
    except Exception as e:
        logger.error(f"{e}")
        raise HTTPException(status_code = 500 , detail=f"{e}")
    
    return response






