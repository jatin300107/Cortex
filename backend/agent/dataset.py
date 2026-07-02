import uuid
import cognee
from cognee.modules.pipelines.operations.run_tasks import run_tasks
from cognee.modules.pipelines.tasks.task import Task
from cognee.tasks.storage import add_data_points
from get_utils import get_user
NAMESPACE = uuid.UUID("85743f0b-4cfa-4dd3-9707-39c0e3a51e9d")  

def get_dataset_id(repo_path: str) -> uuid.UUID:
    return uuid.uuid5(NAMESPACE, repo_path)


async def store_datasets(node_set, dataset_id):
    user = await get_user()
    async for status in run_tasks(
        tasks=[Task(add_data_points)],
        data=node_set,
        dataset_id=dataset_id,
        pipeline_name="cortex_ingest",
        user=user
    ):
        pass
    await cognee.cognify(datasets=[dataset_id], user=user)