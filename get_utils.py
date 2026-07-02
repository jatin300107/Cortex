import asyncio
from cognee.modules.users.methods import get_default_user
import asyncio

from cognee.modules.data.methods import load_or_create_datasets
async def get_user():
    user = await get_default_user()
    return user 

async def get_dataset_id(repo_path):
    user = await get_user()
    
    dataset = await load_or_create_datasets(
        dataset_names=[repo_path],
        existing_datasets=[],
        user=user,
    )
    dataset_id = dataset[0].id
    return dataset_id