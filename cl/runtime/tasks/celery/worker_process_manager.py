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
import multiprocessing
import os
import signal
import sys
from dataclasses import dataclass
from dataclasses import field
from typing import ClassVar
from typing import Dict
from typing import Optional
from cl.runtime.log.log_config import logging_config
from cl.runtime.settings.celery_settings import CelerySettings
from cl.runtime.tasks.celery.worker_metrics import WorkerMetrics

# Windows Job Object support
if sys.platform == "win32":
    import ctypes
    import ctypes.wintypes

    kernel32 = ctypes.windll.kernel32

_logger = logging.getLogger(__name__)


@dataclass
class WorkerProcessManager:
    """Manager for multiple Celery worker processes on Windows."""

    worker_count: int = field(default_factory=lambda: CelerySettings.instance().celery_workers)
    """Number of worker processes to spawn."""

    _worker_processes: ClassVar[Dict[int, multiprocessing.Process]] = {}
    """Dictionary of worker_id -> Process."""

    _manager_instance: ClassVar[Optional["WorkerProcessManager"]] = None
    """Singleton instance of the manager."""

    _main_pid: ClassVar[Optional[int]] = None
    """PID of the main process (used as unique marker for worker names)."""

    _job_handle: ClassVar[Optional[int]] = None
    """Windows Job Object handle for automatic cleanup."""

    @classmethod
    def instance(cls) -> "WorkerProcessManager":
        """Get or create singleton instance."""
        if cls._manager_instance is None:
            cls._manager_instance = cls()
            # Store main process PID as unique marker
            cls._main_pid = os.getpid()
            # Create Windows Job Object for automatic cleanup
            if sys.platform == "win32":
                cls._create_job_object()
        return cls._manager_instance

    @classmethod
    def _create_job_object(cls) -> None:
        """Create Windows Job Object that will kill all child processes when parent dies."""
        try:
            # Create unnamed job object (simpler than named)
            create_job = kernel32.CreateJobObjectW
            create_job.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
            create_job.restype = ctypes.c_void_p

            cls._job_handle = create_job(None, None)
            if not cls._job_handle:
                return

            # Set KILL_ON_JOB_CLOSE flag using simple DWORD structure
            class JobInfo(ctypes.Structure):
                _fields_ = [("LimitFlags", ctypes.c_ulong)]

            info = JobInfo(LimitFlags=0x2000)  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE

            set_info = kernel32.SetInformationJobObject
            set_info.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_ulong]
            set_info.restype = ctypes.c_bool

            if set_info(cls._job_handle, 2, ctypes.byref(info), ctypes.sizeof(info)):
                _logger.info("Windows Job Object created - workers will auto-terminate when parent exits")
            else:
                cls._job_handle = None

        except Exception as e:  # noqa: BLE001
            _logger.warning("Failed to create Job Object: %s", e)
            cls._job_handle = None

    @classmethod
    def _assign_process_to_job(cls, pid: int) -> None:
        """Assign a process to the Job Object."""
        if not cls._job_handle:
            return

        try:
            open_process = kernel32.OpenProcess
            open_process.restype = ctypes.c_void_p

            assign_to_job = kernel32.AssignProcessToJobObject
            assign_to_job.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
            assign_to_job.restype = ctypes.c_bool

            close_handle = kernel32.CloseHandle
            close_handle.argtypes = [ctypes.c_void_p]

            process_handle = open_process(0x0200, False, pid)  # PROCESS_SET_QUOTA | PROCESS_TERMINATE
            if process_handle:
                assign_to_job(cls._job_handle, process_handle)
                close_handle(process_handle)

        except Exception:  # noqa: BLE001
            pass  # Silent fail - not critical

    def start_workers(self) -> None:
        """Start all worker processes."""
        WorkerMetrics.initialize()

        _logger.info("Starting %s worker processes", self.worker_count)

        for worker_id in range(self.worker_count):
            if worker_id not in self._worker_processes or not self._worker_processes[worker_id].is_alive():
                self._start_single_worker(worker_id)

    def _start_single_worker(self, worker_id: int) -> None:
        """Start a single worker process."""
        # Include main PID in worker name as unique marker
        worker_name = f"celery-worker-{worker_id}-{self._main_pid}"

        # Create process with modified celery arguments
        worker_process = multiprocessing.Process(
            target=self._worker_target,
            name=worker_name,
            daemon=True,
            kwargs={
                "worker_id": worker_id,
                "worker_name": worker_name,
                "log_config": logging_config,
            },
        )

        worker_process.start()
        self._worker_processes[worker_id] = worker_process

        # Assign worker to Job Object (Windows only)
        if sys.platform == "win32" and self._job_handle:
            self._assign_process_to_job(worker_process.pid)

        # Record metrics
        WorkerMetrics.record_worker_start(worker_id)

        _logger.info("Started worker %s with PID %s", worker_name, worker_process.pid)

    @staticmethod
    def _worker_target(worker_id: int, worker_name: str, log_config: Dict) -> None:
        """Target function for worker process."""
        import logging.config
        from cl.runtime.tasks.celery.celery_queue import celery_app

        # Setup logging from main process
        logging.config.dictConfig(log_config)

        # Configure this worker's celery instance
        celery_settings = CelerySettings.instance()

        # Start celery worker with unique name
        celery_app.worker_main(
            argv=[
                "-A",
                "cl.runtime.tasks.celery.celery_queue",
                "worker",
                f"--hostname={worker_name}@%h",
                "--loglevel=info",
                "--pool=solo",  # Each worker is single-threaded
                "--concurrency=1",  # Process one task at a time
                "--prefetch-multiplier=1",  # Take only one task from queue
                f"--queues={celery_settings.celery_broker_queue}",
                "--without-gossip",  # Disable gossip for Windows
                "--without-mingle",  # Disable synchronization on start
                "--without-heartbeat",  # Disable heartbeat for Windows
            ],
        )

    def stop_workers(self) -> None:
        """Stop all worker processes gracefully."""
        for process in self._worker_processes.values():
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
                if process.is_alive():
                    os.kill(process.pid, signal.SIGTERM)

        self._worker_processes.clear()

    def restart_dead_workers(self) -> None:
        """Check for dead workers and restart them."""
        for worker_id in list(self._worker_processes.keys()):
            process = self._worker_processes[worker_id]
            if not process.is_alive():
                old_pid = process.pid
                _logger.warning("Worker %s (PID %s) died, restarting...", process.name, old_pid)

                # Record restart in metrics
                WorkerMetrics.record_worker_restart(worker_id)

                self._start_single_worker(worker_id)
                new_pid = self._worker_processes[worker_id].pid
                _logger.info("Worker %s restarted: old PID %s -> new PID %s", process.name, old_pid, new_pid)

    def get_worker_status(self) -> Dict[int, bool]:
        """Get status of all workers."""
        return {worker_id: process.is_alive() for worker_id, process in self._worker_processes.items()}

    def get_worker_pids(self) -> Dict[int, Optional[int]]:
        """Get PIDs of all workers."""
        return {worker_id: process.pid for worker_id, process in self._worker_processes.items()}
