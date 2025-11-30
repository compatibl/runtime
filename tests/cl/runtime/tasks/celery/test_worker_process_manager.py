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

from unittest.mock import Mock
from unittest.mock import patch
from cl.runtime.tasks.celery.worker_process_manager import WorkerProcessManager


class TestWorkerProcessManager:
    """Tests for WorkerProcessManager."""

    def test_singleton_pattern(self):
        """Test that WorkerProcessManager follows singleton pattern."""
        # Clear singleton for test
        WorkerProcessManager._manager_instance = None

        manager1 = WorkerProcessManager.instance()
        manager2 = WorkerProcessManager.instance()

        assert manager1 is manager2
        assert isinstance(manager1, WorkerProcessManager)

    @patch("cl.runtime.tasks.celery.worker_process_manager.CelerySettings")
    def test_start_workers(self, mock_celery_settings):
        """Test starting multiple worker processes."""
        # Setup
        mock_settings = Mock()
        mock_settings.celery_workers = 3
        mock_celery_settings.instance.return_value = mock_settings

        # Clear singleton and dictionary
        WorkerProcessManager._manager_instance = None
        WorkerProcessManager._worker_processes = {}

        manager = WorkerProcessManager.instance()

        # Mock _start_single_worker to avoid creating real processes
        with patch.object(manager, "_start_single_worker") as mock_start_worker:
            manager.start_workers()

            # Verify _start_single_worker was called for each worker
            assert mock_start_worker.call_count == 3
            mock_start_worker.assert_any_call(0)
            mock_start_worker.assert_any_call(1)
            mock_start_worker.assert_any_call(2)

    @patch("cl.runtime.tasks.celery.worker_process_manager.multiprocessing.Process")
    @patch("cl.runtime.tasks.celery.worker_process_manager.CelerySettings")
    def test_start_single_worker(self, mock_celery_settings, mock_process_class):
        """Test starting a single worker process creates and starts Process correctly."""
        # Setup
        mock_settings = Mock()
        mock_settings.celery_workers = 1
        mock_celery_settings.instance.return_value = mock_settings

        mock_process = Mock()
        mock_process.pid = 12345
        mock_process_class.return_value = mock_process

        # Clear singleton and dictionary
        WorkerProcessManager._manager_instance = None
        WorkerProcessManager._worker_processes = {}

        manager = WorkerProcessManager.instance()

        # Start single worker
        manager._start_single_worker(0)

        # Verify Process was created with correct arguments
        mock_process_class.assert_called_once()
        call_kwargs = mock_process_class.call_args[1]
        assert call_kwargs["target"] == manager._worker_target
        # Worker name now includes main PID: celery-worker-0-{main_pid}
        assert call_kwargs["name"].startswith("celery-worker-0-")
        assert call_kwargs["daemon"] is True
        assert "worker_id" in call_kwargs["kwargs"]
        assert call_kwargs["kwargs"]["worker_id"] == 0
        # Worker name in kwargs also includes main PID
        assert call_kwargs["kwargs"]["worker_name"].startswith("celery-worker-0-")

        # Verify process was started and registered
        mock_process.start.assert_called_once()
        assert WorkerProcessManager._worker_processes[0] == mock_process

    @patch("cl.runtime.tasks.celery.worker_process_manager.CelerySettings")
    def test_restart_dead_workers(self, mock_celery_settings):
        """Test restarting dead workers."""
        # Setup
        mock_settings = Mock()
        mock_settings.celery_workers = 2
        mock_celery_settings.instance.return_value = mock_settings

        # Clear singleton and dictionary
        WorkerProcessManager._manager_instance = None
        WorkerProcessManager._worker_processes = {}

        manager = WorkerProcessManager.instance()

        # Mock dead process
        dead_process = Mock()
        dead_process.is_alive.return_value = False
        dead_process.name = "celery-worker-0"

        # Mock alive process
        alive_process = Mock()
        alive_process.is_alive.return_value = True
        alive_process.name = "celery-worker-1"

        WorkerProcessManager._worker_processes = {0: dead_process, 1: alive_process}

        # Test restart
        with patch.object(manager, "_start_single_worker") as mock_start:
            manager.restart_dead_workers()
            mock_start.assert_called_once_with(0)

    @patch("cl.runtime.tasks.celery.worker_process_manager.CelerySettings")
    def test_get_worker_status(self, mock_celery_settings):
        """Test getting worker status."""
        # Setup
        mock_settings = Mock()
        mock_settings.celery_workers = 2
        mock_celery_settings.instance.return_value = mock_settings

        # Clear singleton and dictionary
        WorkerProcessManager._manager_instance = None
        WorkerProcessManager._worker_processes = {}

        manager = WorkerProcessManager.instance()

        # Mock processes
        alive_process = Mock()
        alive_process.is_alive.return_value = True

        dead_process = Mock()
        dead_process.is_alive.return_value = False

        WorkerProcessManager._worker_processes = {0: alive_process, 1: dead_process}

        # Get status
        status = manager.get_worker_status()

        # Verify
        assert status == {0: True, 1: False}

    @patch("cl.runtime.tasks.celery.worker_process_manager.os")
    @patch("cl.runtime.tasks.celery.worker_process_manager.CelerySettings")
    def test_stop_workers_graceful(self, mock_celery_settings, mock_os):
        """Test graceful stop of workers."""
        # Setup
        mock_settings = Mock()
        mock_settings.celery_workers = 1
        mock_celery_settings.instance.return_value = mock_settings
        mock_os.name = "nt"  # Windows

        # Clear singleton and dictionary
        WorkerProcessManager._manager_instance = None
        WorkerProcessManager._worker_processes = {}

        manager = WorkerProcessManager.instance()

        # Mock process that terminates gracefully
        process = Mock()
        process.is_alive.side_effect = [True, False]  # Alive, then terminated
        process.name = "celery-worker-0"
        process.pid = 12345

        WorkerProcessManager._worker_processes = {0: process}

        # Stop workers
        manager.stop_workers()

        # Verify
        process.terminate.assert_called_once()
        process.join.assert_called_once()
        assert len(WorkerProcessManager._worker_processes) == 0

    @patch("cl.runtime.tasks.celery.worker_process_manager.CelerySettings")
    @patch("multiprocessing.Process")
    def test_restart_worker_after_crash(self, mock_process_class, mock_celery_settings):
        """Test that crashed worker is detected and restarted."""
        # Setup
        mock_settings = Mock()
        mock_settings.celery_workers = 2
        mock_celery_settings.instance.return_value = mock_settings

        # Clear singleton and dictionary
        WorkerProcessManager._manager_instance = None
        WorkerProcessManager._worker_processes = {}

        manager = WorkerProcessManager.instance()

        # Create mock processes
        alive_process = Mock()
        alive_process.is_alive.return_value = True
        alive_process.name = "celery-worker-1"
        alive_process.pid = 99999

        # Simulate crashed process
        crashed_process = Mock()
        crashed_process.is_alive.return_value = False
        crashed_process.name = "celery-worker-0"
        crashed_process.pid = 88888

        # Setup initial state with crashed worker
        WorkerProcessManager._worker_processes = {0: crashed_process, 1: alive_process}

        # Mock new process creation for restart
        new_process = Mock()
        new_process.is_alive.return_value = True
        new_process.pid = 77777
        mock_process_class.return_value = new_process

        # Execute restart
        manager.restart_dead_workers()

        # Verify that new process was created and started
        mock_process_class.assert_called_once()
        new_process.start.assert_called_once()

        # Verify crashed worker was replaced
        assert WorkerProcessManager._worker_processes[0] == new_process
        assert WorkerProcessManager._worker_processes[1] == alive_process

        # Verify status reflects new state
        status = manager.get_worker_status()
        assert status[0] is True  # Restarted worker is alive
        assert status[1] is True  # Original worker still alive

    @patch("cl.runtime.tasks.celery.worker_process_manager.CelerySettings")
    @patch("multiprocessing.Process")
    def test_multiple_workers_crash_restart(self, mock_process_class, mock_celery_settings):
        """Test that multiple crashed workers are all restarted."""
        # Setup
        mock_settings = Mock()
        mock_settings.celery_workers = 3
        mock_celery_settings.instance.return_value = mock_settings

        # Clear singleton and dictionary
        WorkerProcessManager._manager_instance = None
        WorkerProcessManager._worker_processes = {}

        manager = WorkerProcessManager.instance()

        # All workers crashed
        crashed_processes = []
        for i in range(3):
            process = Mock()
            process.is_alive.return_value = False
            process.name = f"celery-worker-{i}"
            process.pid = 10000 + i
            crashed_processes.append(process)

        WorkerProcessManager._worker_processes = {i: crashed_processes[i] for i in range(3)}

        # Mock new processes
        new_processes = []
        for i in range(3):
            new_process = Mock()
            new_process.is_alive.return_value = True
            new_process.pid = 20000 + i
            new_processes.append(new_process)

        mock_process_class.side_effect = new_processes

        # Execute restart
        manager.restart_dead_workers()

        # Verify all processes were restarted
        assert mock_process_class.call_count == 3
        for i in range(3):
            new_processes[i].start.assert_called_once()
            assert WorkerProcessManager._worker_processes[i] == new_processes[i]

        # All workers should be alive now
        status = manager.get_worker_status()
        assert all(is_alive for is_alive in status.values())
