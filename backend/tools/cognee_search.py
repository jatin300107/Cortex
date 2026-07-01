from dotenv import load_dotenv
load_dotenv()
from cognee import SearchType
import cognee

# repo_name
# dataset_name=repo_name
# dataset_name=repo_name
async def cognee_query(query: str, mode: str ) -> dict:   
    try:
        if mode == "triplet":
            results = await cognee.recall(query, query_type=SearchType.TRIPLET_COMPLETION )
        else:
            results = await cognee.recall(query)

        formatted_results = [r.text for r in results if r.text]
        return {
            "success": True,
            "mode": mode,
            "results": formatted_results,
            "count": len(results),
        }
    except Exception as e:
        
        return {
            "success": False,
            "error": str(e),
            "results": [],
        }
    