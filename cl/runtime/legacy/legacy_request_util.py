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

from cl.runtime.routers.storage.save_request import SaveRequest


class LegacyRequestUtil:
    """Util class to convert request data in legacy format."""

    @classmethod
    def format_save_request(cls, save_request: SaveRequest) -> SaveRequest:
        # TODO (Roman): Fix on UI

        new_records = []
        for old_record in save_request.records:
            new_record = {k: v for k, v in old_record.items()}

            # Workaround for UiAppState request. Ui send OpenedTabs without _t
            if new_record.get("_t") == "UiAppState" and (opened_tabs := new_record.get("OpenedTabs")) is not None:
                # Add _t to each TabInfo in list
                new_record["OpenedTabs"] = [
                    {
                        **{k: v for k, v in item.items() if k != "Type"},
                        "Type": {**item["Type"], "_t": "BaseTypeInfo"},
                        "_t": "TabInfo",
                    }
                    for item in opened_tabs
                ]
                new_records.append(new_record)

            else:
                new_records.append(old_record)

        return SaveRequest(
            user=save_request.user, env=save_request.env, dataset=save_request.dataset, records=new_records
        )
