from dotenv import load_dotenv
load_dotenv()
from datapoints import ReasoningNode
from google import genai
from dotenv import load_dotenv
import ast
from pathlib import Path
import cognee
from cognee.tasks.storage import add_data_points
import json
import asyncio
import os
from backend.tools.tool_declaration import search_repo_declaration , cognee_query_declaration
from backend.tools.search_tool import SearchTool
from backend.tools.cognee_search import  cognee_query
from pydantic import BaseModel 
from typing import Optional
from backend.logger.logger_setup import logger
from backend.exceptions import AIRequestError
from .dataset import store_datasets
client = genai.Client(api_key=os.getenv('GEMINI_API_KEY'))

class CortexResponse(BaseModel):
    answer: str
    should_remember: bool
    intent: Optional[str]
    reasoning_chain: Optional[str]
    conclusion: Optional[str]

async def agent_loop(user_input , repo , dataset_id):
    search_tool = SearchTool(repo_path=repo , dataset_id = dataset_id)
    tool_map = {
        "search_repo": search_tool.run,
        "cognee_query": cognee_query,
    }
    try:

        interaction =  client.interactions.create(
        model="gemini-3.1-flash-lite",
        system_instruction ='''You are a code intelligence agent for a software repository.

            Only use tools when the user's message actually requires repository or 
            project knowledge — a specific function, class, file, past decision, or 
            codebase behavior. For greetings, small talk, or general questions unrelated 
            to the repository, answer directly with no tool calls.

            When a tool is needed:
            1. Try cognee_query first, to check existing knowledge before searching the 
            repository directly.
            2. If cognee_query doesn't have enough information, use search_repo to 
            explore the codebase — 'ast' mode when you know the exact function or 
            class name, 'grep' mode when you only have a code snippet or partial text.

            After gathering information, always return a clear, complete answer 
            explaining what you found. Never stop at just calling a tool — summarize 
            your findings for the user.''',
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
        
    if interaction:
        print(interaction)
    else:
        print("no interaction found")

    while interaction.status == "requires_action":
        function_results = []
        for step in interaction.steps:
            if step.type == "function_call":
                func = tool_map[step.name]
                logger.info(f"tool used : {step.name}")
                try:
                    if step.name == "search_repo":
                        result = await func(**step.arguments)
                    else:    
                        result = await func(**step.arguments, dataset_id = [dataset_id])
                    print(result)
                    function_results.append({
                "type": "function_result",
                "name": step.name,
                "call_id": step.id,
                "result": [{"type": "text", "text": json.dumps(result)}]
            })

                except Exception as e:
                    import traceback; traceback.print_exc()
                    raise                                                                                  
        interaction =  client.interactions.create(
            model="gemini-3.1-flash-lite",
            previous_interaction_id=interaction.id,
            tools= [{"type": "function", **search_repo_declaration},
                    {"type" : "function" , **cognee_query_declaration}],
            input=function_results,
            response_format = {
            "type" : "text",
            "mime_type"  : "application/json",
            "schema" : CortexResponse.model_json_schema()},
        
                )
    
    response = CortexResponse.model_validate_json(interaction.output_text)
    
    node = ReasoningNode(
    query=user_input,          
    
    intent=response.intent,
    reasoning_chain=response.reasoning_chain,
    conclusion=response.conclusion,
)
    if response.should_remember:
        logger.info("Persisting reasoning to Cognee")
        await store_datasets(node_set=node, dataset_id=dataset_id)
        

    
    print(response)
    print(response.answer)
    return response.answer

