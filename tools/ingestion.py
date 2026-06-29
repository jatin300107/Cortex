import cognee


async def ingest_to_memory(data: str , repo_name : str) -> dict:
    try:
        await cognee.remember(data , self_improvement=True  , dataset_name=repo_name)
        return {
            "success": True,
            "message": "Data ingested successfully"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }