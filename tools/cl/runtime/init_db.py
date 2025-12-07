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

import sys

from cl.runtime.configurations.preload_configuration import PreloadConfiguration
from cl.runtime.db.db import Db
from cl.runtime.contexts.context_manager import activate
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.settings.db_settings import DbSettings
from tools.cl.runtime.init_type_info import init_type_info


def init_db(*, drop_db_interactive: bool = False) -> None:
    """Populate DB with data, drop previous version if not empty after interactive user approval if needed."""
    with activate(DataSource(db=Db.create()).build()):

        # Get DB instance
        db = active(DataSource)._get_db()  # TODO: !! Move

        # Handle the case when DB is not empty
        if not db.is_empty():
            # Drop previous version if not empty after interactive user approval if needed.
            db.drop_db(drop_db_interactive=drop_db_interactive)

        # Initialize type cache before loading data into DB
        init_type_info()

        # Save records from preload directory to DB and execute run_configure on all preloaded Config records
        PreloadConfiguration().build().run_configure()
        print("Done\n")


if __name__ == "__main__":

    # Initialize DB in interactive mode
    init_db(drop_db_interactive=True)
