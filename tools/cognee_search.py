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
            results = await cognee.recall(query )
        
        return {
            "success": True,
            "mode": mode,
            "results": [r.text for r in results if r.text],
            "count": len(results)
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "results": []
        }
    