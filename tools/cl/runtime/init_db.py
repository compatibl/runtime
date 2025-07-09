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

from cl.runtime import Db
from cl.runtime.contexts.db_context import DbContext
from cl.runtime.settings.db_settings import DbSettings
from cl.runtime.settings.preload_settings import PreloadSettings


def init_db():
    """Drop old DB, create and populate new DB."""
    with DbContext(db=Db.create()).build():
        print(f"Dropping the existing DB (will succeed only if DB name has prefix '{DbSettings.instance().db_temp_prefix}')")
        DbContext.drop_temp_db()

        # Save records from preload directory to DB and execute run_configure on all preloaded Config records
        print("Adding preloads to the new DB")
        PreloadSettings.instance().save_and_configure()
        print("Done.\n")


if __name__ == "__main__":

    # Initialize DB
    init_db()
