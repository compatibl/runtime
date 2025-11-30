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

import logging
import time
from typing import Dict
from typing import Optional

_logger = logging.getLogger(__name__)


class WorkerMetrics:
    """Metrics collector for Celery worker pool."""

    _worker_start_times: Dict[int, float] = {}
    """Worker ID -> start timestamp."""

    _worker_restart_counts: Dict[int, int] = {}
    """Worker ID -> restart count."""

    _total_restarts: int = 0
    """Total number of worker restarts."""

    _pool_start_time: Optional[float] = None
    """Timestamp when worker pool started."""

    @classmethod
    def initialize(cls) -> None:
        """Initialize the metrics collector."""
        cls._pool_start_time = time.time()
        cls._worker_start_times.clear()
        cls._worker_restart_counts.clear()
        cls._total_restarts = 0

    @classmethod
    def record_worker_start(cls, worker_id: int) -> None:
        """Record when a worker starts."""
        cls._worker_start_times[worker_id] = time.time()
        if worker_id not in cls._worker_restart_counts:
            cls._worker_restart_counts[worker_id] = 0

    @classmethod
    def record_worker_restart(cls, worker_id: int) -> None:
        """Record when a worker is restarted."""
        cls._worker_restart_counts[worker_id] = cls._worker_restart_counts.get(worker_id, 0) + 1
        cls._total_restarts += 1
        cls._worker_start_times[worker_id] = time.time()
        _logger.info(
            "Worker %s restart count: %s, Total restarts: %s",
            worker_id,
            cls._worker_restart_counts[worker_id],
            cls._total_restarts,
        )

    @classmethod
    def get_worker_uptime(cls, worker_id: int) -> Optional[float]:
        """Get worker uptime in seconds."""
        start_time = cls._worker_start_times.get(worker_id)
        if start_time is None:
            return None
        return time.time() - start_time

    @classmethod
    def get_pool_uptime(cls) -> Optional[float]:
        """Get worker pool uptime in seconds."""
        if cls._pool_start_time is None:
            return None
        return time.time() - cls._pool_start_time

    @classmethod
    def get_metrics_summary(cls) -> Dict:
        """Get summary of all metrics."""
        pool_uptime = cls.get_pool_uptime()
        worker_uptimes = {
            worker_id: uptime
            for worker_id in cls._worker_start_times.keys()
            if (uptime := cls.get_worker_uptime(worker_id)) is not None
        }

        return {
            "pool_uptime_seconds": pool_uptime,
            "pool_uptime_hours": pool_uptime / 3600 if pool_uptime else None,
            "total_restarts": cls._total_restarts,
            "worker_restart_counts": dict(cls._worker_restart_counts),
            "worker_uptimes_seconds": worker_uptimes,
            "average_worker_uptime_seconds": (
                sum(worker_uptimes.values()) / len(worker_uptimes) if worker_uptimes else None
            ),
        }

    @classmethod
    def log_metrics_summary(cls) -> None:
        """Log metrics summary."""
        metrics = cls.get_metrics_summary()

        pool_uptime_hours = metrics.get("pool_uptime_hours")
        if pool_uptime_hours:
            _logger.info("Worker pool uptime: %.2f hours", pool_uptime_hours)

        _logger.info("Total worker restarts: %s", metrics["total_restarts"])

        if metrics["worker_restart_counts"]:
            restart_details = ", ".join(
                f"Worker-{wid}: {count}" for wid, count in sorted(metrics["worker_restart_counts"].items())
            )
            _logger.info("Restart counts by worker: %s", restart_details)

        avg_uptime = metrics.get("average_worker_uptime_seconds")
        if avg_uptime:
            _logger.info("Average worker uptime: %.2f hours", avg_uptime / 3600)
