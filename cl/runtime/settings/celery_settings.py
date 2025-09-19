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

import os
from dataclasses import dataclass
from typing_extensions import final
from cl.runtime.settings.db_settings import DbSettings
from cl.runtime.settings.settings import Settings


@dataclass(slots=True, kw_only=True)
@final
class CelerySettings(Settings):
    """Celery settings."""

    celery_broker: str = "sqlite"
    """Celery broker to be used."""

    celery_broker_uri: str = "redis://localhost:6379/0"
    """Celery broker URI. The value from config file is ignored for `sqlite` broker."""

    celery_broker_queue: str = "celery"
    """Celery broker queue."""

    celery_workers: int = 6
    """Maximum number of workers for Celery."""

    celery_max_retries: int = 0
    """Maximum number of retries for Celery tasks."""

    celery_time_limit: int = 3600 * 2
    """Time limit for Celery tasks in seconds."""

    celery_pool_type: str = "threads"
    """Pool type for Celery workers."""

    def __init(self) -> None:
        if not self.celery_broker:
            raise RuntimeError("Celery broker is not specified in settings.")

        if self.celery_broker == "sqlite":
            databases_dir = DbSettings.get_db_dir()
            celery_file = os.path.join(databases_dir, f"celery.sqlite")

            self._ensure_databases_dir_exists(databases_dir)

            self.celery_broker_uri = f"sqlalchemy+sqlite:///{celery_file}"
        elif self.celery_broker in ["redis", "rabbitmq"]:
            if not self.celery_broker_uri:
                raise RuntimeError("Celery broker URI is not specified for broker.")
            if not self.celery_broker_queue:
                raise RuntimeError("Celery broker queue is not specified for broker.")
        else:
            raise RuntimeError(f"Unsupported Celery broker: {self.celery_broker}")

    @staticmethod
    def _ensure_databases_dir_exists(db_dir) -> None:
        """Checks if a dir for celery exists, and creates it if it does not."""

        if not os.path.exists(db_dir):
            os.makedirs(db_dir)
