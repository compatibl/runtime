# Copyright (C) 2023-present The Project Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Annotated
from fastapi import APIRouter
from fastapi import Depends
from pydantic import BaseModel
from cl.runtime.routers.dependencies.context_headers import ContextHeaders
from cl.runtime.routers.dependencies.context_headers import get_context_headers
from cl.runtime.settings.celery_settings import CelerySettings
from cl.runtime.tasks.celery.worker_metrics import WorkerMetrics
from cl.runtime.tasks.celery.worker_process_manager import WorkerProcessManager

router = APIRouter()


class WorkerStatus(BaseModel):
    """Worker process status."""

    worker_id: int
    is_alive: bool
    hostname: str
    pid: int | None


class WorkersStatusResponse(BaseModel):
    """Response with all workers status."""

    total_workers: int
    alive_workers: int
    workers: list[WorkerStatus]
    multiprocess_mode: bool


@router.get("/status", response_model=WorkersStatusResponse)
async def get_workers_status(
    context_headers: Annotated[ContextHeaders, Depends(get_context_headers)],
) -> WorkersStatusResponse:
    """Get status of all worker processes."""

    celery_settings = CelerySettings.instance()

    if not celery_settings.celery_multiprocess_pool:
        # Single embedded worker mode
        return WorkersStatusResponse(
            total_workers=1,
            alive_workers=1,
            workers=[WorkerStatus(worker_id=0, is_alive=True, hostname="embedded", pid=None)],
            multiprocess_mode=False,
        )

    # Multi-process mode
    manager = WorkerProcessManager.instance()
    status = manager.get_worker_status()
    pids = manager.get_worker_pids()

    workers = [
        WorkerStatus(
            worker_id=worker_id,
            is_alive=is_alive,
            hostname=f"celery-worker-{worker_id}",
            pid=pids.get(worker_id),
        )
        for worker_id, is_alive in status.items()
    ]

    return WorkersStatusResponse(
        total_workers=len(workers),
        alive_workers=sum(1 for w in workers if w.is_alive),
        workers=workers,
        multiprocess_mode=True,
    )


@router.post("/restart")
async def restart_dead_workers(context_headers: Annotated[ContextHeaders, Depends(get_context_headers)]) -> dict:
    """Restart dead worker processes."""

    celery_settings = CelerySettings.instance()

    if not celery_settings.celery_multiprocess_pool:
        return {"message": "Multi-process mode is not enabled"}

    manager = WorkerProcessManager.instance()
    manager.restart_dead_workers()

    return {"message": "Dead workers restarted"}


@router.get("/metrics")
async def get_workers_metrics(context_headers: Annotated[ContextHeaders, Depends(get_context_headers)]) -> dict:
    """Get worker pool metrics."""

    celery_settings = CelerySettings.instance()

    if not celery_settings.celery_multiprocess_pool:
        return {"message": "Multi-process mode is not enabled", "metrics": None}

    metrics = WorkerMetrics.get_metrics_summary()

    return {"multiprocess_mode": True, "metrics": metrics}
