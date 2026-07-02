from pydantic import BaseModel
from .function_calling import agent_loop
from fastapi import HTTPException
from backend.logger.logger_setup import  logger

from pathlib import Path
from fastapi import APIRouter
from get_utils import get_dataset_id

chat = APIRouter()
class Chat(BaseModel):
    message : str
    path : str
    repo_type : str

@chat.post('/chat/request')
async def chat_request(chat:Chat):
    logger.info(f"User Request: {chat.message}")
    logger.info(f"Repo path: {chat.path}")
    repo = Path(chat.path)
    dataset_id = await get_dataset_id(repo.name)
    if not chat.repo_type.upper() in ['GITHUB' , 'LOCAL']:
        raise HTTPException(status_code=404 , detail = f"repo type should be  GITHUB or LOCAL" )
    try:
        response = await agent_loop(user_input = chat.message , repo = chat.path , dataset_id = dataset_id)
    except Exception as e:
        logger.error(f"{e}")
        raise HTTPException(status_code = 500 , detail=f"{e}")
    
    return response






