from cognee import SearchType
import cognee

async def cognee_query(query: str, mode: str , repo_name) -> dict:
    try:
        if mode == "triplet":
            results = await cognee.recall(query, query_type=SearchType.TRIPLET_COMPLETION  , dataset_name=repo_name)
        else:
            results = await cognee.recall(query ,  dataset_name=repo_name)
        
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