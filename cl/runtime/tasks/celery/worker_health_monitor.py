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
import threading
from typing import ClassVar
from typing import Optional
from cl.runtime.settings.celery_settings import CelerySettings
from cl.runtime.tasks.celery.worker_metrics import WorkerMetrics
from cl.runtime.tasks.celery.worker_process_manager import WorkerProcessManager

_logger = logging.getLogger(__name__)


class WorkerHealthMonitor:
    """Monitor and restart dead worker processes."""

    _monitor_thread: ClassVar[Optional[threading.Thread]] = None
    _stop_event: ClassVar[threading.Event] = threading.Event()

    @classmethod
    def start_monitoring(cls) -> None:
        """Start the health monitoring thread."""
        if cls._monitor_thread is not None and cls._monitor_thread.is_alive():
            _logger.warning("Health monitor already running")
            return

        cls._stop_event.clear()
        cls._monitor_thread = threading.Thread(target=cls._monitoring_loop, daemon=True, name="WorkerHealthMonitor")
        cls._monitor_thread.start()
        _logger.info("Started worker health monitor")

    @classmethod
    def stop_monitoring(cls) -> None:
        """Stop the health monitoring thread."""
        if cls._monitor_thread is None:
            return

        cls._stop_event.set()
        cls._monitor_thread.join(timeout=5)
        cls._monitor_thread = None
        _logger.info("Stopped worker health monitor")

    @classmethod
    def _monitoring_loop(cls) -> None:
        """Main monitoring loop."""
        celery_settings = CelerySettings.instance()
        manager = WorkerProcessManager.instance()
        check_interval = celery_settings.celery_worker_restart_interval

        # Log metrics every 10 health checks
        metrics_log_counter = 0
        metrics_log_interval = 10

        while not cls._stop_event.is_set():
            try:
                # Check and restart dead workers
                manager.restart_dead_workers()

                # Log current status with PIDs
                cls._log_worker_status(manager)

                # Periodically log detailed metrics
                metrics_log_counter += 1
                if metrics_log_counter >= metrics_log_interval:
                    WorkerMetrics.log_metrics_summary()
                    metrics_log_counter = 0

            except Exception as e:
                _logger.error("Error in health monitor: %s", e, exc_info=True)

            # Wait for next check
            cls._stop_event.wait(check_interval)

    @classmethod
    def _log_worker_status(cls, manager: WorkerProcessManager) -> None:
        """Log current worker status with PIDs."""
        status = manager.get_worker_status()
        alive_count = sum(1 for is_alive in status.values() if is_alive)
        worker_pids = {worker_id: pid for worker_id, pid in manager.get_worker_pids().items() if status[worker_id]}

        if alive_count < len(status):
            _logger.warning("Only %s/%s workers are alive. PIDs: %s", alive_count, len(status), worker_pids)
        else:
            _logger.info("All %s workers are alive. PIDs: %s", alive_count, worker_pids)
