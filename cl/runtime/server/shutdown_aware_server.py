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
import uvicorn
from cl.runtime.settings.celery_settings import CelerySettings

_logger = logging.getLogger(__name__)


class ShutdownAwareServer(uvicorn.Server):
    """Uvicorn server that stops worker health monitor before killing worker processes."""

    def handle_exit(self, sig, frame):
        """Stop worker health monitor before uvicorn kills worker processes."""
        _logger.info("Shutdown signal %s received, stopping worker health monitor", sig)
        if CelerySettings.instance().celery_multiprocess_pool:
            from cl.runtime.tasks.celery.worker_health_monitor import WorkerHealthMonitor

            WorkerHealthMonitor.stop_monitoring()
        super().handle_exit(sig, frame)
