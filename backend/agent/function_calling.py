from dotenv import load_dotenv
load_dotenv()

from google import genai
from dotenv import load_dotenv
import ast
from pathlib import Path
from fastapi import HTTPException

import json
import asyncio
import os
from backend.tools.tool_declaration import search_repo_declaration , cognee_query_declaration
from backend.tools.search_tool import SearchTool
from backend.tools.cognee_search import CogneeSearch
from pydantic import BaseModel 
from typing import Optional
from backend.logger.logger_setup import logger_setup
from backend.exceptions import AIRequestError


logger = logger_setup()
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

class CortexResponse(BaseModel):
    answer: str
    should_remember: bool
    intent: Optional[str]
    reasoning_chain: Optional[str]
    conclusion: Optional[str]

async def agent_loop(user_input , repo ):
    search_tool = SearchTool(repo_path=repo)
    repo = Path(repo)
    cognee_search = CogneeSearch(repo_name=repo.name)
    tool_map = {
        "search_repo": search_tool.run,
        "cognee_query": cognee_search.cognee_query,
    }
    try:
        logger.info(f"Sending request to gemini")
        FULL_SYSTEM_INSTRUCTION = '''You are a code intelligence agent for a software repository.

            Only use tools when the user's message actually requires repository or 
            project knowledge — a specific function, class, file, past decision, or 
            codebase behavior. For greetings, small talk, or general questions unrelated 
            to the repository, answer directly with no tool calls.

            When a tool is needed:
            1. Try cognee_query first, to check existing knowledge before searching the 
            repository directly.
            2. If cognee_query doesn't have any information, use search_repo to 
            explore the codebase — 'ast' mode when you know the exact function or 
            class name, 'grep' mode when you only have a code snippet or partial text.

            STRICT RULE: Never call cognee_query more than once for the same user 
            request, even reworded. Once cognee_query returns any result — even a 
            partial one — treat it as final for that tool. Do not re-invoke 
            cognee_query with a rephrased query to "double-check" or seek more detail.

            After gathering information, always return a clear, complete answer 
            explaining what you found. Never stop at just calling a tool — summarize 
            your findings for the user.

            Only call search_repo if cognee_query returned no information at all.
            Once you have any usable result from either tool, produce your final 
            response immediately. Do not call any tool a second time for the same 
            request under any circumstance.'''

        interaction =  client.interactions.create(
        model="gemini-3.5-flash",
        system_instruction =FULL_SYSTEM_INSTRUCTION,
        input=user_input,
        tools= [{"type": "function", **search_repo_declaration},
                    {"type" : "function" , **cognee_query_declaration}],
        response_format = {
            "type" : "text",
            "mime_type"  : "application/json",
            "schema" : CortexResponse.model_json_schema()},
        
    )
        
        logger.info(f"Requst sent to gemini")
    except Exception as e:
        logger.error(f"{e}")
        raise AIRequestError(e)
        
    

    max_tries = 3
    try_count = 0
    while interaction.status == "requires_action" :
        logger.info(f"{interaction.status}")
        try_count += 1
        logger.info(f"Agent loop attempt {try_count}/{max_tries}")
        function_results = []
        for step in interaction.steps:
            if step.type == "function_call":
                func = tool_map[step.name]
                logger.info(f"tool used : {step.name}")
                try:
                    
                    result = await func(**step.arguments)
                    function_results.append({
                "type": "function_result",
                "name": step.name,
                "call_id": step.id,
                "result": [{"type": "text", "text": json.dumps(result)}]
            })
                    logger.info(f"{step.name} results: {json.dumps(result)}")
                   
            
                    

                except Exception as e:
                    import traceback; traceback.print_exc()
                    raise                                                                                  
        interaction =  client.interactions.create(
            model="gemini-3.5-flash",
            previous_interaction_id=interaction.id,
            tools= [{"type": "function", **search_repo_declaration},
                    {"type" : "function" , **cognee_query_declaration}],
            input=function_results,
            system_instruction = FULL_SYSTEM_INSTRUCTION,
            response_format = {
            "type" : "text",
            "mime_type"  : "application/json",
            "schema" : CortexResponse.model_json_schema()},
            
                
        
                )
        logger.info(interaction.status)
    
        if try_count >= max_tries and interaction.status == "requires_action":
            logger.warning(f"Reached max tries ({max_tries}) while agent still requires action")
            raise HTTPException(status_code=500,detail=f"Reached max tries ({max_tries}) while agent still requires action")
    response = CortexResponse.model_validate_json(interaction.output_text)
    
    
    if response.should_remember:
        logger.info(response)
        memory_dataset = f"{repo.name}_memory"
        reasoning_text = (
        f"Query: {user_input}\n"
        f"Intent: {response.intent}\n"
        f"Reasoning: {response.reasoning_chain}\n"
        f"Conclusion: {response.conclusion}\n"
        f"Answer: {response.answer}"
    )
        try:
            await cognee.remember(
            reasoning_text,
            dataset_name=memory_dataset,
            self_improvement=True,
            )
            logger.info(f"Ingested memory")
        except Exception as e:
            logger.error(f"Failed to ingest reasoning: {e}", exc_info=True)
    return response.answer
        
        