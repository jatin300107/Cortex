from dotenv import load_dotenv
load_dotenv()
from cognee import SearchType
import cognee
from get_utils import get_user
# repo_name
# dataset_name=repo_name
# dataset_name=repo_name
async def cognee_query(query: str, mode: str , dataset_id : list ) -> dict:   
    try:
        if mode == "triplet":
            results = await cognee.recall(query, query_type=SearchType.TRIPLET_COMPLETION  , dataset_ids = dataset_id )
        else:
            results = await cognee.recall(query, dataset_ids = dataset_id )

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
    