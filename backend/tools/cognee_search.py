from dotenv import load_dotenv
load_dotenv()
from cognee import SearchType
import cognee
from get_utils import get_user
from backend.logger.logger_setup import logger_setup
logger = logger_setup()
from fastapi import HTTPException
from cognee.shared.logging_utils import DatasetNotFoundError
# repo_name
# dataset_name=repo_name
# dataset_name=repo_name
class CogneeSearch():
    def __init__(self,repo_name):
        self.repo_name = repo_name
        self.memory_dataset = f"{repo_name}_memory"
        
    async def cognee_query(self, query: str, mode: str = "default"):
        try:
            if mode == "triplet":
                results = await cognee.recall(
                    query,
                    query_type=SearchType.TRIPLET_COMPLETION,
                    datasets=[self.repo_name, self.memory_dataset],
                )
            else:
                results = await cognee.recall(
                    query,
                    datasets=[self.repo_name , self.memory_dataset],
                )

            if not results:
                return {"success": True, "answer": None, "note": "No relevant memory found."}

            answer = results[0].text
            
            return {
                "success": True,
                "answer": answer,
            }
        except DatasetNotFoundError:



        except Exception as e:
            logger.error(f"cognee_query failed: {e}", exc_info=True)
            error_str = str(e).lower()

            if "rate limit" in error_str or "429" in error_str:
                logger.error(f"Rate limit hit in cognee_query: {e}", exc_info=True)
                raise HTTPException(status_code=429, detail="Rate limit exceeded, please try again later.")
            logger.error(f"cognee_query failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
        