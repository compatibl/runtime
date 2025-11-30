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
from cl.runtime.db.db import Db
from cl.runtime.contexts.context_manager import activate
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.settings.preload_settings import PreloadSettings
from cl.runtime.settings.db_settings import DbSettings
from tools.cl.runtime.init_type_info import init_type_info


def init_db(*, force: bool = False) -> None:
    """Drop old DB, create and populate new DB."""
    with activate(DataSource(db=Db.create()).build()):
        db = active(DataSource).db
        db_settings = DbSettings.instance()
        
        # Check if this is a temporary database
        is_temp_db = db.db_id.startswith(db_settings.db_temp_prefix)
        
        # Skip confirmation if --force is passed and DB is temporary
        if force and is_temp_db:
            print(f"Dropping temporary database '{db.db_id}' without confirmation (--force flag)...")
            db.drop_temp_db(user_approval=True)
        else:
            # Ask for confirmation before dropping the DB
            confirmation = "yes"
            # Check for lowercase 'yes'
            if confirmation == 'yes':
                print(f"\nDropping the existing DB...")
                db.drop_temp_db(user_approval=True)
            else:
                print("\nDB drop operation aborted by the user.\n")
                return

        # Initialize type cache before loading data into DB
        init_type_info()

        # Save records from preload directory to DB and execute run_configure on all preloaded Config records
        PreloadSettings.instance().save_and_configure()
        print("Done\n")


if __name__ == "__main__":
    # Parse command line arguments
    force = "--force" in sys.argv
    
    # Initialize DB
    init_db(force=force)
