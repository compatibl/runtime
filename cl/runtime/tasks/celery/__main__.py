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

import logging.config
from cl.runtime.log.log_config import logging_config
from cl.runtime.settings.celery_settings import CelerySettings
from cl.runtime.tasks.celery.celery_queue import celery_app


celery_settings = CelerySettings.instance()


if __name__ == "__main__":
    logging.config.dictConfig(logging_config)

    celery_app.worker_main(
        argv=[
            "-A",
            "cl.runtime.tasks.celery.celery_queue",
            "worker",
            "-E",
            "--loglevel=info",
            f"--pool={celery_settings.celery_pool_type}",
            f"--concurrency={celery_settings.celery_workers}",
        ],
    )